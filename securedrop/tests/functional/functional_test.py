# -*- coding: utf-8 -*-

import errno
import mock
import os
import pytest
import signal
import socket
import time
import traceback
import requests

from datetime import datetime
from multiprocessing import Process
from os.path import abspath, dirname, join, realpath
from selenium import webdriver
from selenium.common.exceptions import (WebDriverException,
                                        NoAlertPresentException)
from selenium.webdriver.firefox import firefox_binary
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from sdconfig import config
import journalist_app
import source_app
import tests.utils.env as env

from db import db

LOG_DIR = abspath(join(dirname(realpath(__file__)), '..', 'log'))


# https://stackoverflow.com/a/34795883/837471
class alert_is_not_present(object):
    """ Expect an alert to not be present."""
    def __call__(self, driver):
        try:
            alert = driver.switch_to.alert
            alert.text
            return False
        except NoAlertPresentException:
            return True


class FunctionalTest(object):

    def _unused_port(self):
        s = socket.socket()
        s.bind(("localhost", 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def _create_webdriver(self, firefox, profile=None):
        # see https://review.openstack.org/#/c/375258/ and the
        # associated issues for background on why this is necessary
        connrefused_retry_count = 3
        connrefused_retry_interval = 5

        for i in range(connrefused_retry_count + 1):
            try:
                driver = webdriver.Firefox(firefox_binary=firefox,
                                           firefox_profile=profile)
                if i > 0:
                    # i==0 is normal behavior without connection refused.
                    print('NOTE: Retried {} time(s) due to '
                          'connection refused.'.format(i))
                return driver
            except socket.error as socket_error:
                if (socket_error.errno == errno.ECONNREFUSED
                        and i < connrefused_retry_count):
                    time.sleep(connrefused_retry_interval)
                    continue
                raise

    def _prepare_webdriver(self):
        log_file = open(join(LOG_DIR, 'firefox.log'), 'a')
        log_file.write(
            '\n\n[%s] Running Functional Tests\n' % str(
                datetime.now()))
        log_file.flush()
        return firefox_binary.FirefoxBinary(log_file=log_file)

    def setup(self, session_expiration=30):
        self.__context = journalist_app.create_app(config).app_context()
        self.__context.push()
        # Patch the two-factor verification to avoid intermittent errors
        self.patcher = mock.patch('models.Journalist.verify_token')
        self.mock_journalist_verify_token = self.patcher.start()
        self.mock_journalist_verify_token.return_value = True

        self.patcher2 = mock.patch('source_app.main.get_entropy_estimate')
        self.mock_get_entropy_estimate = self.patcher2.start()
        self.mock_get_entropy_estimate.return_value = 8192

        signal.signal(signal.SIGUSR1, lambda _, s: traceback.print_stack(s))

        env.create_directories()
        self.gpg = env.init_gpg()
        db.create_all()

        source_port = self._unused_port()
        journalist_port = self._unused_port()

        self.source_location = "http://localhost:%d" % source_port
        self.journalist_location = "http://localhost:%d" % journalist_port

        # Allow custom session expiration lengths
        self.session_expiration = session_expiration

        self.source_app = source_app.create_app(config)
        self.journalist_app = journalist_app.create_app(config)

        def start_source_server(app):
            config.SESSION_EXPIRATION_MINUTES = self.session_expiration

            app.run(
                port=source_port,
                debug=True,
                use_reloader=False,
                threaded=True)

        def start_journalist_server(app):
            app.run(
                port=journalist_port,
                debug=True,
                use_reloader=False,
                threaded=True)

        self.source_process = Process(
            target=lambda: start_source_server(self.source_app))

        self.journalist_process = Process(
            target=lambda: start_journalist_server(self.journalist_app))

        self.source_process.start()
        self.journalist_process.start()

        for tick in range(30):
            try:
                requests.get(self.source_location)
                requests.get(self.journalist_location)
            except Exception:
                time.sleep(1)
            else:
                break

        if not hasattr(self, 'override_driver'):
            try:
                self.driver = self._create_webdriver(self._prepare_webdriver())
            except WebDriverException as e:
                # Exceptions during driver setup will result in the teardown not being called.
                # Let's teardown and _then_ fail the test so that the patchers are cleaned
                # up for the subsequent tests.
                self.teardown()
                pytest.fail(e)

        # Polls the DOM to wait for elements. To read more about why
        # this is necessary:
        #
        # http://www.obeythetestinggoat.com/how-to-get-selenium-to-wait-for-page-load-after-a-click.html
        #
        # A value of 5 is known to not be enough in some cases, when
        # the machine hosting the tests is slow, reason why it was
        # raised to 10. Setting the value to 60 or more would surely
        # cover even the slowest of machine. However it also means
        # that a test failing to find the desired element in the DOM
        # will only report failure after 60 seconds which is painful
        # for quickly debuging.
        #
        self.driver.implicitly_wait(10)

        # Set window size and position explicitly to avoid potential bugs due
        # to discrepancies between environments.
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1024, 768)

        self.secret_message = ('These documents outline a major government '
                               'invasion of privacy.')

    def wait_for_source_key(self, source_name):
        filesystem_id = self.source_app.crypto_util.hash_codename(source_name)

        def key_available(filesystem_id):
            assert self.source_app.crypto_util.getkey(filesystem_id)
        self.wait_for(
            lambda: key_available(filesystem_id), timeout=60)

    def teardown(self):
        self.patcher.stop()
        env.teardown()
        if hasattr(self, 'driver') and not hasattr(self, 'override_driver'):
            self.driver.quit()
        self.source_process.terminate()
        self.journalist_process.terminate()
        self.__context.pop()

    def wait_for(self, function_with_assertion, timeout=5):
        """Polling wait for an arbitrary assertion."""
        # Thanks to
        # http://chimera.labs.oreilly.com/books/1234000000754/ch20.html#_a_common_selenium_problem_race_conditions
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                return function_with_assertion()
            except (AssertionError, WebDriverException):
                time.sleep(0.1)
        # one more try, which will raise any errors if they are outstanding
        return function_with_assertion()

    def _alert_wait(self):
        WebDriverWait(self.driver, 10).until(
            expected_conditions.alert_is_present(),
            'Timed out waiting for confirmation popup.')

    def _alert_accept(self):
        self.driver.switch_to.alert.accept()
        WebDriverWait(self.driver, 10).until(
            alert_is_not_present(),
            'Timed out waiting for confirmation popup to disappear.')

    def _alert_dismiss(self):
        self.driver.switch_to.alert.dismiss()
        WebDriverWait(self.driver, 10).until(
            alert_is_not_present(),
            'Timed out waiting for confirmation popup to disappear.')
