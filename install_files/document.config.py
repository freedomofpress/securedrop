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

# fingerprint of the GPG key to encrypt submissions to
JOURNALIST_KEY='APP_GPG_KEY_FINGERPRINT'

SOURCE_TEMPLATES_DIR='/var/www/securedrop/source_templates'
JOURNALIST_TEMPLATES_DIR='/var/www/securedrop/journalist_templates'
WORD_LIST='/var/www/securedrop/wordlist'
NOUNS='/var/www/securedrop/dictionaries/nouns.txt'
ADJECTIVES='/var/www/securedrop/dictionaries/adjectives.txt'
SCRYPT_ID_PEPPER='SCRYPT_ID_PEPPER_VALUE'
SCRYPT_GPG_PEPPER='SCRYPT_GPG_PEPPER_VALUE'
SCRYPT_PARAMS=dict(N=2**14, r=8, p=1)

# Default to the production configuration
FlaskConfig = ProductionConfig
SECUREDROP_ROOT=os.path.abspath('/var/www/securedrop') 

if os.environ.get('SECUREDROP_ENV') == 'test':
    FlaskConfig = TestingConfig
    TEST_DIR='/tmp/securedrop_test'
    STORE_DIR=os.path.join(TEST_DIR, 'store')
    GPG_KEY_DIR=os.path.join(TEST_DIR, 'keys')
    # test_journalist_key.pub
    JOURNALIST_KEY='65A1B5FF195B56353CC63DFFCC40EF1228271441'

### Logging

# Note that the loggers propagate up to the root logger, which has a default
# logging level of WARNING. This means logged messages with severity < WARNING
# will not appear unless *both* the handler and the logger are set to desired
# level.
# http://docs.python.org/2.7/library/logging.html
#
# Also note that Flask's built-in logger will adjust its level based on the
# DEBUG flag, and will also automatically log to stdout if the flag is set.

import logging

logfile_path = os.path.join(SECUREDROP_ROOT, 'securedrop.log')
file_handler = logging.FileHandler(logfile_path)
# can .setLevel here, but the default of warning is fine

# more handlers here ...
# e.g.
#
# from logging.handlers import SysLogHandler
# syslog_handler = SysLogHandler(address='/dev/log')

handlers = [file_handler]

def register_handlers(logger):
    for handler in handlers:
        logger.addHandler(handler)

# Database Configuration

# Default to using a sqlite database file for development
DATABASE_ENGINE = 'sqlite'
DATABASE_FILE=os.path.join(SECUREDROP_ROOT, 'db.sqlite')

# Uncomment to use mysql (or any other databaes backend supported by
# SQLAlchemy). Make sure you have the necessary dependencies installed, and run
# `python -c "import db; db.create_tables()"` to initialize the database

#DATABASE_ENGINE = 'mysql'
#DATABASE_HOST = 'localhost'
#DATABASE_NAME = 'securedrop'
#DATABASE_USERNAME = 'document_mysql'
#DATABASE_PASSWORD = 'MYSQL_USER_PASS'
