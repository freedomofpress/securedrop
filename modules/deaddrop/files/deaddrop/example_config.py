# data directories - should be on secure media
STORE_DIR='/tmp/deaddrop/store'
GPG_KEY_DIR='/tmp/deaddrop/keys'
TEMP_DIR='/tmp/deaddrop/tmp'

# fingerprint of the GPG key to encrypt submissions to
JOURNALIST_KEY=''

SOURCE_TEMPLATES_DIR='./source_templates'
JOURNALIST_TEMPLATES_DIR='./journalist_templates'
WORD_LIST='./wordlist'

BCRYPT_SALT='$2a$12$gLZnkcyhZBrWbCZKHKYgKee8g/Yb9O7.24/H.09Yu9Jt9hzW6n0Ky' # bcrypt.gensalt()
SECRET_KEY='\xa1\x93\xedr\xb6\xa4\x93\x01fG\x8d\x13\x08\xa8\xb3_S\x06\xa1\xbd\xd9\x1b!\xc5' # import os; os.urandom(24)

# Use different settings for tests
import os
if 'DEADDROPENV' in os.environ and os.environ['DEADDROPENV'] == 'test':
    TEST_DIR='/tmp/deaddrop_test'
    STORE_DIR=os.path.join(TEST_DIR, 'store')
    GPG_KEY_DIR=os.path.join(TEST_DIR, 'keys')
    JOURNALIST_KEY='65A1B5FF195B56353CC63DFFCC40EF1228271441'
