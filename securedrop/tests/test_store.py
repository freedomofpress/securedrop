import logging
import os
import re
import stat
import time
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator

import pytest
import store
from db import db
from journalist_app import create_app
from models import Reply, Submission
from passphrases import PassphraseGenerator
from rq.job import Job
from store import Storage, async_add_checksum_for_file, queued_add_checksum_for_file
from tests import utils
from tests.factories.models_factories import SourceFactory


@pytest.fixture(scope="function")
def test_storage() -> Generator[Storage, None, None]:
    # Setup the filesystem for the storage object
    with TemporaryDirectory() as data_dir_name:
        data_dir = Path(data_dir_name)
        store_dir = data_dir / "store"
        store_dir.mkdir()
        tmp_dir = data_dir / "tmp"
        tmp_dir.mkdir()

        storage = Storage(str(store_dir), str(tmp_dir))

        yield storage


def create_file_in_source_dir(base_dir, filesystem_id, filename):
    """Helper function for simulating files"""
    source_directory = os.path.join(base_dir, filesystem_id)
    os.makedirs(source_directory)

    file_path = os.path.join(source_directory, filename)
    with open(file_path, "a"):
        os.utime(file_path, None)

    return source_directory, file_path


def test_path_returns_filename_of_folder(test_storage):
    """`Storage.path` is called in this way in
    journalist.delete_collection
    """
    filesystem_id = "example"
    generated_absolute_path = test_storage.path(filesystem_id)

    expected_absolute_path = os.path.join(test_storage.storage_path, filesystem_id)
    assert generated_absolute_path == expected_absolute_path


def test_path_returns_filename_of_items_within_folder(test_storage):
    """`Storage.path` is called in this  way in journalist.bulk_delete"""
    filesystem_id = "example"
    item_filename = "1-quintuple_cant-msg.gpg"
    generated_absolute_path = test_storage.path(filesystem_id, item_filename)

    expected_absolute_path = os.path.join(test_storage.storage_path, filesystem_id, item_filename)
    assert generated_absolute_path == expected_absolute_path


def test_path_without_filesystem_id(test_storage):
    filesystem_id = "example"
    item_filename = "1-quintuple_cant-msg.gpg"

    basedir = os.path.join(test_storage.storage_path, filesystem_id)
    os.makedirs(basedir)

    path_to_file = os.path.join(basedir, item_filename)
    with open(path_to_file, "a"):
        os.utime(path_to_file, None)

    generated_absolute_path = test_storage.path_without_filesystem_id(item_filename)

    expected_absolute_path = os.path.join(test_storage.storage_path, filesystem_id, item_filename)
    assert generated_absolute_path == expected_absolute_path


def test_path_without_filesystem_id_duplicate_files(test_storage):
    filesystem_id = "example"
    filesystem_id_duplicate = "example2"
    item_filename = "1-quintuple_cant-msg.gpg"

    basedir = os.path.join(test_storage.storage_path, filesystem_id)
    duplicate_basedir = os.path.join(test_storage.storage_path, filesystem_id_duplicate)

    for directory in [basedir, duplicate_basedir]:
        os.makedirs(directory)
        path_to_file = os.path.join(directory, item_filename)
        with open(path_to_file, "a"):
            os.utime(path_to_file, None)

    with pytest.raises(store.TooManyFilesException):
        test_storage.path_without_filesystem_id(item_filename)


def test_path_without_filesystem_id_no_file(test_storage):
    item_filename = "not there"
    with pytest.raises(store.NoFileFoundException):
        test_storage.path_without_filesystem_id(item_filename)


def test_verify_path_not_absolute(test_storage):
    with pytest.raises(store.PathException):
        test_storage.verify(os.path.join(test_storage.storage_path, "..", "etc", "passwd"))


def test_verify_in_store_dir(test_storage):
    with pytest.raises(store.PathException) as e:
        path = test_storage.storage_path + "_backup"
        test_storage.verify(path)
        assert e.message == f"Path not valid in store: {path}"


def test_verify_store_path_not_absolute(test_storage):
    with pytest.raises(store.PathException) as e:
        test_storage.verify("..")
        assert e.message == "Path not valid in store: .."


def test_verify_rejects_symlinks(test_storage):
    """
    Test that verify rejects paths involving links outside the store.
    """
    try:
        link = os.path.join(test_storage.storage_path, "foo")
        os.symlink("/foo", link)
        with pytest.raises(store.PathException) as e:
            test_storage.verify(link)
            assert e.message == f"Path not valid in store: {link}"
    finally:
        os.unlink(link)


def test_verify_store_dir_not_absolute():
    with pytest.raises(store.PathException) as exc_info:
        Storage("..", "/")

    msg = str(exc_info.value)
    assert re.compile("storage_path.*is not absolute").match(msg)


def test_verify_store_temp_dir_not_absolute():
    with pytest.raises(store.PathException) as exc_info:
        Storage("/", "..")

    msg = str(exc_info.value)
    assert re.compile("temp_dir.*is not absolute").match(msg)


def test_verify_regular_submission_in_sourcedir_returns_true(test_storage):
    """
    Tests that verify is happy with a regular submission file.

    Verify should return True for a regular file that matches the
    naming scheme of submissions.
    """
    source_directory, file_path = create_file_in_source_dir(
        test_storage.storage_path, "example-filesystem-id", "1-regular-doc.gz.gpg"
    )

    assert test_storage.verify(file_path)


def test_verify_invalid_file_extension_in_sourcedir_raises_exception(test_storage):

    source_directory, file_path = create_file_in_source_dir(
        test_storage.storage_path, "example-filesystem-id", "not_valid.txt"
    )

    with pytest.raises(store.PathException) as e:
        test_storage.verify(file_path)

    assert f"Path not valid in store: {file_path}" in str(e)


def test_verify_invalid_filename_in_sourcedir_raises_exception(test_storage):

    source_directory, file_path = create_file_in_source_dir(
        test_storage.storage_path, "example-filesystem-id", "NOTVALID.gpg"
    )

    with pytest.raises(store.PathException) as e:
        test_storage.verify(file_path)
        assert e.message == f"Path not valid in store: {file_path}"


def test_get_zip(journalist_app, test_source, app_storage, config):
    with journalist_app.app_context():
        submissions = utils.db_helper.submit(app_storage, test_source["source"], 2)
        filenames = [
            os.path.join(config.STORE_DIR, test_source["filesystem_id"], submission.filename)
            for submission in submissions
        ]

        archive = zipfile.ZipFile(app_storage.get_bulk_archive(submissions))
        archivefile_contents = archive.namelist()

    for archived_file, actual_file in zip(archivefile_contents, filenames):
        with open(actual_file, "rb") as f:
            actual_file_content = f.read()
        zipped_file_content = archive.read(archived_file)
        assert zipped_file_content == actual_file_content


@pytest.mark.parametrize("db_model", [Submission, Reply])
def test_add_checksum_for_file(config, app_storage, db_model):
    """
    Check that when we execute the `add_checksum_for_file` function, the database object is
    correctly updated with the actual hash of the file.

    We have to create our own app in order to have more control over the SQLAlchemy sessions. The
    fixture pushes a single app context that forces us to work within a single transaction.
    """
    app = create_app(config)

    test_storage = app_storage

    with app.app_context():
        db.create_all()
        source = SourceFactory.create(db.session, app_storage)
        target_file_path = test_storage.path(source.filesystem_id, "1-foo-msg.gpg")
        test_message = b"hash me!"
        expected_hash = "f1df4a6d8659471333f7f6470d593e0911b4d487856d88c83d2d187afa195927"

        with open(target_file_path, "wb") as f:
            f.write(test_message)

        if db_model == Submission:
            db_obj = Submission(source, target_file_path, app_storage)
        else:
            journalist, _ = utils.db_helper.init_journalist()
            db_obj = Reply(journalist, source, target_file_path, app_storage)

        db.session.add(db_obj)
        db.session.commit()
        db_obj_id = db_obj.id

    queued_add_checksum_for_file(
        db_model, db_obj_id, target_file_path, app.config["SQLALCHEMY_DATABASE_URI"]
    )

    with app.app_context():
        # requery to get a new object
        db_obj = db_model.query.filter_by(id=db_obj_id).one()
        assert db_obj.checksum == "sha256:" + expected_hash


def _wait_for_redis_worker(job: Job, timeout: int = 60) -> None:
    """Raise an error if the Redis job doesn't complete successfully
    before a timeout.

    :param rq.job.Job job: A Redis job to wait for.

    :param int timeout: Seconds to wait for the job to finish.

    :raises: An :exc:`AssertionError`.
    """
    # This is an arbitrarily defined value in the SD codebase and not something from rqworker
    redis_success_return_value = "success"

    start_time = time.time()
    while time.time() - start_time < timeout:
        if job.result == redis_success_return_value:
            return
        elif job.result not in (None, redis_success_return_value):
            assert False, "Redis worker failed!"
        time.sleep(0.1)
    assert False, "Redis worker timed out!"


@pytest.mark.parametrize("db_model", [Submission, Reply])
def test_async_add_checksum_for_file(config, app_storage, db_model):
    """
    Check that when we execute the `add_checksum_for_file` function, the database object is
    correctly updated with the actual hash of the file.

    We have to create our own app in order to have more control over the SQLAlchemy sessions. The
    fixture pushes a single app context that forces us to work within a single transaction.
    """
    app = create_app(config)

    with app.app_context():
        db.create_all()
        source = SourceFactory.create(db.session, app_storage)
        target_file_path = app_storage.path(source.filesystem_id, "1-foo-msg.gpg")
        test_message = b"hash me!"
        expected_hash = "f1df4a6d8659471333f7f6470d593e0911b4d487856d88c83d2d187afa195927"

        with open(target_file_path, "wb") as f:
            f.write(test_message)

        if db_model == Submission:
            db_obj = Submission(source, target_file_path, app_storage)
        else:
            journalist, _ = utils.db_helper.init_journalist()
            db_obj = Reply(journalist, source, target_file_path, app_storage)

        db.session.add(db_obj)
        db.session.commit()
        db_obj_id = db_obj.id

        job = async_add_checksum_for_file(db_obj, app_storage)

    _wait_for_redis_worker(job, timeout=5)

    with app.app_context():
        # requery to get a new object
        db_obj = db_model.query.filter_by(id=db_obj_id).one()
        assert db_obj.checksum == "sha256:" + expected_hash


def test_path_configuration_is_immutable(test_storage):
    """
    Check that the store's paths cannot be changed.

    They're exposed via properties that are supposed to be
    read-only. It is of course possible to change them via the mangled
    attribute names, but we want to confirm that accidental changes
    are prevented.
    """
    with pytest.raises(AttributeError):
        test_storage.storage_path = "/foo"

    original_storage_path = test_storage.storage_path[:]
    test_storage.__storage_path = "/foo"
    assert test_storage.storage_path == original_storage_path

    with pytest.raises(AttributeError):
        test_storage.shredder_path = "/foo"

    original_shredder_path = test_storage.shredder_path[:]
    test_storage.__shredder_path = "/foo"
    assert test_storage.shredder_path == original_shredder_path


def test_shredder_configuration(journalist_app, app_storage):
    """
    Ensure we're creating the shredder directory correctly.

    We want to ensure that it's a sibling of the store directory, with
    mode 0700.
    """
    store_path = app_storage.storage_path
    shredder_path = app_storage.shredder_path
    assert os.path.dirname(shredder_path) == os.path.dirname(store_path)
    s = os.stat(shredder_path)
    assert stat.S_ISDIR(s.st_mode) is True
    assert stat.S_IMODE(s.st_mode) == 0o700


def test_shredder_deletes_symlinks(journalist_app, app_storage, caplog):
    """
    Confirm that `store.clear_shredder` removes any symlinks in the shredder.
    """
    caplog.set_level(logging.DEBUG)

    link_target = "/foo"
    link = os.path.abspath(os.path.join(app_storage.shredder_path, "foo"))
    os.symlink(link_target, link)
    app_storage.clear_shredder()
    assert f"Deleting link {link} to {link_target}" in caplog.text
    assert not os.path.exists(link)


def test_shredder_shreds(journalist_app, app_storage, caplog):
    """
    Confirm that `store.clear_shredder` removes files.
    """
    caplog.set_level(logging.DEBUG)

    testdir = os.path.abspath(os.path.join(app_storage.shredder_path, "testdir"))
    os.makedirs(testdir)
    testfile = os.path.join(testdir, "testfile")
    with open(testfile, "w") as f:
        f.write("testdata\n")

    app_storage.clear_shredder()
    assert f"Securely deleted file 1/1: {testfile}" in caplog.text
    assert not os.path.isfile(testfile)
    assert not os.path.isdir(testdir)
