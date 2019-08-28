import argparse
import os

from db import db
from management import submissions
from models import Submission

from tests import utils


def test_delete_disconnected_db_submissions(journalist_app, config):
    """
    Test that Submission records without corresponding files are deleted.
    """
    with journalist_app.app_context():
        source, codename = utils.db_helper.init_source()
        source_id = source.id

        # make two submissions
        utils.db_helper.submit(source, 2)
        submission_id = source.submissions[0].id

        # remove one submission's file
        f1 = os.path.join(config.STORE_DIR, source.filesystem_id, source.submissions[0].filename)
        assert os.path.exists(f1)
        os.remove(f1)
        assert os.path.exists(f1) is False

        # check that the single disconnect is seen
        disconnects = submissions.find_disconnected_db_submissions(config.STORE_DIR)
        assert len(disconnects) == 1
        assert disconnects[0].filename == source.submissions[0].filename

        # remove the disconnected Submission
        args = argparse.Namespace(force=True, store_dir=config.STORE_DIR)
        submissions.delete_disconnected_db_submissions(args)

        assert db.session.query(Submission).filter(Submission.id == submission_id).count() == 0
        assert db.session.query(Submission).filter(Submission.source_id == source_id).count() == 1


def test_delete_disconnected_fs_submissions(journalist_app, config):
    """
    Test that files in the store without corresponding Submission records are deleted.
    """
    source, codename = utils.db_helper.init_source()

    # make two submissions
    utils.db_helper.submit(source, 2)
    source_filesystem_id = source.filesystem_id
    submission_filename = source.submissions[0].filename
    disconnect_path = os.path.join(config.STORE_DIR, source_filesystem_id, submission_filename)

    # delete the first Submission record
    db.session.delete(source.submissions[0])
    db.session.commit()

    disconnects = submissions.find_disconnected_fs_submissions(config.STORE_DIR)
    assert len(disconnects) == 1
    assert disconnects[0] == disconnect_path
    assert os.path.exists(disconnect_path)

    args = argparse.Namespace(force=True, store_dir=config.STORE_DIR)
    submissions.delete_disconnected_fs_submissions(args)

    assert os.path.exists(disconnect_path) is False
