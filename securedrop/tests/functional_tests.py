import unittest
from selenium import webdriver
from multiprocessing import Process
import socket
import shutil
import os
import gnupg
import urllib2
import time
import sys

os.environ['SECUREDROP_ENV'] = 'test'
import config

import source
import journalist
import test_setup

class SubmitAndRetrieveHappyPath(unittest.TestCase):

    def _unused_port(self):
        s = socket.socket()
        s.bind(("localhost", 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def _wait_until_up(self, url, server_name):
        seconds_to_wait = 10
        sleep_time = 0.1
        for _ in range(int(seconds_to_wait / sleep_time)):
            try:
                urllib2.urlopen(url).getcode()
                return
            except urllib2.URLError:
                time.sleep(sleep_time)
        sys.exit("could not start %s server" % server_name)

    def setUp(self):
        test_setup.create_directories()
        self.gpg = test_setup.init_gpg()
        test_setup.init_db()

        source_port = self._unused_port()
        journalist_port = self._unused_port()

        self.source_location = "http://localhost:%d" % source_port
        self.journalist_location = "http://localhost:%d" % journalist_port

        def start_source_server():
            source.app.run(port=source_port,
                           debug=True,
                           use_reloader=False)

        def start_journalist_server():
            journalist.app.run(port=journalist_port,
                               debug=True,
                               use_reloader=False)

        self.source_process = Process(target = start_source_server)
        self.journalist_process = Process(target = start_journalist_server)

        self.source_process.start()
        self.journalist_process.start()

        self._wait_until_up(self.source_location, "source")
        self._wait_until_up(self.journalist_location, "journalist")

        self.driver = webdriver.PhantomJS()

        self.secret_message = 'blah blah blah'

    def tearDown(self):
        test_setup.clean_root()
        self.driver.quit()
        self.source_process.terminate()
        self.journalist_process.terminate()

    def _source_visits_source_homepage(self):
        self.driver.get(self.source_location)

        self.assertEqual("SecureDrop", self.driver.title)

    def _source_chooses_to_submit_documents(self):
        self.driver.find_element_by_id('submit-documents-button').click()

        code_name = self.driver.find_element_by_css_selector('#code-name')

        self.assertTrue(len(code_name.text) > 0)
        self.source_name = code_name.text

    def _source_continues_to_submit_page(self):
        continue_button = self.driver.find_element_by_id('continue-button')

        continue_button.click()
        headline = self.driver.find_element_by_class_name('headline')
        self.assertEqual('Submit a document, message, or both', headline.text)

    def _source_submits_a_message(self):
        text_box = self.driver.find_element_by_css_selector('[name=msg]')

        text_box.send_keys(self.secret_message) # send_keys = type into text box
        submit_button = self.driver.find_element_by_css_selector(
            'button[type=submit]')
        submit_button.click()

        notification = self.driver.find_element_by_css_selector( 'p.notification')
        self.assertEquals('Thanks! We received your message.', notification.text)

    def _journalist_checks_messages(self):
        self.driver.get(self.journalist_location)

        code_names = self.driver.find_elements_by_class_name('code-name')
        self.assertEquals(1, len(code_names))

    def _journalist_downloads_message(self):
        self.driver.find_element_by_css_selector('.code-name a').click()

        submissions = self.driver.find_elements_by_css_selector( '#submissions a')

        self.assertEqual(1, len(submissions))

        file_url = submissions[0].get_attribute('href')

        encrypted_submission = urllib2.urlopen(file_url).read()
        submission = str(self.gpg.decrypt(encrypted_submission))
        self.assertEqual(self.secret_message, submission)

    def test_submit_and_retrieve_happy_path(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_message()
        self._journalist_checks_messages()
        self._journalist_downloads_message()

if __name__ == "__main__":
    unittest.main(verbosity=2)
