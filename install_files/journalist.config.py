import os

class BaseConfig(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY='SECRET_KEY_VALUE'

class ProductionConfig(BaseConfig):
    pass

class DevelopmentConfig(BaseConfig):
    DEBUG = True

class TestingConfig(BaseConfig):
    TESTING = True
    # Tests are simpler if CSRF protection is disabled
    WTF_CSRF_ENABLED = False

# data directories - should be on secure media
STORE_DIR='/var/www/securedrop/store'
GPG_KEY_DIR='/var/www/securedrop/keys'
TEMP_DIR='/var/www/securedrop/temp'

# fingerprint of the GPG key to encrypt submissions to
JOURNALIST_KEY='APP_GPG_KEY_FINGERPRINT'

SOURCE_TEMPLATES_DIR='/var/www/securedrop/source_templates'
JOURNALIST_TEMPLATES_DIR='/var/www/securedrop/journalist_templates'
WORD_LIST='/var/www/securedrop/wordlist'
NOUNS='/var/www/securedrop/dictionaries/nouns.txt'
ADJECTIVES='/var/www/securedrop/dictionaries/adjectives.txt'

BCRYPT_SALT='BCRYPT_SALT_VALUE'

DATABASE_ENGINE='mysql'
DATABASE_USERNAME='securedrop'
DATABASE_PASSWORD=''
DATABASE_HOST='localhost'
DATABASE_NAME='securedrop'

# Default to the production configuration
FlaskConfig = ProductionConfig

if os.environ.get('SECUREDROP_ENV') == 'test':
    FlaskConfig = TestingConfig
    TEST_DIR='/tmp/deaddrop_test'
    STORE_DIR=os.path.join(TEST_DIR, 'store')
    GPG_KEY_DIR=os.path.join(TEST_DIR, 'keys')
    # test_journalist_key.pub
    JOURNALIST_KEY='65A1B5FF195B56353CC63DFFCC40EF1228271441'
