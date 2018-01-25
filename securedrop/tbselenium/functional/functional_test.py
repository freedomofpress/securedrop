# -*- coding: utf-8 -*-

from datetime import datetime
import errno
from multiprocessing import Process
import os
from os.path import abspath, dirname, join, realpath, expanduser
import signal
import socket
import time
import traceback
import subprocess
import requests



import pyotp
import gnupg
from selenium import webdriver
from selenium.common.exceptions import (WebDriverException,
                                        NoAlertPresentException)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

TBB_PATH = abspath(join(expanduser('~'), '.local/tbb/tor-browser_en-US/'))
os.environ['TBB_PATH'] = TBB_PATH

from tbselenium.tbdriver import TorBrowserDriver
from tbselenium.utils import start_xvfb, stop_xvfb

os.environ['SECUREDROP_ENV'] = 'test'  # noqa


FUNCTIONAL_TEST_DIR = abspath(dirname(__file__))
LOGFILE_PATH = abspath(join(FUNCTIONAL_TEST_DIR, 'log/firefox.log'))
FILES_DIR = abspath(join(dirname(realpath(__file__)), '../..', 'tests/files'))



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
                                        pref_dict = pref_dict,
                                        tbb_logfile_path = LOGFILE_PATH)
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

    def init_gpg(self):
        """Initialize the GPG keyring and import the journalist key for
        testing.
        """
        gpg = gnupg.GPG(homedir="/tmp/testgpg")
        # Faster to import a pre-generated key than to gen a new one every time.
        for keyfile in (join(FILES_DIR, "test_journalist_key.pub"),
                        join(FILES_DIR, "test_journalist_key.sec")):
            gpg.import_keys(open(keyfile).read())
        return gpg

    def system(self, cmd):
        """
        Invoke a shell command. Primary replacement for os.system calls.
        """
        print(cmd)
        ret = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        out, err = ret.communicate()
        return out

    def setup(self, session_expiration=30):

        signal.signal(signal.SIGUSR1, lambda _, s: traceback.print_stack(s))



        self.source_location = "http://127.0.0.1:8080"
        self.journalist_location = "http://127.0.0.1:8081"
        self.journo = {'password': 'subside pristine smitten sandpaper curler carve waggle',
                       'secret': 'j2ugccqm3iwlydp7', 'name': 'foot'}
        self.journo['totp'] = pyotp.TOTP(self.journo['secret'])
        self.new_totp = None # To be created runtime

        # Allow custom session expiration lengths
        self.session_expiration = session_expiration


        for tick in range(30):
            try:
                requests.get(self.source_location)
                requests.get(self.journalist_location)
            except Exception:
                time.sleep(1)
            else:
                break

        if not hasattr(self, 'override_driver'):
            self.driver = self._create_webdriver()

        self.gpg = self.init_gpg()

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
        #self.driver.set_window_position(0, 0)
        #self.driver.set_window_size(1024, 768)

        self.secret_message = ('These documents outline a major government '
                               'invasion of privacy.')

    def teardown(self):

        if not hasattr(self, 'override_driver'):
            self.driver.quit()

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
