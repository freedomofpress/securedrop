import config
import db
import os
import gnupg
import shutil
import uuid

def clean_root():
    shutil.rmtree(config.SECUREDROP_ROOT)

def create_directories():
    # Create directories for the file store and the GPG keyring
    for d in (config.SECUREDROP_ROOT, config.STORE_DIR, config.GPG_KEY_DIR):
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
