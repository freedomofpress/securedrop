# -*- coding: utf-8 -*-
import os
import subprocess
from base64 import b32encode

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
else:
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

# HACK: use_agent=True is used to avoid logging noise.
#
# --use-agent is a dummy option in gpg2, which is the only version of
# gpg used by SecureDrop. If use_agent=False, gpg2 prints a warning
# message every time it runs because the option is deprecated and has
# no effect. This message cannot be silenced even if you change the
# --debug-level (controlled via the verbose= keyword argument to the
# gnupg.GPG constructor), and creates a lot of logging noise.
#
# The best solution here would be to avoid passing either --use-agent
# or --no-use-agent to gpg2, and I have filed an issue upstream to
# address this: https://github.com/isislovecruft/python-gnupg/issues/96
gpg = gnupg.GPG(binary='gpg2', homedir=config.GPG_KEY_DIR, use_agent=True)

words = file(config.WORD_LIST).read().split('\n')
nouns = file(config.NOUNS).read().split('\n')
adjectives = file(config.ADJECTIVES).read().split('\n')


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
    # safe characters for every possible word in the wordlist includes capital
    # letters because codename hashes are base32-encoded with capital letters
    ok = ' !#%$&)(+*-1032547698;:=?@acbedgfihkjmlonqpsrutwvyxzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for c in s:
        if c not in ok and c not in also:
            raise CryptoException("invalid input: {0}".format(s))
    # scrypt.hash requires input of type str. Since the wordlist is all ASCII
    # characters, this conversion is not problematic
    return str(s)


def genrandomid(words_in_random_id=DEFAULT_WORDS_IN_RANDOM_ID):
    return ' '.join(random.choice(words) for x in range(words_in_random_id))


def display_id():
    return ' '.join([random.choice(adjectives), random.choice(nouns)])


def hash_codename(codename, salt=SCRYPT_ID_PEPPER):
    """
    >>> hash_codename('Hello, world!')
    'EQZGCJBRGISGOTC2NZVWG6LILJBHEV3CINNEWSCLLFTUWZLFHBTS6WLCHFHTOLRSGQXUQLRQHFMXKOKKOQ4WQ6SXGZXDAS3Z'
    """
    return b32encode(scrypt.hash(clean(codename), salt, **SCRYPT_PARAMS))


def genkeypair(name, secret):
    """
    >>> if not gpg.list_keys(hash_codename('randomid')):
    ...     genkeypair(hash_codename('randomid'), 'randomid').type
    ... else:
    ...     u'P'
    u'P'
    """
    name = clean(name)
    secret = hash_codename(secret, salt=SCRYPT_GPG_PEPPER)
    return gpg.gen_key(gpg.gen_key_input(
        key_type=GPG_KEY_TYPE, key_length=GPG_KEY_LENGTH,
        passphrase=secret,
        name_email=name
    ))


def delete_reply_keypair(source_id):
    key = getkey(source_id)
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


def get_key_by_fingerprint(fingerprint):
    matches = filter(
        lambda k: k['fingerprint'] == fingerprint,
        gpg.list_keys())
    return matches[0] if matches else None


def encrypt(plaintext, fingerprints, output=None):
    # Verify the output path
    if output:
        store.verify(output)

    # Remove any spaces from provided fingerprints
    # GPG outputs fingerprints with spaces for readability, but requires the
    # spaces to be removed when using fingerprints to specify recipients.
    if not isinstance(fingerprints, (list, tuple)):
        fingerprints = [fingerprints, ]
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
    >>> decrypt('randomid', 'randomid',
    ...   encrypt('randomid', 'Goodbye, cruel world!')
    ... )
    'Goodbye, cruel world!'
    """
    hashed_codename = hash_codename(secret, salt=SCRYPT_GPG_PEPPER)
    return gpg.decrypt(ciphertext, passphrase=hashed_codename).data


class AuthenticationError(Exception): pass


class AES_then_HMAC:
    """Implements an encrypt-then-MAC scheme using AES-CTR-128 and
    HMAC-SHA224 for securing client-side session. Since each time a
    client re-authenticates new encryption and authentication keys are
    generated for one-time use to secure that session, we need not worry
    about re-using the initialization vector.
    """

    # Encryption parameters
    enc_key_size = 128 // 8
    mode = AES.MODE_CTR
    iv = 128

    # Authentication parameters
    digestmod = hashlib.sha224
    digest_size = digestmod().digest_size

    @classmethod
    def gen_keys_string(cls):
        """Generate keys for encryption and authentication.

        :rtype: str
        :returns: A base64-encoded string containing an authentication
                  key appended to an encryption key in the class
                  parameters.
        """
        keys = os.urandom(cls.enc_key_size + cls.digest_size)
        return key.encode("base64").replace("\n", "")

    @classmethod
    def extract_keys(cls, keys_string):
        """Pull the encryption and authentication keys out of a
        keystring.
        
        :param str keys_string: Generated by
                                :meth:`AES_then_HMAC.gen_keys_string`.

        :rtype: str, str
        :returns: The raw byte strings corresponding to the encryption
                  and authentication keys, respectively.
        """
        keys = keys_string.decode("base64")
        assert len(keys) == cls.enc_key_size + cls.digest_size, "invalid keys"
        enc_key, auth_key = key[:-cls.digest_size], key[-cls.digest_size:]
        return enc_key, auth_key

    @classmethod
    def encrypt_then_mac(cls, keys_string, plaintext):
        """Encrypt a message with AES-CTR, then sign the resulting
        ciphertext with with HMAC-SHA224.

        :param str keys_string: Generated by
                                :meth:AES_then_HMAC.gen_keys_string.

        :param str plaintext: The plaintext message to be encrypted.

        :rtype: str
        :returns: The ciphertext with its MAC appended.
        """
        enc_key, auth_key = cls.extract_keys(keys_string)
        ctr = Counter.new(cls.iv)
        ciphertext = AES.new(aes_key, cls.mode, counter=ctr).encrypt(plaintext)
        mac = hmac.new(hmac_key, ciphertext, cls.digestmod).digest()
        return ciphertext + mac

    @classmethod
    def authenticate_then_decrypt(cls, key_string, data):
        """Authenticate the MAC on a ciphertext, and then decrypt it.

        :param str keys_string: Generated by
                                :meth:`AES_then_HMAC.gen_keys_string`.

        :param str data: Generated by 
                         :meth:`AES_then_HMAC.encrypt_then_mac`.

        :raises: A :exc:`AuthenticationError` when the MAC cannot be 
                 authenticated.

        :rtype: str
        :returns: The original plaintext message passed to 
                  :meth:AES_then_HMAC.encrypt_then_mac.
        """
        enc_key, auth_key = cls.extract_keys(keys_string)
        ciphertext, mac = data[:-cls.digest_size], data[-cls.digest_size:]
        if hmac.new(hmac_key, ciphertext, cls.digestmod).digest() != mac:
            raise AuthenticationError("Message authentication failed!")
        ctr = Counter.new(cls.iv)
        return AES.new(aes_key, cls.mode, counter=ctr).decrypt(ciphertext)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
