import os, stat

### Flask Configurations

class BaseConfig(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = '' # import os; os.urandom(32)

class ProductionConfig(BaseConfig):
    pass

class DevelopmentConfig(BaseConfig):
    DEBUG = True

class TestingConfig(BaseConfig):
    TESTING = True
    # Tests are simpler if CSRF protection is disabled
    WTF_CSRF_ENABLED = False

### Application Configuration

SOURCE_TEMPLATES_DIR = './source_templates'
JOURNALIST_TEMPLATES_DIR = './journalist_templates'
WORD_LIST = './wordlist'

JOURNALIST_KEY='' # fingerprint of the public key for encrypting submissions
BCRYPT_SALT=''    # bcrypt.gensalt()

if os.environ.get('SECUREDROP_ENV') == 'test':
    FlaskConfig=TestingConfig
    SECUREDROP_ROOT='/tmp/securedrop_test'
    JOURNALIST_KEY='65A1B5FF195B56353CC63DFFCC40EF1228271441' # test_journalist_key.pub
else:
    FlaskConfig = ProductionConfig
    SECUREDROP_ROOT=os.path.abspath('.securedrop')

# data directories - should be on secure media
STORE_DIR=os.path.join(SECUREDROP_ROOT, 'store')
GPG_KEY_DIR=os.path.join(SECUREDROP_ROOT, 'keys')

# create the data directories
for d in (SECUREDROP_ROOT, STORE_DIR, GPG_KEY_DIR):
    if not os.path.isdir(d):
        os.mkdir(d)

# restrict permissions to avoid warnings from GPG
def has_perms(path, mode):
    return oct(stat.S_IMODE(os.stat(path).st_mode)) == oct(mode)
safe_perms = 0700
if not has_perms(GPG_KEY_DIR, safe_perms):
    os.chmod(GPG_KEY_DIR, safe_perms)

### Database Configuration

# Default to using a sqlite database file for development
DATABASE_ENGINE = 'sqlite'
DATABASE_FILE=os.path.join(SECUREDROP_ROOT, 'db.sqlite')

# Uncomment to use mysql (or any other databaes backend supported by
# SQLAlchemy). Make sure you have the necessary dependencies installed, and run
# `python -c "import db; db.create_tables()"` to initialize the database

# DATABASE_ENGINE = 'mysql'
# DATABASE_HOST = 'localhost'
# DATABASE_NAME = 'securedrop'
# DATABASE_USERNAME = 'securedrop'
# DATABASE_PASSWORD = '3XKiqH+asPjh2il5VPqHVHBBtPWpNvGY4HfWfQ+CCGY='
