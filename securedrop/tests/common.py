import config
import db
import os
import gnupg
import shutil
import uuid
import crypto_util


def clean_root():
    shutil.rmtree(config.SECUREDROP_DATA_ROOT)


def create_directories():
    # Create directories for the file store and the GPG keyring
    for d in (config.SECUREDROP_DATA_ROOT, config.STORE_DIR, config.GPG_KEY_DIR):
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


def init_db():
    db.init_db()


def setup_test_docs(sid, files):
    filenames = [os.path.join(config.STORE_DIR, sid, file) for file in files]
    for filename in filenames:
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'w') as fp:
            fp.write(str(uuid.uuid4()))
    return filenames


def new_codename(client, session):
    """Helper function to go through the "generate codename" flow"""
    with client as c:
        rv = c.get('/generate')
        codename = session['codename']
        rv = c.post('/create')
    return codename


def shared_setup():
    """Set up the file sysem, GPG, and database"""
    create_directories()
    init_gpg()
    init_db()

    # Do tests that should always run on app startup
    crypto_util.do_runtime_tests()


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
