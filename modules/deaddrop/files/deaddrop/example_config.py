# data directories - should be on secure media
STORE_DIR='/tmp/deaddrop/store'
GPG_KEY_DIR='/tmp/deaddrop/keys'
JOURNALIST_KEY=''

SOURCE_TEMPLATES_DIR='./source_templates'
JOURNALIST_TEMPLATES_DIR='./journalist_templates'
WORD_LIST='./wordlist'

HMAC_SECRET='c75f391d54717cbfbd89d3a5597dacad0eab42242661512d18d8087a3c842128' # $ date | sha256sum
BCRYPT_SALT='$2a$12$gLZnkcyhZBrWbCZKHKYgKee8g/Yb9O7.24/H.09Yu9Jt9hzW6n0Ky' # bcrypt.gensalt()

# Use different settings for tests
import os
if 'DEADDROPENV' in os.environ and os.environ['DEADDROPENV'] == 'test':
    TEST_DIR='/tmp/deaddrop_test'
    STORE_DIR=os.path.join(TEST_DIR, 'store')
    GPG_KEY_DIR=os.path.join(TEST_DIR, 'keys')
    JOURNALIST_KEY='test@deaddrop.example.com'
