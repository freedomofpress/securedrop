# -*- coding: utf-8 -*-

from datetime import datetime
import mock
from multiprocessing import Process
import os
from os.path import abspath, dirname, join, realpath
import signal
import socket
import time
import traceback
import requests

from Crypto import Random
from selenium import webdriver
from selenium.common.exceptions import (WebDriverException,
                                        NoAlertPresentException)
from selenium.webdriver.firefox import firefox_binary
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import db
import journalist
import source
import tests.utils.env as env

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


class FunctionalTest():

    def _unused_port(self):
        s = socket.socket()
        s.bind(("localhost", 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def _create_webdriver(self):
        log_file = open(join(LOG_DIR, 'firefox.log'), 'a')
        log_file.write(
            '\n\n[%s] Running Functional Tests\n' % str(
                datetime.now()))
        log_file.flush()
        firefox = firefox_binary.FirefoxBinary(log_file=log_file)
        return webdriver.Firefox(firefox_binary=firefox)

    def setup(self):
        # Patch the two-factor verification to avoid intermittent errors
        self.patcher = mock.patch('journalist.Journalist.verify_token')
        self.mock_journalist_verify_token = self.patcher.start()
        self.mock_journalist_verify_token.return_value = True

        signal.signal(signal.SIGUSR1, lambda _, s: traceback.print_stack(s))

        env.create_directories()
        self.gpg = env.init_gpg()
        db.init_db()

        source_port = self._unused_port()
        journalist_port = self._unused_port()

        self.source_location = "http://localhost:%d" % source_port
        self.journalist_location = "http://localhost:%d" % journalist_port

        def start_source_server():
            # We call Random.atfork() here because we fork the source and
            # journalist server from the main Python process we use to drive
            # our browser with multiprocessing.Process() below. These child
            # processes inherit the same RNG state as the parent process, which
            # is a problem because they would produce identical output if we
            # didn't re-seed them after forking.
            Random.atfork()
            source.app.run(
                port=source_port,
                debug=True,
                use_reloader=False,
                threaded=True)

        def start_journalist_server():
            Random.atfork()
            journalist.app.run(
                port=journalist_port,
                debug=True,
                use_reloader=False,
                threaded=True)

        self.source_process = Process(target=start_source_server)
        self.journalist_process = Process(target=start_journalist_server)

        self.source_process.start()
        self.journalist_process.start()

        for tick in range(30):
            try:
                requests.get(self.source_location)
                requests.get(self.journalist_location)
            except:
                time.sleep(1)
            else:
                break

        if not hasattr(self, 'override_driver'):
            self.driver = self._create_webdriver()

            # Poll the DOM briefly to wait for elements. It appears
            # .click() does not always do a good job waiting for the
            # page to load, or perhaps Firefox takes too long to
            # render it (#399)
            self.driver.implicitly_wait(5)

        # Set window size and position explicitly to avoid potential bugs due
        # to discrepancies between environments.
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1024, 768)

        self.secret_message = 'blah blah blah'

    def teardown(self):
        self.patcher.stop()
        env.teardown()
        if not hasattr(self, 'override_driver'):
            self.driver.quit()
        self.source_process.terminate()
        self.journalist_process.terminate()

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
        WebDriverWait(self.driver, 5).until(
            expected_conditions.alert_is_present(),
            'Timed out waiting for confirmation popup.')

    def _alert_accept(self):
        self.driver.switch_to.alert.accept()
        WebDriverWait(self.driver, 5).until(
            alert_is_not_present(),
            'Timed out waiting for confirmation popup to disappear.')

    def _alert_dismiss(self):
        self.driver.switch_to.alert.dismiss()
        WebDriverWait(self.driver, 5).until(
            alert_is_not_present(),
            'Timed out waiting for confirmation popup to disappear.')
