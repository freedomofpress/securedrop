"""This file contains the oldest config.py file available from Securedrop's Git repo, at
https://github.com/freedomofpress/securedrop/blob/5aa8a4432949201893afbac0f506c60d93fa7483
/securedrop/config.py.example

We use it to ensure that we can parse very old config files.
"""
import os


# Default values for production, may be overridden later based on environment
class FlaskConfig(object):
    DEBUG = False
    TESTING = False
    WTF_CSRF_ENABLED = True


# Use different secret keys for the two different applications so their
# sessions can't be confused.
# TODO consider using salts instead: http://pythonhosted.org//itsdangerous/#the-salt
class SourceInterfaceFlaskConfig(FlaskConfig):
    SECRET_KEY = "{{ source_secret_key }}"


class JournalistInterfaceFlaskConfig(FlaskConfig):
    SECRET_KEY = "{{ journalist_secret_key }}"


# These files are in the same directory as config.py. Use absolute paths to
# avoid potential problems with the test runner - otherwise, you have to be in
# this directory when you run the code.
CODE_ROOT = os.path.dirname(os.path.realpath(__file__))

SOURCE_TEMPLATES_DIR = os.path.join(CODE_ROOT, "source_templates")
JOURNALIST_TEMPLATES_DIR = os.path.join(CODE_ROOT, "journalist_templates")
WORD_LIST = os.path.join(CODE_ROOT, "wordlist")
NOUNS = os.path.join(CODE_ROOT, "dictionaries/nouns.txt")
ADJECTIVES = os.path.join(CODE_ROOT, "./dictionaries/adjectives.txt")

JOURNALIST_PIDFILE = "/tmp/journalist.pid"
SOURCE_PIDFILE = "/tmp/source.pid"

# "head -c 32 /dev/urandom | base64" for constructing public ID from source codename
SCRYPT_ID_PEPPER = "{{ scrypt_id_pepper }}"
# "head -c 32 /dev/urandom | base64" for stretching source codename into GPG passphrase
SCRYPT_GPG_PEPPER = "{{ scrypt_gpg_pepper }}"
SCRYPT_PARAMS = dict(N=2**14, r=8, p=1)

# Fingerprint of the public key to use for encrypting submissions
# Defaults to test_journalist_key.pub, which is used for development and testing
JOURNALIST_KEY = "{{ journalist_key }}"

# Directory where SecureDrop stores the database file, GPG keyring, and
# encrypted submissions.
SECUREDROP_ROOT = "{{ securedrop_root }}"

# Modify configuration for alternative environments
env = os.environ.get("SECUREDROP_ENV") or "prod"

if env == "prod":
    pass
elif env == "dev":
    # Enable Flask's debugger for development
    FlaskConfig.DEBUG = False
elif env == "test":
    FlaskConfig.TESTING = True
    # Disable CSRF checks for tests to make writing tests easier
    FlaskConfig.WTF_CSRF_ENABLED = False
    # TODO use a unique temporary directory for each test so we can parallelize them
    SECUREDROP_ROOT = "/tmp/securedrop"

# The following configuration is dependent on SECUREDROP_ROOT

# Directory where encrypted submissions are stored
STORE_DIR = os.path.join(SECUREDROP_ROOT, "store")

# Directory where GPG keyring is stored
GPG_KEY_DIR = os.path.join(SECUREDROP_ROOT, "keys")

# Database configuration
# TODO we currently use sqlite in production since it is sufficient and simple,
# but in the future may want to be able to choose a different database
# depending on the environment
DATABASE_ENGINE = "sqlite"
DATABASE_FILE = os.path.join(SECUREDROP_ROOT, "db.sqlite")
