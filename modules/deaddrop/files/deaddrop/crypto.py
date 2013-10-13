# -*- coding: utf-8 -*-
import bcrypt, subprocess, threading
from Crypto.Random import random
import random as badrandom
import gnupg
import config
import store
from base64 import b32encode

GPG_KEY_TYPE = "RSA"
GPG_KEY_LENGTH = "4096"

DEFAULT_WORDS_IN_RANDOM_ID = 8

class CryptoException(Exception): pass

def clean(s, also=''):
    """
    >>> clean("Hello, world!")
    Traceback (most recent call last):
      ...
    CryptoException: invalid input
    >>> clean("Helloworld")
    'Helloworld'
    """
    ok = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    for c in s:
        if c not in ok and c not in also: raise CryptoException("invalid input")
    return s

words = file(config.WORD_LIST).read().split('\n')
def genrandomid(words_in_random_id = DEFAULT_WORDS_IN_RANDOM_ID):
    return ' '.join(random.choice(words) for x in range(words_in_random_id))

def displayid(n, words_in_random_id = DEFAULT_WORDS_IN_RANDOM_ID):
    badrandom_value = badrandom.WichmannHill()
    badrandom_value.seed(n)
    return ' '.join(badrandom_value.choice(words) for x in range(words_in_random_id))

def shash(s):
    """
    >>> shash('Hello, world!')
    '$2a$12$gLZnkcyhZBrWbCZKHKYgKee8g/Yb9O7.24/H.09Yu9Jt9hzW6n0Ky'
    """
    return b32encode(bcrypt.hashpw(s, config.BCRYPT_SALT))

GPG_BINARY = 'gpg2'
try:
    p = subprocess.Popen([GPG_BINARY, '--version'], stdout=subprocess.PIPE)
except OSError:
    GPG_BINARY = 'gpg'
    p = subprocess.Popen([GPG_BINARY, '--version'], stdout=subprocess.PIPE)

assert p.stdout.readline().split()[-1].split('.')[0] == '2', "upgrade GPG to 2.0"
gpg = gnupg.GPG(binary=GPG_BINARY, homedir=config.GPG_KEY_DIR)

def genkeypair(name, secret):
    """
    >>> if not gpg.list_keys(shash('randomid')):
    ...     genkeypair(shash('randomid'), 'randomid').type
    ... else:
    ...     u'P'
    u'P'
    """
    name, secret = clean(name), clean(secret, ' ')
    return gpg.gen_key(gpg.gen_key_input(
      key_type=GPG_KEY_TYPE, key_length=GPG_KEY_LENGTH,
      passphrase=secret,
      name_email="%s@deaddrop.example.com" % name
    ))

def getkey(name):
    for key in gpg.list_keys():
        for uid in key['uids']:
            if ' <%s@' % name in uid: return key['fingerprint']
    return None

def _shquote(s):
    return "\\'".join("'" + p + "'" for p in s.split("'"))
_gpghacklock = threading.Lock()

def encrypt(fingerprint, s, output=None, fn=None):
    r"""
    >>> key = genkeypair('randomid', 'randomid')
    >>> encrypt('randomid', "Goodbye, cruel world!")[:45]
    '-----BEGIN PGP MESSAGE-----\nVersion: GnuPG v2'
    """
    if output:
        store.verify(output)
    fingerprint = fingerprint.replace(' ', '')
    if isinstance(s, unicode):
        s = s.encode('utf8')
    if isinstance(s, str):
        out = gpg.encrypt(s, fingerprint, output=output, always_trust=True)
    else:
        if fn:
            with _gpghacklock:
                print fn
                out = gpg.encrypt(s, fingerprint, output=fn, always_trust=True)
        else:
            out = gpg.encrypt(s, fingerprint, output=fn, always_trust=True)
    if out.ok:
        return out.data
    else:
        raise CryptoException(out.stderr)

def decrypt(name, secret, s):
    """
    >>> key = genkeypair('randomid', 'randomid')
    >>> decrypt('randomid', 'randomid',
    ...   encrypt('randomid', 'Goodbye, cruel world!')
    ... )
    'Goodbye, cruel world!'
    """
    return gpg.decrypt(s, passphrase=secret).data

def secureunlink(fn):
    store.verify(fn)
    return subprocess.check_call(['srm', fn])

# crash if we don't have srm:
try:
    subprocess.check_call(['srm'], stdout=subprocess.PIPE)
except subprocess.CalledProcessError:
    pass

if __name__ == "__main__":
    import doctest
    doctest.testmod()
