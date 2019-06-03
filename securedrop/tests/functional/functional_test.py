# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
import os
import signal
import socket
import time
import traceback
from datetime import datetime
from multiprocessing import Process
from os.path import abspath
from os.path import dirname
from os.path import expanduser
from os.path import join
from os.path import realpath

import mock
import pyotp
import pytest
import requests
import tbselenium.common as cm
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy.exc import IntegrityError
from tbselenium.tbdriver import TorBrowserDriver

import journalist_app
import source_app
import tests.utils.env as env
from db import db
from models import Journalist
from sdconfig import config

os.environ["SECUREDROP_ENV"] = "test"

LOGFILE_PATH = abspath(join(dirname(realpath(__file__)), "../log/driver.log"))
FIREFOX_PATH = "/usr/bin/firefox/firefox"

TBB_PATH = abspath(join(expanduser("~"), ".local/tbb/tor-browser_en-US/"))
os.environ["TBB_PATH"] = TBB_PATH
TBBRC = join(TBB_PATH, "Browser/TorBrowser/Data/Tor/torrc")
LOGGER.setLevel(logging.WARNING)


class FunctionalTest(object):
    gpg = None
    new_totp = None
    session_expiration = 30
    secret_message = "These documents outline a major government invasion of privacy."
    timeout = 10

    accept_languages = None
    driver = None
    firefox_driver = None
    torbrowser_driver = None

    driver_retry_count = 3
    driver_retry_interval = 5

    def _unused_port(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def create_torbrowser_driver(self):
        logging.info("Creating TorBrowserDriver")
        log_file = open(LOGFILE_PATH, "a")
        log_file.write("\n\n[%s] Running Functional Tests\n" % str(datetime.now()))
        log_file.flush()

        # Don't use Tor when reading from localhost, and turn off private
        # browsing. We need to turn off private browsing because we won't be
        # able to access the browser's cookies in private browsing mode. Since
        # we use session cookies in SD anyway (in private browsing mode all
        # cookies are set as session cookies), this should not affect session
        # lifetime.
        pref_dict = {
            "network.proxy.no_proxies_on": "127.0.0.1",
            "browser.privatebrowsing.autostart": False,
        }
        if self.accept_languages is not None:
            pref_dict["intl.accept_languages"] = self.accept_languages

        for i in range(self.driver_retry_count):
            try:
                self.torbrowser_driver = TorBrowserDriver(
                    TBB_PATH,
                    tor_cfg=cm.USE_RUNNING_TOR,
                    pref_dict=pref_dict,
                    tbb_logfile_path=LOGFILE_PATH,
                )
                logging.info("Created Tor Browser web driver")
                break
            except Exception as e:
                logging.error("Error creating Tor Browser web driver: %s", e)
                if i < self.driver_retry_count:
                    time.sleep(self.driver_retry_interval)

        if not self.torbrowser_driver:
            raise Exception("Could not create Tor Browser web driver")

    def create_firefox_driver(self):
        logging.info("Creating Firefox web driver")

        profile = webdriver.FirefoxProfile()
        if self.accept_languages is not None:
            profile.set_preference("intl.accept_languages", self.accept_languages)
            profile.update_preferences()

        for i in range(self.driver_retry_count):
            try:
                self.firefox_driver = webdriver.Firefox(
                    firefox_binary=FIREFOX_PATH, firefox_profile=profile
                )
                self.firefox_driver.set_window_position(0, 0)
                self.firefox_driver.set_window_size(1024, 768)
                self.firefox_driver.implicitly_wait(self.timeout)
                logging.info("Created Firefox web driver")
                break
            except Exception as e:
                logging.error("Error creating Firefox web driver: %s", e)
                if i < self.driver_retry_count:
                    time.sleep(self.driver_retry_interval)
        if not self.firefox_driver:
            raise Exception("Could not create Firefox web driver")

    def switch_to_firefox_driver(self):
        self.driver = self.firefox_driver
        logging.info("Switched %s to Firefox driver: %s", self, self.driver)

    def switch_to_torbrowser_driver(self):
        self.driver = self.torbrowser_driver
        logging.info("Switched %s to TorBrowser driver: %s", self, self.driver)

    @pytest.fixture(autouse=True)
    def drivers(self):
        logging.info("Creating web drivers")
        self.create_torbrowser_driver()
        self.create_firefox_driver()

        self.switch_to_torbrowser_driver()

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
        self.driver.implicitly_wait(self.timeout)

        yield

        try:
            self.torbrowser_driver.quit()
        except Exception as e:
            logging.error("Error stopping TorBrowser driver: %s", e)

        try:
            self.firefox_driver.quit()
        except Exception as e:
            logging.error("Error stopping Firefox driver: %s", e)

    @pytest.fixture(autouse=True)
    def sd_servers(self):
        logging.info(
            "Starting SecureDrop servers (session expiration = %s)", self.session_expiration
        )

        # Patch the two-factor verification to avoid intermittent errors
        logging.info("Mocking models.Journalist.verify_token")
        with mock.patch("models.Journalist.verify_token", return_value=True):
            logging.info("Mocking source_app.main.get_entropy_estimate")
            with mock.patch("source_app.main.get_entropy_estimate", return_value=8192):

                try:
                    signal.signal(signal.SIGUSR1, lambda _, s: traceback.print_stack(s))

                    source_port = self._unused_port()
                    journalist_port = self._unused_port()

                    self.source_location = "http://127.0.0.1:%d" % source_port
                    self.journalist_location = "http://127.0.0.1:%d" % journalist_port

                    self.source_app = source_app.create_app(config)
                    self.journalist_app = journalist_app.create_app(config)
                    self.journalist_app.config['WTF_CSRF_ENABLED'] = True

                    self.__context = self.journalist_app.app_context()
                    self.__context.push()

                    env.create_directories()
                    db.create_all()
                    self.gpg = env.init_gpg()

                    # Add our test user
                    try:
                        valid_password = "correct horse battery staple profanity oil chewy"
                        user = Journalist(
                            username="journalist", password=valid_password, is_admin=True
                        )
                        user.otp_secret = "JHCOGO7VCER3EJ4L"
                        db.session.add(user)
                        db.session.commit()
                    except IntegrityError:
                        logging.error("Test user already added")
                        db.session.rollback()

                    # This user is required for our tests cases to login
                    self.admin_user = {
                        "name": "journalist",
                        "password": ("correct horse battery staple" " profanity oil chewy"),
                        "secret": "JHCOGO7VCER3EJ4L",
                    }

                    self.admin_user["totp"] = pyotp.TOTP(self.admin_user["secret"])

                    def start_source_server(app):
                        config.SESSION_EXPIRATION_MINUTES = self.session_expiration / 60.0

                        app.run(port=source_port, debug=True, use_reloader=False, threaded=True)

                    def start_journalist_server(app):
                        app.run(port=journalist_port, debug=True, use_reloader=False, threaded=True)

                    self.source_process = Process(
                        target=lambda: start_source_server(self.source_app)
                    )

                    self.journalist_process = Process(
                        target=lambda: start_journalist_server(self.journalist_app)
                    )

                    self.source_process.start()
                    self.journalist_process.start()

                    for tick in range(30):
                        try:
                            requests.get(self.source_location, timeout=1)
                            requests.get(self.journalist_location, timeout=1)
                        except Exception:
                            time.sleep(0.25)
                        else:
                            break
                    yield
                finally:
                    try:
                        self.source_process.terminate()
                    except Exception as e:
                        logging.error("Error stopping source app: %s", e)

                    try:
                        self.journalist_process.terminate()
                    except Exception as e:
                        logging.error("Error stopping source app: %s", e)

                    env.teardown()
                    self.__context.pop()

    def wait_for_source_key(self, source_name):
        filesystem_id = self.source_app.crypto_util.hash_codename(source_name)

        def key_available(filesystem_id):
            assert self.source_app.crypto_util.getkey(filesystem_id)

        self.wait_for(lambda: key_available(filesystem_id), timeout=60)

    def create_new_totp(self, secret):
        self.new_totp = pyotp.TOTP(secret)

    def wait_for(self, function_with_assertion, timeout=None):
        """Polling wait for an arbitrary assertion."""
        # Thanks to
        # http://chimera.labs.oreilly.com/books/1234000000754/ch20.html#_a_common_selenium_problem_race_conditions
        if timeout is None:
            timeout = self.timeout

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                return function_with_assertion()
            except (AssertionError, WebDriverException):
                time.sleep(0.1)
        # one more try, which will raise any errors if they are outstanding
        return function_with_assertion()

    def safe_click_by_id(self, element_id):
        WebDriverWait(self.driver, self.timeout).until(
            expected_conditions.element_to_be_clickable((By.ID, element_id))
        )

        el = self.wait_for(lambda: self.driver.find_element_by_id(element_id))
        el.location_once_scrolled_into_view
        ActionChains(self.driver).move_to_element(el).click().perform()

    def safe_click_by_css_selector(self, selector):
        WebDriverWait(self.driver, self.timeout).until(
            expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )

        el = self.wait_for(lambda: self.driver.find_element_by_css_selector(selector))
        el.location_once_scrolled_into_view
        ActionChains(self.driver).move_to_element(el).click().perform()

    def safe_click_all_by_css_selector(self, selector, root=None):
        if root is None:
            root = self.driver
        els = self.wait_for(lambda: root.find_elements_by_css_selector(selector))
        for el in els:
            el.location_once_scrolled_into_view
            self.wait_for(lambda: el.is_enabled() and el.is_displayed())
            ActionChains(self.driver).move_to_element(el).click().perform()

    def _alert_wait(self, timeout=None):
        if timeout is None:
            timeout = self.timeout
        WebDriverWait(self.driver, timeout).until(
            expected_conditions.alert_is_present(), "Timed out waiting for confirmation popup."
        )

    def _alert_accept(self):
        # adapted from https://stackoverflow.com/a/34795883/837471
        def alert_is_not_present(object):
            """ Expect an alert to not be present."""
            try:
                alert = self.driver.switch_to.alert
                alert.text
                return False
            except NoAlertPresentException:
                return True

        self.driver.switch_to.alert.accept()
        WebDriverWait(self.driver, self.timeout).until(
            alert_is_not_present, "Timed out waiting for confirmation popup to disappear."
        )
