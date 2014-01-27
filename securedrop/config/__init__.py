import os, stat

from flask_defaults import *
from base import *

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

# restrict permissions in the data directories to avoid warnings from GPG
def has_perms(path, mode):
    return oct(stat.S_IMODE(os.stat(path).st_mode)) == oct(mode)
safe_perms = 0700
if not has_perms(GPG_KEY_DIR, safe_perms):
    os.chmod(GPG_KEY_DIR, safe_perms)

### Flask base configuration
class FlaskConfig(object):
    DEBUG = FLASK_DEBUG
    TESTING = FLASK_TESTING
    SECRET_KEY = FLASK_SECRET_KEY
    WTF_CSRF_ENABLED = FLASK_CSRF_ENABLED
