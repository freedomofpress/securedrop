import os
import shutil
import uuid
import subprocess

import gnupg

import config
from db import init_db, db_session, Source, Submission
import crypto_util

# TODO: the PID file for the redis worker is hard-coded below.
# Ideally this constant would be provided by a test harness.
# It has been intentionally omitted from `config.py.example`
# in order to isolate the test vars from prod vars.
# When refactoring the test suite, the TEST_WORKER_PIDFILE
# TEST_WORKER_PIDFILE is also hard-coded in `manage.py`.
TEST_WORKER_PIDFILE = "/tmp/securedrop_test_worker.pid"


def clean_root():
    shutil.rmtree(config.SECUREDROP_DATA_ROOT)


def create_directories():
    # Create directories for the file store and the GPG keyring
    for d in (config.SECUREDROP_DATA_ROOT, config.STORE_DIR,
              config.GPG_KEY_DIR, config.TEMP_DIR):
        if not os.path.isdir(d):
            os.mkdir(d)


def init_gpg():
    # Initialize the GPG keyring
    gpg = gnupg.GPG(homedir=config.GPG_KEY_DIR)
    # Import the journalist key for testing (faster to import a pre-generated
    # key than to gen a new one every time)
    for keyfile in ("test_journalist_key.pub", "test_journalist_key.sec"):
        gpg.import_keys(open(keyfile).read())
    return gpg


def setup_test_docs(sid, files):
    filenames = [os.path.join(config.STORE_DIR, sid, file) for file in files]

    for filename in filenames:
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'w') as fp:
            fp.write(str(uuid.uuid4()))

        # Add Submission to the db
        source = Source.query.filter(Source.filesystem_id == sid).one()
        submission = Submission(source, os.path.basename(filename))
        db_session.add(submission)
        db_session.commit()

    return filenames


def new_codename(client, session):
    """Helper function to go through the "generate codename" flow"""
    with client as c:
        rv = c.get('/generate')
        codename = session['codename']
        rv = c.post('/create')
    return codename


def shared_setup():
    """Set up the file system, GPG, and database"""
    create_directories()
    init_gpg()
    init_db()

    # Do tests that should always run on app startup
    crypto_util.do_runtime_tests()

    # Start the Python-RQ worker if it's not already running
    if not os.path.exists(TEST_WORKER_PIDFILE):
        subprocess.Popen(["rqworker", "-P", config.SECUREDROP_ROOT,
                                      "--pid", TEST_WORKER_PIDFILE])


def shared_teardown():
    clean_root()


def logout(test_client):
    # See http://flask.pocoo.org/docs/testing/#accessing-and-modifying-sessions
    # This is necessary because SecureDrop doesn't have a logout button, so a
    # user is logged in until they close the browser, which clears the session.
    # For testing, this function simulates closing the browser at places
    # where a source is likely to do so (for instance, between submitting a
    # document and checking for a journalist reply).
    with test_client.session_transaction() as sess:
        sess.clear()
