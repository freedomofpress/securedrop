import os
from base import BaseFlaskConfig

JOURNALIST_KEY='65A1B5FF195B56353CC63DFFCC40EF1228271441' # test_journalist_key.pub
SECUREDROP_ROOT='/tmp/securedrop_test'

class FlaskConfig(BaseFlaskConfig):
    TESTING = True
    # Tests are simpler if CSRF protection is disabled
    WTF_CSRF_ENABLED = False


### Database Configuration

# Default to using a sqlite database file for testing
DATABASE_ENGINE = 'sqlite'
DATABASE_FILE=os.path.join(SECUREDROP_ROOT, 'db_test.sqlite')
