#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base64 import b32encode
import os
import subprocess

from Crypto.Random import random
import gnupg
from gnupg._util import _is_stream, _make_binary_stream
import scrypt

import config
import store

# to fix gpg error #78 on production
os.environ['USERNAME'] = 'www-data'

GPG_KEY_TYPE = "RSA"
if os.environ.get('SECUREDROP_ENV') == 'test':
    # Optimize crypto to speed up tests (at the expense of security - DO NOT
    # use these settings in production)
    GPG_KEY_LENGTH = 1024
    SCRYPT_PARAMS = dict(N=2**1, r=1, p=1)
else:  # pragma: no cover
    GPG_KEY_LENGTH = 4096
    SCRYPT_PARAMS = config.SCRYPT_PARAMS

SCRYPT_ID_PEPPER = config.SCRYPT_ID_PEPPER
SCRYPT_GPG_PEPPER = config.SCRYPT_GPG_PEPPER

DEFAULT_WORDS_IN_RANDOM_ID = 8


# Make sure these pass before the app can run
# TODO: Add more tests
def do_runtime_tests():
    assert(config.SCRYPT_ID_PEPPER != config.SCRYPT_GPG_PEPPER)
    # crash if we don't have srm:
    try:
        subprocess.check_call(['srm'], stdout=subprocess.PIPE)
    except subprocess.CalledProcessError:
        pass


do_runtime_tests()

gpg = gnupg.GPG(binary='gpg2', homedir=config.GPG_KEY_DIR)

language2words = {}
nouns = open(config.NOUNS).read().rstrip('\n').split('\n')
adjectives = open(config.ADJECTIVES).read().rstrip('\n').split('\n')


class CryptoException(Exception):
    pass


def clean(s, also=''):
    """
    >>> clean("Hello, world!")
    Traceback (most recent call last):
      ...
    CryptoException: invalid input: Hello, world!
    >>> clean("Helloworld")
    'Helloworld'
    """
    # safe characters for every possible word in the wordlist includes capital
    # letters because codename hashes are base32-encoded with capital letters
    ok = (' !#%$&)(+*-1032547698;:=?@acbedgfihkjmlonqpsrutwvyxzABCDEFGHIJ'
          'KLMNOPQRSTUVWXYZ')
    for c in s:
        if c not in ok and c not in also:
            raise CryptoException("invalid input: {0}".format(s))
    # scrypt.hash requires input of type str. Since the wordlist is all ASCII
    # characters, this conversion is not problematic
    return str(s)


def _get_wordlist(locale):
    """" Ensure the wordlist for the desired locale is read and available
    in the words global variable. If there is no wordlist for the
    desired local, fallback to the default english wordlist.

    The localized wordlist are read from wordlists/{locale}.txt but
    for backward compatibility purposes the english wordlist is read
    from the config.WORD_LIST file.

    """

    if locale not in language2words:
        if locale != 'en':
            path = os.path.join(config.SECUREDROP_ROOT,
                                'wordlists',
                                locale + '.txt')
            if os.path.exists(path):
                wordlist_path = path
            else:
                wordlist_path = config.WORD_LIST
        else:
            wordlist_path = config.WORD_LIST

        language2words[locale] = open(
            wordlist_path).read().rstrip('\n').split('\n')

    return language2words[locale]


def genrandomid(words_in_random_id=DEFAULT_WORDS_IN_RANDOM_ID, locale='en'):
    return ' '.join(random.choice(_get_wordlist(locale))
                    for x in range(words_in_random_id))


def display_id():
    return ' '.join([random.choice(adjectives), random.choice(nouns)])


def hash_codename(codename, salt=SCRYPT_ID_PEPPER):
    """Salts and hashes a codename using scrypt.

    :param str codename: A source's codename.
    :param str salt: The salt to mix with the codename when hashing.
    :returns: A base32 encoded string; the salted codename hash.
    """
    return b32encode(scrypt.hash(clean(codename), salt, **SCRYPT_PARAMS))


def genkeypair(name, secret):
    """Generate a GPG key through batch file key generation. A source's
    codename is salted with SCRYPT_GPG_PEPPER and hashed with scrypt to
    provide the passphrase used to encrypt their private key. Their name
    should be their filesystem id.

    >>> if not gpg.list_keys(hash_codename('randomid')):
    ...     genkeypair(hash_codename('randomid'), 'randomid').type
    ... else:
    ...     u'P'
    u'P'

    :param str name: The source's filesystem id (their codename, salted
                     with SCRYPT_ID_PEPPER, and hashed with scrypt).
    :param str secret: The source's codename.
    :returns: a :class:`GenKey <gnupg._parser.GenKey>` object, on which
              the ``__str__()`` method may be called to return the
              generated key's fingeprint.

    """
    name = clean(name)
    secret = hash_codename(secret, salt=SCRYPT_GPG_PEPPER)
    return gpg.gen_key(gpg.gen_key_input(
        key_type=GPG_KEY_TYPE, key_length=GPG_KEY_LENGTH,
        passphrase=secret,
        name_email=name
    ))


def delete_reply_keypair(source_filesystem_id):
    key = getkey(source_filesystem_id)
    # If this source was never flagged for review, they won't have a reply
    # keypair
    if not key:
        return
    # The private key needs to be deleted before the public key can be deleted
    # http://pythonhosted.org/python-gnupg/#deleting-keys
    gpg.delete_keys(key, True)  # private key
    gpg.delete_keys(key)  # public key
    # TODO: srm?


def getkey(name):
    for key in gpg.list_keys():
        for uid in key['uids']:
            if name in uid:
                return key['fingerprint']
    return None


def encrypt(plaintext, fingerprints, output=None):
    # Verify the output path
    if output:
        store.verify(output)

    if not isinstance(fingerprints, (list, tuple)):
        fingerprints = [fingerprints, ]
    # Remove any spaces from provided fingerprints GPG outputs fingerprints
    # with spaces for readability, but requires the spaces to be removed when
    # using fingerprints to specify recipients.
    fingerprints = [fpr.replace(' ', '') for fpr in fingerprints]

    if not _is_stream(plaintext):
        plaintext = _make_binary_stream(plaintext, "utf_8")

    out = gpg.encrypt(plaintext,
                      *fingerprints,
                      output=output,
                      always_trust=True,
                      armor=False)
    if out.ok:
        return out.data
    else:
        raise CryptoException(out.stderr)


def decrypt(secret, ciphertext):
    """
    >>> key = genkeypair('randomid', 'randomid')
    >>> decrypt('randomid',
    ...   encrypt('Goodbye, cruel world!', str(key))
    ... )
    'Goodbye, cruel world!'
    """
    hashed_codename = hash_codename(secret, salt=SCRYPT_GPG_PEPPER)
    return gpg.decrypt(ciphertext, passphrase=hashed_codename).data


if __name__ == "__main__":  # pragma: no cover
    import doctest
    doctest.testmod()
