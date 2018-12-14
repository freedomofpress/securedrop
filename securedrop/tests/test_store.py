# -*- coding: utf-8 -*-
import os
import io
import pytest
import re
import store
import zipfile

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import utils

from store import Storage


def create_file_in_source_dir(journalist_config, filesystem_id, filename):
    """Helper function for simulating files"""
    source_directory = os.path.join(journalist_config.STORE_DIR,
                                    filesystem_id)
    os.makedirs(source_directory)

    file_path = os.path.join(source_directory, filename)
    with io.open(file_path, 'a'):
        os.utime(file_path, None)

    return source_directory, file_path


def test_path_returns_filename_of_folder(journalist_app, journalist_config):
    """`Storage.path` is called in this way in
        journalist.delete_collection
    """
    filesystem_id = 'example'
    generated_absolute_path = journalist_app.storage.path(filesystem_id)

    expected_absolute_path = os.path.join(journalist_config.STORE_DIR,
                                          filesystem_id)
    assert generated_absolute_path == expected_absolute_path


def test_path_returns_filename_of_items_within_folder(journalist_app,
                                                      journalist_config):
    """`Storage.path` is called in this way in journalist.bulk_delete"""
    filesystem_id = 'example'
    item_filename = '1-quintuple_cant-msg.gpg'
    generated_absolute_path = journalist_app.storage.path(filesystem_id,
                                                          item_filename)

    expected_absolute_path = os.path.join(journalist_config.STORE_DIR,
                                          filesystem_id, item_filename)
    assert generated_absolute_path == expected_absolute_path


def test_verify_path_not_absolute(journalist_app, journalist_config):
    with pytest.raises(store.PathException):
        journalist_app.storage.verify(
            os.path.join(journalist_config.STORE_DIR, '..', 'etc', 'passwd'))


def test_verify_in_store_dir(journalist_app, journalist_config):
    with pytest.raises(store.PathException) as e:
        journalist_app.storage.verify(journalist_config.STORE_DIR + "_backup")

    assert 'Invalid directory' in str(e)


def test_verify_store_path_not_absolute(journalist_app):
    with pytest.raises(store.PathException) as e:
        journalist_app.storage.verify('..')

    assert 'The path is not absolute and/or normalized' in str(e)


def test_verify_store_dir_not_absolute():
    with pytest.raises(store.PathException) as exc_info:
        Storage('..', '/', '<not a gpg key>')

    msg = str(exc_info.value)
    assert re.compile('storage_path.*is not absolute').match(msg)


def test_verify_store_temp_dir_not_absolute():
    with pytest.raises(store.PathException) as exc_info:
        Storage('/', '..', '<not a gpg key>')

    msg = str(exc_info.value)
    assert re.compile('temp_dir.*is not absolute').match(msg)


def test_verify_flagged_file_in_sourcedir_returns_true(journalist_app,
                                                       journalist_config):
    source_directory, file_path = create_file_in_source_dir(
        journalist_config, 'example-filesystem-id', '_FLAG'
    )

    assert journalist_app.storage.verify(file_path)


def test_verify_invalid_file_extension_in_sourcedir_raises_exception(
        journalist_app, journalist_config):

    source_directory, file_path = create_file_in_source_dir(
        journalist_config, 'example-filesystem-id', 'not_valid.txt'
    )

    with pytest.raises(store.PathException) as e:
        journalist_app.storage.verify(file_path)

    assert 'Invalid file extension .txt' in str(e)


def test_verify_invalid_filename_in_sourcedir_raises_exception(
        journalist_app, journalist_config):

    source_directory, file_path = create_file_in_source_dir(
        journalist_config, 'example-filesystem-id', 'NOTVALID.gpg'
    )

    with pytest.raises(store.PathException) as e:
        journalist_app.storage.verify(file_path)

    assert 'Invalid filename NOTVALID.gpg' in str(e)


def test_get_zip(journalist_app, test_source, journalist_config):
    with journalist_app.app_context():
        submissions = utils.db_helper.submit(
            test_source['source'], 2)
        filenames = [os.path.join(journalist_config.STORE_DIR,
                                  test_source['filesystem_id'],
                                  submission.filename)
                     for submission in submissions]

        archive = zipfile.ZipFile(
            journalist_app.storage.get_bulk_archive(submissions))
        archivefile_contents = archive.namelist()

    for archived_file, actual_file in zip(archivefile_contents, filenames):
        with io.open(actual_file, 'rb') as f:
            actual_file_content = f.read()
        zipped_file_content = archive.read(archived_file)
        assert zipped_file_content == actual_file_content


def test_rename_valid_submission(journalist_app, test_source):
    with journalist_app.app_context():
        old_journalist_filename = test_source['source'].journalist_filename
        old_filename = utils.db_helper.submit(
            test_source['source'], 1)[0].filename

        new_journalist_filename = 'nestor_makhno'
        expected_filename = old_filename.replace(old_journalist_filename,
                                                 new_journalist_filename)
        actual_filename = journalist_app.storage.rename_submission(
            test_source['source'].filesystem_id, old_filename,
            new_journalist_filename)

    assert actual_filename == expected_filename


def test_rename_submission_with_invalid_filename(journalist_app):
    original_filename = '1-quintuple_cant-msg.gpg'
    returned_filename = journalist_app.storage.rename_submission(
            'example-filesystem-id', original_filename,
            'this-new-filename-should-not-be-returned')

    # None of the above files exist, so we expect the attempt to rename
    # the submission to fail and the original filename to be returned.
    assert original_filename == returned_filename
