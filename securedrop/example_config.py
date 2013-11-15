import os

class BaseConfig(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = '' # import os; os.urandom(24)

class ProductionConfig(BaseConfig):
    pass

class DevelopmentConfig(BaseConfig):
    DEBUG = True

class TestingConfig(BaseConfig):
    TESTING = True
    # Tests are simpler if CSRF protection is disabled
    WTF_CSRF_ENABLED = False

# data directories - should be on secure media
STORE_DIR='/tmp/deaddrop/store'
GPG_KEY_DIR='/tmp/deaddrop/keys'
TEMP_DIR='/tmp/deaddrop/tmp'

JOURNALIST_KEY=''

SOURCE_TEMPLATES_DIR='./source_templates'
JOURNALIST_TEMPLATES_DIR='./journalist_templates'
WORD_LIST='./wordlist'

BCRYPT_SALT='' # bcrypt.gensalt()

# Default to the production configuration
FlaskConfig = ProductionConfig

if os.environ.get('SECUREDROP_ENV') == 'test':
    FlaskConfig = TestingConfig
    TEST_DIR='/tmp/deaddrop_test'
    STORE_DIR=os.path.join(TEST_DIR, 'store')
    GPG_KEY_DIR=os.path.join(TEST_DIR, 'keys')
    # test_journalist_key.pub
    JOURNALIST_KEY='65A1B5FF195B56353CC63DFFCC40EF1228271441'
