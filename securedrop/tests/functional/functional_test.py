# -*- coding: utf-8 -*-

from datetime import datetime
import errno
import mock
from multiprocessing import Process
import os
import logging
from os.path import abspath, dirname, join, realpath, expanduser
import signal
import socket
import time
import json
import traceback
import shutil
import requests

import pyotp
import gnupg
from selenium import webdriver
from selenium.common.exceptions import (WebDriverException,
                                        NoAlertPresentException)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.remote_connection import LOGGER
from tbselenium.tbdriver import TorBrowserDriver

os.environ['SECUREDROP_ENV'] = 'test'  # noqa

from sqlalchemy.exc import IntegrityError
from models import Journalist
from sdconfig import config
import journalist_app
import source_app
import tests.utils.env as env

from db import db

FUNCTIONAL_TEST_DIR = abspath(dirname(__file__))
LOGFILE_PATH = abspath(join(FUNCTIONAL_TEST_DIR, 'firefox.log'))
FILES_DIR = abspath(join(dirname(realpath(__file__)), '../..', 'tests/files'))
FIREFOX_PATH = '/usr/bin/firefox/firefox'

TBB_PATH = abspath(join(expanduser('~'), '.local/tbb/tor-browser_en-US/'))
os.environ['TBB_PATH'] = TBB_PATH
TBBRC = join(TBB_PATH, 'Browser/TorBrowser/Data/Tor/torrc')
LOGGER.setLevel(logging.WARNING)


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
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def add_hidservauth(self, address, token):
        if not os.path.exists(TBBRC):
            return False
        found_flag = False
        entry = "HidServAuth {0} {1}\n".format(address, token)
        lines = []
        with open(TBBRC) as fobj:
            lines = fobj.readlines()
        for line in lines:
            if entry.strip() == line.strip():
                found_flag = True

        if found_flag:  # We already have the information in the torrc file
            return True
        lines.append(entry)

        with open(TBBRC, 'w') as fobj:
            fobj.write(''.join(lines))
        return True

    def _create_webdriver(self,  profile=None):
        log_file = open(LOGFILE_PATH, 'a')
        log_file.write(
            '\n\n[%s] Running Functional Tests\n' % str(
                datetime.now()))
        log_file.flush()
        # see https://review.openstack.org/#/c/375258/ and the
        # associated issues for background on why this is necessary
        connrefused_retry_count = 3
        connrefused_retry_interval = 5

        # Don't use Tor when reading from localhost, and turn off private
        # browsing. We need to turn off private browsing because we won't be
        # able to access the browser's cookies in private browsing mode. Since
        # we use session cookies in SD anyway (in private browsing mode all
        # cookies are set as session cookies), this should not affect session
        # lifetime.
        pref_dict = {'network.proxy.no_proxies_on': '127.0.0.1',
                     'browser.privatebrowsing.autostart': False}
        for i in range(connrefused_retry_count + 1):
            try:
                driver = TorBrowserDriver(TBB_PATH,
                                          pref_dict=pref_dict,
                                          tbb_logfile_path=LOGFILE_PATH)
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
            except WebDriverException:
                if i < connrefused_retry_count:
                    time.sleep(connrefused_retry_interval)
                raise

    def _create_secondary_firefox_driver(self, profile=None):
        self.f_profile_path = "/tmp/testprofile"
        if os.path.exists(self.f_profile_path):
            shutil.rmtree(self.f_profile_path)
        if self.journalist_location.find('.onion') != -1:
            os.mkdir(self.f_profile_path)
            profile = webdriver.FirefoxProfile(self.f_profile_path)
            # set FF preference to socks proxy in Tor Browser
            profile.set_preference("network.proxy.type", 1)
            profile.set_preference("network.proxy.socks", "127.0.0.1")
            profile.set_preference("network.proxy.socks_port", 9150)
            profile.set_preference("network.proxy.socks_version", 5)
            profile.set_preference("network.proxy.socks_remote_dns", True)
            profile.set_preference("network.dns.blockDotOnion", False)
            profile.update_preferences()
        self.second_driver = webdriver.Firefox(firefox_binary=FIREFOX_PATH,
                                               firefox_profile=profile)
        self.second_driver.implicitly_wait(15)

    def _create_webdriver2(self, profile=None):
        # Only for layout tests
        # see https://review.openstack.org/#/c/375258/ and the
        # associated issues for background on why this is necessary
        connrefused_retry_count = 3
        connrefused_retry_interval = 5
        for i in range(connrefused_retry_count + 1):
            try:
                driver = webdriver.Firefox(firefox_binary=FIREFOX_PATH,
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

    def _javascript_toggle(self):
        # the following is a noop for some reason, workaround it
        # profile.set_preference("javascript.enabled", False)
        # https://stackoverflow.com/a/36782979/837471
        self.driver.get("about:config")
        actions = ActionChains(self.driver)
        actions.send_keys(Keys.RETURN)
        actions.send_keys("javascript.enabled")
        actions.perform()
        actions.send_keys(Keys.TAB)
        actions.send_keys(Keys.RETURN)
        actions.perform()

    def swap_drivers(self):
        if not self.second_driver:
            self._create_secondary_firefox_driver()
        # Only if we two drivers
        if self.driver and self.second_driver:
            self.driver, self.second_driver = self.second_driver, self.driver

    def init_gpg(self):
        """Initialize the GPG keyring and import the journalist key for
        testing.
        """
        gpg = gnupg.GPG(homedir="/tmp/testgpg")
        # Faster to import a pre-generated key than a new one every time.
        for keyfile in (join(FILES_DIR, "test_journalist_key.pub"),
                        join(FILES_DIR, "test_journalist_key.sec")):
            gpg.import_keys(open(keyfile).read())
        return gpg

    def setup(self, session_expiration=30):

        self.localtesting = False
        self.driver = None
        self.second_driver = None
        self.new_totp = None  # To be created runtime

        instance_information_path = join(FUNCTIONAL_TEST_DIR,
                                         'instance_information.json')

        env.create_directories()
        self.gpg = env.init_gpg()

        if os.path.exists(instance_information_path):
            with open(instance_information_path) as fobj:
                data = json.load(fobj)
            self.source_location = data.get('source_location')
            self.journalist_location = data.get('journalist_location')
            self.hidservauth = data.get('hidserv_token', '')
            self.admin_user = data.get('user')
            self.admin_user['totp'] = pyotp.TOTP(self.admin_user['secret'])
            self.sleep_time = data.get('sleep_time', 10)
            if self.hidservauth:
                if self.journalist_location.startswith('http://'):
                    location = self.journalist_location[7:]
                self.add_hidservauth(location, self.hidservauth)
        else:
            self.localtesting = True
            self.__context = journalist_app.create_app(config).app_context()
            self.__context.push()

            self.patcher2 = mock.patch('source_app.main.get_entropy_estimate')
            self.mock_get_entropy_estimate = self.patcher2.start()
            self.mock_get_entropy_estimate.return_value = 8192

            db.create_all()

            # Add our test user
            try:
                valid_password = "correct horse battery staple profanity oil chewy"  # noqa: E501
                user = Journalist(username='journalist',
                                  password=valid_password,
                                  is_admin=True)
                user.otp_secret = 'JHCOGO7VCER3EJ4L'
                db.session.add(user)
                db.session.commit()
            except IntegrityError:
                print("Test user already added")
                db.session.rollback()

            source_port = self._unused_port()
            journalist_port = self._unused_port()

            self.source_location = "http://127.0.0.1:%d" % source_port
            self.journalist_location = "http://127.0.0.1:%d" % journalist_port

            # Allow custom session expiration lengths
            self.session_expiration = session_expiration

            self.source_app = source_app.create_app(config)
            self.journalist_app = journalist_app.create_app(config)

            # This user is required for our tests cases to login
            self.admin_user = {
                                "name": "journalist",
                                "password": ("correct horse battery staple"
                                             " profanity oil chewy"),
                                "secret": "JHCOGO7VCER3EJ4L"}
            self.admin_user['totp'] = pyotp.TOTP(self.admin_user['secret'])
            self.sleep_time = 2

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

        signal.signal(signal.SIGUSR1, lambda _, s: traceback.print_stack(s))

        # Allow custom session expiration lengths
        self.session_expiration = session_expiration

        if not hasattr(self, 'override_driver'):
            # Means this is not pages-layout tests
            self._create_secondary_firefox_driver()
            self.driver = self._create_webdriver()
        else:
            # We will use a normal firefox esr for the pages-layout tests
            self.driver = self._create_webdriver2(self.new_profile)  # noqa # pylint: disable=no-member

            # Set window size and position explicitly to avoid potential bugs
            # due to discrepancies between environments.
            self.driver.set_window_position(0, 0)
            self.driver.set_window_size(1024, 768)

            self._javascript_toggle()

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
        self.driver.implicitly_wait(15)

        self.secret_message = ('These documents outline a major government '
                               'invasion of privacy.')

    def teardown(self):

        if self.driver:
            self.driver.quit()
        if self.second_driver:
            self.second_driver.quit()
        if self.localtesting:
            self.source_process.terminate()
            self.journalist_process.terminate()
            self.__context.pop()

    def create_new_totp(self, secret):
        self.new_totp = pyotp.TOTP(secret)

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
