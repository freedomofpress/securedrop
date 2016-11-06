#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import unittest
import zipfile
# Set environment variable so config.py uses a test environment
os.environ['SECUREDROP_ENV'] = 'test'
import config
import store
import common
from db import db_session, Source, Submission
import crypto_util


class TestStore(unittest.TestCase):

    """The set of tests for store.py."""

    def setUp(self):
        common.shared_setup()

    def tearDown(self):
        common.shared_teardown()

    def test_verify(self):
        with self.assertRaises(store.PathException):
            store.verify(os.path.join(config.STORE_DIR, '..', 'etc', 'passwd'))
        with self.assertRaises(store.PathException):
            store.verify(config.STORE_DIR + "_backup")

    def test_get_zip(self):
        sid = 'EQZGCJBRGISGOTC2NZVWG6LILJBHEV3CINNEWSCLLFTUWZJPKJFECLS2NZ4G4U3QOZCFKTTPNZMVIWDCJBBHMUDBGFHXCQ3R'
        source = Source(sid, crypto_util.display_id())
        db_session.add(source)
        db_session.commit()

        files = ['1-abc1-msg.gpg', '2-abc2-msg.gpg']
        filenames = common.setup_test_docs(sid, files)
        submissions = Submission.query.all()

        archive = zipfile.ZipFile(store.get_bulk_archive(submissions))

        archivefile_contents = archive.namelist()

        for archived_file, actual_file in zip(archivefile_contents, filenames):
            actual_file_content = open(actual_file).read()
            zipped_file_content = archive.read(archived_file)
            self.assertEquals(zipped_file_content, actual_file_content)

    def test_rename_valid_submission(self):
        sid = 'EQZGCJBRGISGOTC2NZVWG6LILJBHEV3CINNEWSCLLFTUWZJPKJFECLS2NZ4G4U3QOZCFKTTPNZMVIWDCJBBHMUDBGFHXCQ3R'

        source_dir = os.path.join(config.STORE_DIR, sid)
        if not os.path.exists(source_dir):
            os.makedirs(source_dir)

        old_filename = '1-abc1-msg.gpg'
        open(os.path.join(source_dir, old_filename), 'w').close()

        new_filestem = 'abc2'
        expected_filename = '1-abc2-msg.gpg'
        actual_filename = store.rename_submission(sid, old_filename,
                                                  new_filestem)
        self.assertEquals(actual_filename, expected_filename)

if __name__ == "__main__":
    unittest.main(verbosity=2)
