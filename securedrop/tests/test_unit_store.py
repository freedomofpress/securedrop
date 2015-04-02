#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import unittest
import zipfile
import config
import store
import common
from db import db_session, Source
import crypto_util

# Set environment variable so config.py uses a test environment
os.environ['SECUREDROP_ENV'] = 'test'


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

        archive = zipfile.ZipFile(store.get_bulk_archive(filenames))

        archivefile_contents = archive.namelist()

        for archived_file, actual_file in zip(archivefile_contents, filenames):
            actual_file_content = open(actual_file).read()
            zipped_file_content = archive.read(archived_file)
            self.assertEquals(zipped_file_content, actual_file_content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
