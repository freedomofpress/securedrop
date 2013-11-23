import os, stat

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

JOURNALIST_KEY=''

SOURCE_TEMPLATES_DIR='./source_templates'
JOURNALIST_TEMPLATES_DIR='./journalist_templates'
WORD_LIST='./wordlist'

BCRYPT_SALT='' # bcrypt.gensalt()

if os.environ.get('SECUREDROP_ENV') == 'test':
    FlaskConfig=TestingConfig
    SECUREDROP_ROOT='/tmp/securedrop_test'
    JOURNALIST_KEY='65A1B5FF195B56353CC63DFFCC40EF1228271441' # test_journalist_key.pub
else:
    FlaskConfig = ProductionConfig
    # Note: most OS automatically delete /tmp on reboot. If you want your
    # Securedrop to persist over reboots, change this value to a directory that
    # is not in /tmp!
    SECUREDROP_ROOT='/tmp/securedrop'

# data directories - should be on secure media
STORE_DIR=os.path.join(SECUREDROP_ROOT, 'store')
GPG_KEY_DIR=os.path.join(SECUREDROP_ROOT, 'keys')
TEMP_DIR=os.path.join(SECUREDROP_ROOT, 'tmp')

# create the data directories
for d in (SECUREDROP_ROOT, STORE_DIR, GPG_KEY_DIR, TEMP_DIR):
    if not os.path.isdir(d):
        os.mkdir(d)

# restrict permissions to avoid warnings from GPG
def has_perms(path, mode):
    return oct(stat.S_IMODE(os.stat(path).st_mode)) == oct(mode)
safe_perms = 0700
if not has_perms(GPG_KEY_DIR, safe_perms):
    os.chmod(GPG_KEY_DIR, safe_perms)