import unittest
from flask import session, g, escape
from cStringIO import StringIO
from io import BytesIO
from mock import patch

import source
import test_setup

class TestSecureFileUpload(unittest.TestCase):

    def setUp(self):
        self.app = source.app
        self.client = self.app.test_client()
        test_setup.create_directories()
        test_setup.init_gpg()
        test_setup.init_db()

    # from test_unit.py:133
    def _new_codename(self):
        """Helper function to go through the "generate codename" flow"""
        with self.client as c:
            rv = c.get('/generate')
            codename = session['codename']
            rv = c.post('/create')
        return codename

    @patch('request_that_secures_file_uploads.create_secure_file_stream')
    def test_custom_file_upload_stream(self, create_secure_file_stream):
        create_secure_file_stream.return_value = BytesIO()
        self._new_codename()

        self.client.post('/submit', data=dict(
            msg="",
            fh=(StringIO('This is a test'), "filename"),
        ), follow_redirects=True)

        create_secure_file_stream.assert_any_call()
