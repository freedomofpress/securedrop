# -*- coding: utf-8 -*-
import os
import bcrypt
import subprocess
import threading
from Crypto.Random import random
import random as badrandom
import gnupg
import config
import store
from base64 import b32encode
import re

# to fix gpg error #78 on production
os.environ['USERNAME'] = 'www-data'

GPG_KEY_TYPE = "RSA"
if os.environ.get('SECUREDROP_ENV') == 'test':
    # Optiimize crypto to speed up tests (at the expense of security - DO NOT
    # use these settings in production)
    GPG_KEY_LENGTH = "1024"
    BCRYPT_ID_SALT = bcrypt.gensalt(log_rounds=0)
    BCRYPT_GPG_SALT = bcrypt.gensalt(log_rounds=0)
else:
    GPG_KEY_LENGTH = "4096"
    BCRYPT_ID_SALT = config.BCRYPT_ID_SALT
    BCRYPT_GPG_SALT = config.BCRYPT_GPG_SALT

DEFAULT_WORDS_IN_RANDOM_ID = 8


class CryptoException(Exception):
    pass


def clean(s, also=''):
    """
    >>> clean("Hello, world!")
    Traceback (most recent call last):
      ...
    CryptoException: invalid input
    >>> clean("Helloworld")
    'Helloworld'
    """
    # safe characters for every possible word in the wordlist
    # includes capital letters because bcrypt hashes are base32-encoded with
    # capital letters
    ok = '!#%$&)(+*-1032547698;:=?@acbedgfihkjmlonqpsrutwvyxzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for c in s:
        if c not in ok and c not in also:
            raise CryptoException("invalid input: %s" % s)
    return s

words = file(config.WORD_LIST).read().split('\n')
nouns = file('dictionaries/nouns.txt').read().split('\n')
adjectives = file('dictionaries/adjectives.txt').read().split('\n')


def genrandomid(words_in_random_id=DEFAULT_WORDS_IN_RANDOM_ID):
    return ' '.join(random.choice(words) for x in range(words_in_random_id))


def displayid(n):
    badrandom_value = badrandom.WichmannHill()
    badrandom_value.seed(n)
    return badrandom_value.choice(adjectives) + " " + badrandom_value.choice(nouns)



def shash(s, salt=BCRYPT_ID_SALT):
    """
    >>> shash('Hello, world!')
    'EQZGCJBRGISGOTC2NZVWG6LILJBHEV3CINNEWSCLLFTUWZLFHBTS6WLCHFHTOLRSGQXUQLRQHFMXKOKKOQ4WQ6SXGZXDAS3Z'
    """
    return b32encode(bcrypt.hashpw(s, salt))

GPG_BINARY = 'gpg2'
try:
    p = subprocess.Popen([GPG_BINARY, '--version'], stdout=subprocess.PIPE)
except OSError:
    GPG_BINARY = 'gpg'
    p = subprocess.Popen([GPG_BINARY, '--version'], stdout=subprocess.PIPE)

assert p.stdout.readline().split()[
    -1].split('.')[0] == '2', "upgrade GPG to 2.0"
gpg = gnupg.GPG(gpgbinary=GPG_BINARY, gnupghome=config.GPG_KEY_DIR)


def genkeypair(name, secret):
    """
    >>> if not gpg.list_keys(shash('randomid')):
    ...     genkeypair(shash('randomid'), 'randomid').type
    ... else:
    ...     u'P'
    u'P'
    """
    name, secret = clean(name), shash(clean(secret, ' '), salt=BCRYPT_GPG_SALT)
    return gpg.gen_key(gpg.gen_key_input(
        key_type=GPG_KEY_TYPE, key_length=GPG_KEY_LENGTH,
        passphrase=secret,
        name_email=name
    ))


def getkey(name):
    for key in gpg.list_keys():
        for uid in key['uids']:
            if name in uid:
                return key['fingerprint']
    return None


def get_key_by_fingerprint(fingerprint):
    matches = filter(lambda k: k['fingerprint'] == fingerprint, gpg.list_keys())
    return matches[0] if matches else None


def _shquote(s):
    return "\\'".join("'" + p + "'" for p in s.split("'"))


def encrypt(fp, s, output=None):
    r"""
    >>> key = genkeypair('randomid', 'randomid')
    >>> encrypt('randomid', "Goodbye, cruel world!")[:45]
    '-----BEGIN PGP MESSAGE-----\nVersion: GnuPG v2'
    """
    if output:
        store.verify(output)
    fp = fp.replace(' ', '')
    if isinstance(s, unicode):
        s = s.encode('utf8')
    if isinstance(s, str):
        out = gpg.encrypt(s, [fp], output=output, always_trust=True)
    else:
        out = gpg.encrypt_file(s, [fp], output=output, always_trust=True)
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
    secret = shash(secret, salt=BCRYPT_GPG_SALT)
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
