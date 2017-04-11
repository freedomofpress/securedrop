# -*- coding: utf-8 -*-

from datetime import datetime
import mock
from multiprocessing import Process
import os
from os.path import abspath, dirname, join, realpath
import shutil
import signal
import socket
import sys
import time
import traceback
import unittest
import urllib2

from Crypto import Random
import gnupg
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox import firefox_binary
from tbselenium.tbdriver import TorBrowserDriver

os.environ['SECUREDROP_ENV'] = 'test'
import config
import db
import journalist
import source
import tests.utils.env as env

LOG_DIR = abspath(join(dirname(realpath(__file__)), '..', 'log'))

class FunctionalTest():

    def _unused_port(self):
        s = socket.socket()
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
        s.close()
        return port


    def _create_tor_browser_webdriver(self, abs_log_file_path):
        # Creating the TorBrowser driver changes the working directory,
        # so we need to save and then restore the current one.
        old_dir = os.getcwd()

        # Read the TorBrowser location from Ansible
        with open('/opt/.tbb_path_file') as f:
           path_to_tbb = f.readline().strip()
        path_to_tbb = path_to_tbb + os.path.sep + "tor-browser_en-US"
        path_to_tbb = os.path.abspath(path_to_tbb)

        # Due to Travis having opinions, we need to chown the tor dir
        # to be owned by root when we're running CI.
        if '/home/travis/' in path_to_tbb:
            for root, dirs, files in os.walk(path_to_tbb):
                for d in dirs:
                    os.chown(os.path.join(root, d), 0, 0)
                for f in files:
                    os.chown(os.path.join(root, f), 0, 0)

        # Don't use Tor when reading from localhost,
        # and turn off private browsing.
        # We need this to make functional tests work,
        # but they should _not_ be used in any other circumstances
        pref_dict = {
                     'marionette': False,
                     'network.proxy.no_proxies_on': '127.0.0.1',
                     'browser.privatebrowsing.autostart': False
                    }
        driver = TorBrowserDriver(path_to_tbb,
                                  pref_dict=pref_dict,
                                  tbb_logfile_path=abs_log_file_path)

        # Restore the old directory
        os.chdir(old_dir)

        return driver

    def _create_firefox_webdriver(self, abs_log_file_path):
        with open(abs_log_file_path, 'a') as f:
            firefox = firefox_binary.FirefoxBinary(log_file=f)
            return webdriver.Firefox(firefox_binary=firefox)

    def _create_webdriver(self):
        abs_log_file_path = os.path.abspath(join(dirname(__file__), '../log/firefox.log'))
        with open(abs_log_file_path, 'a') as f:
            log_msg = '\n\n[%s] Running Functional Tests\n' % str(datetime.now())
            f.write(log_msg)
            f.flush()

        if 'SD_USE_FALLBACK_BROWSER' in os.environ:
            driver = self._create_firefox_webdriver(abs_log_file_path)
        else:
            driver = self._create_tor_browser_webdriver(abs_log_file_path)

        return driver

    def setUp(self):
        # Patch the two-factor verification to avoid intermittent errors
        patcher = mock.patch('journalist.Journalist.verify_token')
        self.addCleanup(patcher.stop)
        self.mock_journalist_verify_token = patcher.start()
        self.mock_journalist_verify_token.return_value = True

        signal.signal(signal.SIGUSR1, lambda _, s: traceback.print_stack(s))

        env.create_directories()
        self.gpg = env.init_gpg()
        db.init_db()

        source_port = self._unused_port()
        journalist_port = self._unused_port()

        self.source_location = "http://127.0.0.1:%d" % source_port
        self.journalist_location = "http://127.0.0.1:%d" % journalist_port

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
        self.driver = self._create_webdriver()

        # Set window size and position explicitly to avoid potential bugs due
        # to discrepancies between environments.
        self.driver.set_window_position(0, 0);
        self.driver.set_window_size(1024, 768);

        # Poll the DOM briefly to wait for elements. It appears .click() does
        # not always do a good job waiting for the page to load, or perhaps
        # Firefox takes too long to render it (#399)
        self.driver.implicitly_wait(5)
        self.secret_message = 'blah blah blah'

    def tearDown(self):
        env.teardown()
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
