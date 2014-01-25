import os, stat

### Application Configuration

SOURCE_TEMPLATES_DIR = './source_templates'
JOURNALIST_TEMPLATES_DIR = './journalist_templates'
WORD_LIST = './wordlist'
NOUNS='./dictionaries/nouns.txt'
ADJECTIVES='./dictionaries/adjectives.txt'

SCRYPT_ID_PEPPER='$2a$12$gLZnkcyhZBrWbCZKHKYgKee8g/Yb9O7.24/H.09Yu9Jt9hzW6n0Ky'    # os.urandom(32); for constructing public ID from source codename
SCRYPT_GPG_PEPPER='$2a$12$kZkkpMNrVnCaGvMaLF2/B.'   # os.urandom(32); for stretching source codename into GPG passphrase
SCRYPT_PARAMS = dict(N=2**14, r=8, p=1)


### Theming Options

# If you want a custom image at the top, copy your png or jpg to static/i and
# update this to its filename (e.g. "logo.jpg") .
CUSTOM_HEADER_IMAGE = None


### Flask base configuration
class BaseFlaskConfig(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = '\xa1\x93\xedr\xb6\xa4\x93\x01fG\x8d\x13\x08\xa8\xb3_S\x06\xa1\xbd\xd9\x1b!\xc5' # import os; os.urandom(32)


### Import configuration from the current environment
env = os.environ.get('SECUREDROP_ENV')

# default env is 'development'
env = env or 'development'

if env == 'test':
  from test import *
if env == 'development':
  from development import *
if env == 'production':
  from production import *

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
