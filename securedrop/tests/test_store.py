# -*- coding: utf-8 -*-
from cStringIO import StringIO
import os
import unittest
import zipfile

from mock import patch, ANY

import crypto_util
os.environ['SECUREDROP_ENV'] = 'test'
import config
from db import db_session, Source
import store
import utils


class TestStore(unittest.TestCase):

    """The set of tests for store.py."""

    def setUp(self):
        utils.env.setup()

    def tearDown(self):
        utils.env.teardown()
        db_session.remove()

    def test_verify_path_not_absolute(self):
        with self.assertRaises(store.PathException):
            store.verify(os.path.join(config.STORE_DIR, '..', 'etc', 'passwd'))

    def test_verify_in_store_dir(self):
        with self.assertRaisesRegexp(store.PathException, 'Invalid directory'):
            store.verify(config.STORE_DIR + "_backup")

    def test_verify_store_dir_not_absolute(self):
        STORE_DIR = config.STORE_DIR
        try:
            with self.assertRaisesRegexp(store.PathException,
                                         'config.STORE_DIR\(\S*\) is not absolute'):
                config.STORE_DIR = '.'
                store.verify('something')
        finally:
            config.STORE_DIR = STORE_DIR

    def test_get_zip(self):
        source, _ = utils.db_helper.init_source()
        submissions = utils.db_helper.submit(source, 2)
        filenames = [os.path.join(config.STORE_DIR,
                                  source.filesystem_id,
                                  submission.filename)
                     for submission in submissions]

        archive = zipfile.ZipFile(store.get_bulk_archive(submissions))
        archivefile_contents = archive.namelist()

        for archived_file, actual_file in zip(archivefile_contents, filenames):
            actual_file_content = open(actual_file).read()
            zipped_file_content = archive.read(archived_file)
            self.assertEquals(zipped_file_content, actual_file_content)

    def test_rename_valid_submission(self):
        source, _ = utils.db_helper.init_source()
        old_journalist_filename = source.journalist_filename
        old_filename = utils.db_helper.submit(source, 1)[0].filename
        new_journalist_filename = 'nestor_makhno'
        expected_filename = old_filename.replace(old_journalist_filename,
                                                 new_journalist_filename)
        actual_filename = store.rename_submission(source.filesystem_id, old_filename,
                                                  new_journalist_filename)
        self.assertEquals(actual_filename, expected_filename)

    @patch('gzip.GzipFile')
    def test_save_file_submission_sanitizes_filename(self, gzipfile):
        """Test that upload file name is sanitized.
        """
        insecure_filename = '../../bin/gpg'
        sanitized_filename = 'bin_gpg'
        source, _ = utils.db_helper.init_source()
        journalist, _ = utils.db_helper.init_journalist()

        # Since we mock gzip.Gzipfile, calling :meth:`write()` on the object
        # returned does not in turn call :meth:`write()` on the
        # SecureTemporaryFile object. So :attr:`last_action` of the
        # SecureTemporaryFile object is not updated, and we run into errors
        # when python-gnupg tries to read from the SecureTemporaryFile object,
        # as the :attr:`last_action` is still `'init'`, so an
        # :exc:`AssertionError` will be raised. To further complicate things,
        # since python-gnupg uses daemon threads, this exception will not
        # rise up the call stack back to our app code, and the call to
        # `crypto_util.encrypt()` in `store.save_file_submission()` will hang
        # indefinitely. To fix this, we mock `crypto_util.encrypt()` as well.
        with patch('crypto_util.encrypt'):
            store.save_file_submission(source.filesystem_id,
                                       source.interaction_count + 1,
                                       journalist,
                                       insecure_filename,
                                       StringIO('_'))

        gzipfile.assert_called_with(filename=sanitized_filename,
                                    mode='wb',
                                    fileobj=ANY)
