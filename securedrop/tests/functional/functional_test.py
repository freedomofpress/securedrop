import unittest
from selenium import webdriver
from multiprocessing import Process
import socket
import shutil
import os
import gnupg
import urllib2

os.environ['SECUREDROP_ENV'] = 'test'
import config

import source
import journalist
import test_setup
import urllib2

class FunctionalTest():

    def _unused_port(self):
        s = socket.socket()
        s.bind(("localhost", 0))
        port = s.getsockname()[1]
        s.close()
        return port

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

        self.driver = webdriver.Firefox()

        self.secret_message = 'blah blah blah'

    def tearDown(self):
        test_setup.clean_root()
        self.driver.quit()
        self.source_process.terminate()
        self.journalist_process.terminate()

