# -*- coding: utf-8 -*-
import os
import io
import pytest
import re
import store
import zipfile

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from . import utils

from db import db
from journalist_app import create_app
from models import Submission, Reply
from store import Storage, queued_add_checksum_for_file, async_add_checksum_for_file


def create_file_in_source_dir(config, filesystem_id, filename):
    """Helper function for simulating files"""
    source_directory = os.path.join(config.STORE_DIR,
                                    filesystem_id)
    os.makedirs(source_directory)

    file_path = os.path.join(source_directory, filename)
    with io.open(file_path, 'a'):
        os.utime(file_path, None)

    return source_directory, file_path


def test_path_returns_filename_of_folder(journalist_app, config):
    """`Storage.path` is called in this way in
        journalist.delete_collection
    """
    filesystem_id = 'example'
    generated_absolute_path = journalist_app.storage.path(filesystem_id)

    expected_absolute_path = os.path.join(config.STORE_DIR, filesystem_id)
    assert generated_absolute_path == expected_absolute_path


def test_path_returns_filename_of_items_within_folder(journalist_app, config):
    """`Storage.path` is called in this way in journalist.bulk_delete"""
    filesystem_id = 'example'
    item_filename = '1-quintuple_cant-msg.gpg'
    generated_absolute_path = journalist_app.storage.path(filesystem_id,
                                                          item_filename)

    expected_absolute_path = os.path.join(config.STORE_DIR,
                                          filesystem_id, item_filename)
    assert generated_absolute_path == expected_absolute_path


def test_path_without_filesystem_id(journalist_app, config):
    filesystem_id = 'example'
    item_filename = '1-quintuple_cant-msg.gpg'

    basedir = os.path.join(config.STORE_DIR, filesystem_id)
    os.makedirs(basedir)

    path_to_file = os.path.join(basedir, item_filename)
    with open(path_to_file, 'a'):
        os.utime(path_to_file, None)

    generated_absolute_path = \
        journalist_app.storage.path_without_filesystem_id(item_filename)

    expected_absolute_path = os.path.join(config.STORE_DIR,
                                          filesystem_id, item_filename)
    assert generated_absolute_path == expected_absolute_path


def test_path_without_filesystem_id_duplicate_files(journalist_app, config):
    filesystem_id = 'example'
    filesystem_id_duplicate = 'example2'
    item_filename = '1-quintuple_cant-msg.gpg'

    basedir = os.path.join(config.STORE_DIR, filesystem_id)
    duplicate_basedir = os.path.join(config.STORE_DIR, filesystem_id_duplicate)

    for directory in [basedir, duplicate_basedir]:
        os.makedirs(directory)
        path_to_file = os.path.join(directory, item_filename)
        with open(path_to_file, 'a'):
            os.utime(path_to_file, None)

    with pytest.raises(store.TooManyFilesException):
        journalist_app.storage.path_without_filesystem_id(item_filename)


def test_path_without_filesystem_id_no_file(journalist_app, config):
    item_filename = 'not there'
    with pytest.raises(store.NoFileFoundException):
        journalist_app.storage.path_without_filesystem_id(item_filename)


def test_verify_path_not_absolute(journalist_app, config):
    with pytest.raises(store.PathException):
        journalist_app.storage.verify(
            os.path.join(config.STORE_DIR, '..', 'etc', 'passwd'))


def test_verify_in_store_dir(journalist_app, config):
    with pytest.raises(store.PathException) as e:
        journalist_app.storage.verify(config.STORE_DIR + "_backup")

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


def test_verify_flagged_file_in_sourcedir_returns_true(journalist_app, config):
    source_directory, file_path = create_file_in_source_dir(
        config, 'example-filesystem-id', '_FLAG'
    )

    assert journalist_app.storage.verify(file_path)


def test_verify_invalid_file_extension_in_sourcedir_raises_exception(
        journalist_app, config):

    source_directory, file_path = create_file_in_source_dir(
        config, 'example-filesystem-id', 'not_valid.txt'
    )

    with pytest.raises(store.PathException) as e:
        journalist_app.storage.verify(file_path)

    assert 'Invalid file extension .txt' in str(e)


def test_verify_invalid_filename_in_sourcedir_raises_exception(
        journalist_app, config):

    source_directory, file_path = create_file_in_source_dir(
        config, 'example-filesystem-id', 'NOTVALID.gpg'
    )

    with pytest.raises(store.PathException) as e:
        journalist_app.storage.verify(file_path)

    assert 'Invalid filename NOTVALID.gpg' in str(e)


def test_get_zip(journalist_app, test_source, config):
    with journalist_app.app_context():
        submissions = utils.db_helper.submit(
            test_source['source'], 2)
        filenames = [os.path.join(config.STORE_DIR,
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


@pytest.mark.parametrize('db_model', [Submission, Reply])
def test_add_checksum_for_file(config, db_model):
    '''
    Check that when we execute the `add_checksum_for_file` function, the database object is
    correctly updated with the actual hash of the file.

    We have to create our own app in order to have more control over the SQLAlchemy sessions. The
    fixture pushes a single app context that forces us to work within a single transaction.
    '''
    app = create_app(config)

    with app.app_context():
        db.create_all()
        source, _ = utils.db_helper.init_source_without_keypair()
        target_file_path = app.storage.path(source.filesystem_id, '1-foo-msg.gpg')
        test_message = b'hash me!'
        expected_hash = 'f1df4a6d8659471333f7f6470d593e0911b4d487856d88c83d2d187afa195927'

        with open(target_file_path, 'wb') as f:
            f.write(test_message)

        if db_model == Submission:
            db_obj = Submission(source, target_file_path)
        else:
            journalist, _ = utils.db_helper.init_journalist()
            db_obj = Reply(journalist, source, target_file_path)

        db.session.add(db_obj)
        db.session.commit()
        db_obj_id = db_obj.id

    queued_add_checksum_for_file(db_model,
                                 db_obj_id,
                                 target_file_path,
                                 app.config['SQLALCHEMY_DATABASE_URI'])

    with app.app_context():
        # requery to get a new object
        db_obj = db_model.query.filter_by(id=db_obj_id).one()
        assert db_obj.checksum == 'sha256:' + expected_hash


@pytest.mark.parametrize('db_model', [Submission, Reply])
def test_async_add_checksum_for_file(config, db_model):
    '''
    Check that when we execute the `add_checksum_for_file` function, the database object is
    correctly updated with the actual hash of the file.

    We have to create our own app in order to have more control over the SQLAlchemy sessions. The
    fixture pushes a single app context that forces us to work within a single transaction.
    '''
    app = create_app(config)

    with app.app_context():
        db.create_all()
        source, _ = utils.db_helper.init_source_without_keypair()
        target_file_path = app.storage.path(source.filesystem_id, '1-foo-msg.gpg')
        test_message = b'hash me!'
        expected_hash = 'f1df4a6d8659471333f7f6470d593e0911b4d487856d88c83d2d187afa195927'

        with open(target_file_path, 'wb') as f:
            f.write(test_message)

        if db_model == Submission:
            db_obj = Submission(source, target_file_path)
        else:
            journalist, _ = utils.db_helper.init_journalist()
            db_obj = Reply(journalist, source, target_file_path)

        db.session.add(db_obj)
        db.session.commit()
        db_obj_id = db_obj.id

        job = async_add_checksum_for_file(db_obj)

    utils.asynchronous.wait_for_redis_worker(job, timeout=5)

    with app.app_context():
        # requery to get a new object
        db_obj = db_model.query.filter_by(id=db_obj_id).one()
        assert db_obj.checksum == 'sha256:' + expected_hash
