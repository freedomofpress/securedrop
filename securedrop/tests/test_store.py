# -*- coding: utf-8 -*-
import os
import shutil
import unittest
import zipfile

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import config
from db import db_session
import store
import utils


class TestStore(unittest.TestCase):

    """The set of tests for store.py."""

    def setUp(self):
        utils.env.setup()

    def tearDown(self):
        utils.env.teardown()
        db_session.remove()

    def test_path_returns_filename_of_folder(self):
        """store.path is called in this way in journalist.delete_collection"""
        filesystem_id = 'example'

        generated_absolute_path = store.path(filesystem_id)

        expected_absolute_path = os.path.join(config.STORE_DIR, filesystem_id)
        self.assertEquals(generated_absolute_path, expected_absolute_path)

    def test_path_returns_filename_of_items_within_folder(self):
        """store.path is called in this way in journalist.bulk_delete"""
        filesystem_id = 'example'
        item_filename = '1-quintuple_cant-msg.gpg'

        generated_absolute_path = store.path(filesystem_id, item_filename)

        expected_absolute_path = os.path.join(config.STORE_DIR,
                                              filesystem_id, item_filename)
        self.assertEquals(generated_absolute_path, expected_absolute_path)

    def test_verify_path_not_absolute(self):
        with self.assertRaises(store.PathException):
            store.verify(os.path.join(config.STORE_DIR, '..', 'etc', 'passwd'))

    def test_verify_in_store_dir(self):
        with self.assertRaisesRegexp(store.PathException, 'Invalid directory'):
            store.verify(config.STORE_DIR + "_backup")

    def test_verify_store_dir_not_absolute(self):
        STORE_DIR = config.STORE_DIR
        try:
            with self.assertRaisesRegexp(
                    store.PathException,
                    'config.STORE_DIR\(\S*\) is not absolute'):
                config.STORE_DIR = '.'
                store.verify('something')
        finally:
            config.STORE_DIR = STORE_DIR

    def test_verify_flagged_file_in_sourcedir_returns_true(self):
        # Simulate source directory with flagged file
        source_directory = os.path.join(config.STORE_DIR,
                                        'example-filesystem-id')
        os.makedirs(source_directory)

        flagged_file_path = os.path.join(source_directory, '_FLAG')
        with open(flagged_file_path, 'a'):
            os.utime(flagged_file_path, None)

        # This should be considered a valid path by verify
        self.assertTrue(store.verify(flagged_file_path))

        # Clean up created files
        shutil.rmtree(source_directory)

    def test_verify_invalid_file_extension_in_sourcedir_raises_exception(self):
        # Simulate source directory with flagged file
        source_directory = os.path.join(config.STORE_DIR,
                                        'example-filesystem-id')
        os.makedirs(source_directory)

        invalid_file_path = os.path.join(source_directory, 'not_valid.txt')
        with open(invalid_file_path, 'a'):
            os.utime(invalid_file_path, None)

        # This should not be considered a valid path by verify
        with self.assertRaisesRegexp(
                store.PathException,
                'Invalid file extension .txt'):
            store.verify(invalid_file_path)

        # Clean up created files
        shutil.rmtree(source_directory)

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
        actual_filename = store.rename_submission(
            source.filesystem_id, old_filename,
            new_journalist_filename)
        self.assertEquals(actual_filename, expected_filename)
