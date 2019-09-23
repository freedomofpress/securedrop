# -*- coding: utf-8 -*-

from distutils.version import StrictVersion
import pretty_bad_protocol as gnupg
import os
import io
import scrypt
from random import SystemRandom

from base64 import b32encode
from datetime import date
from flask import current_app
from pretty_bad_protocol._util import _is_stream, _make_binary_stream

import rm

import typing
# https://www.python.org/dev/peps/pep-0484/#runtime-or-type-checking
if typing.TYPE_CHECKING:
    # flake8 can not understand type annotation yet.
    # That is why all type annotation relative import
    # statements has to be marked as noqa.
    # http://flake8.pycqa.org/en/latest/user/error-codes.html?highlight=f401stream
    from typing import Dict, List, Text  # noqa: F401


# to fix gpg error #78 on production
os.environ['USERNAME'] = 'www-data'

# SystemRandom sources from the system rand (e.g. urandom, CryptGenRandom, etc)
# It supplies a CSPRNG but with an interface that supports methods like choice
random = SystemRandom()

# safe characters for every possible word in the wordlist includes capital
# letters because codename hashes are base32-encoded with capital letters
DICEWARE_SAFE_CHARS = (' !#%$&)(+*-1032547698;:=?@acbedgfihkjmlonqpsrutwvyxzA'
                       'BCDEFGHIJKLMNOPQRSTUVWXYZ')


def monkey_patch_delete_handle_status(self, key, value):
    """
    Parse a status code from the attached GnuPG process.
    :raises: :exc:`~exceptions.ValueError` if the status message is unknown.
    """
    if key in ("DELETE_PROBLEM", "KEY_CONSIDERED"):
        self.status = self.problem_reason.get(value, "Unknown error: %r" % value)
    elif key in ("PINENTRY_LAUNCHED"):
        self.status = key.replace("_", " ").lower()
    else:
        raise ValueError("Unknown status message: %r" % key)


# Monkey patching to resolve https://github.com/freedomofpress/securedrop/issues/4294
gnupg._parsers.DeleteResult._handle_status = monkey_patch_delete_handle_status


class CryptoException(Exception):
    pass


class CryptoUtil:

    GPG_KEY_TYPE = "RSA"
    DEFAULT_WORDS_IN_RANDOM_ID = 8

    # All reply keypairs will be "created" on the same day SecureDrop (then
    # Strongbox) was publicly released for the first time.
    # https://www.newyorker.com/news/news-desk/strongbox-and-aaron-swartz
    DEFAULT_KEY_CREATION_DATE = date(2013, 5, 14)

    # '0' is the magic value that tells GPG's batch key generation not
    # to set an expiration date.
    DEFAULT_KEY_EXPIRATION_DATE = '0'

    def __init__(self,
                 scrypt_params,
                 scrypt_id_pepper,
                 scrypt_gpg_pepper,
                 securedrop_root,
                 word_list,
                 nouns_file,
                 adjectives_file,
                 gpg_key_dir):
        self.__securedrop_root = securedrop_root
        self.__word_list = word_list

        if os.environ.get('SECUREDROP_ENV') == 'test':
            # Optimize crypto to speed up tests (at the expense of security
            # DO NOT use these settings in production)
            self.__gpg_key_length = 1024
            self.scrypt_params = dict(N=2**1, r=1, p=1)
        else:  # pragma: no cover
            self.__gpg_key_length = 4096
            self.scrypt_params = scrypt_params

        self.scrypt_id_pepper = scrypt_id_pepper
        self.scrypt_gpg_pepper = scrypt_gpg_pepper

        self.do_runtime_tests()

        # --pinentry-mode, required for SecureDrop on gpg 2.1.x+, was
        # added in gpg 2.1.
        self.gpg_key_dir = gpg_key_dir
        gpg_binary = gnupg.GPG(binary='gpg2', homedir=self.gpg_key_dir)
        if StrictVersion(gpg_binary.binary_version) >= StrictVersion('2.1'):
            self.gpg = gnupg.GPG(binary='gpg2',
                                 homedir=gpg_key_dir,
                                 options=['--pinentry-mode loopback'])
        else:
            self.gpg = gpg_binary

        # map code for a given language to a localized wordlist
        self.__language2words = {}  # type: Dict[Text, List[str]]

        with io.open(nouns_file) as f:
            self.nouns = f.read().splitlines()

        with io.open(adjectives_file) as f:
            self.adjectives = f.read().splitlines()

    # Make sure these pass before the app can run
    def do_runtime_tests(self):
        if self.scrypt_id_pepper == self.scrypt_gpg_pepper:
            raise AssertionError('scrypt_id_pepper == scrypt_gpg_pepper')
        # crash if we don't have a way to securely remove files
        if not rm.check_secure_delete_capability():
            raise AssertionError("Secure file deletion is not possible.")

    def get_wordlist(self, locale):
        # type: (Text) -> List[str]
        """" Ensure the wordlist for the desired locale is read and available
        in the words global variable. If there is no wordlist for the
        desired local, fallback to the default english wordlist.

        The localized wordlist are read from wordlists/{locale}.txt but
        for backward compatibility purposes the english wordlist is read
        from the config.WORD_LIST file.
        """

        if locale not in self.__language2words:
            if locale != 'en':
                path = os.path.join(self.__securedrop_root,
                                    'wordlists',
                                    locale + '.txt')
                if os.path.exists(path):
                    wordlist_path = path
                else:
                    wordlist_path = self.__word_list
            else:
                wordlist_path = self.__word_list

            with io.open(wordlist_path) as f:
                content = f.read().splitlines()
                self.__language2words[locale] = content

        return self.__language2words[locale]

    def genrandomid(self,
                    words_in_random_id=None,
                    locale='en'):
        if words_in_random_id is None:
            words_in_random_id = self.DEFAULT_WORDS_IN_RANDOM_ID
        return ' '.join(random.choice(self.get_wordlist(locale))
                        for x in range(words_in_random_id))

    def display_id(self):
        return ' '.join([random.choice(self.adjectives),
                         random.choice(self.nouns)])

    def hash_codename(self, codename, salt=None):
        """Salts and hashes a codename using scrypt.

        :param str codename: A source's codename.
        :param str salt: The salt to mix with the codename when hashing.
        :returns: A base32 encoded string; the salted codename hash.
        """
        if salt is None:
            salt = self.scrypt_id_pepper
        return b32encode(scrypt.hash(clean(codename),
                         salt,
                         **self.scrypt_params)).decode('utf-8')

    def genkeypair(self, name, secret):
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
        secret = self.hash_codename(secret, salt=self.scrypt_gpg_pepper)
        genkey_obj = self.gpg.gen_key(self.gpg.gen_key_input(
            key_type=self.GPG_KEY_TYPE,
            key_length=self.__gpg_key_length,
            passphrase=secret,
            name_email=name,
            creation_date=self.DEFAULT_KEY_CREATION_DATE.isoformat(),
            expire_date=self.DEFAULT_KEY_EXPIRATION_DATE
        ))
        return genkey_obj

    def delete_reply_keypair(self, source_filesystem_id):
        key = self.getkey(source_filesystem_id)
        # If this source was never flagged for review, they won't have a reply
        # keypair
        if not key:
            return

        # Always delete keys without invoking pinentry-mode = loopback
        # see: https://lists.gnupg.org/pipermail/gnupg-users/2016-May/055965.html
        temp_gpg = gnupg.GPG(binary='gpg2', homedir=self.gpg_key_dir)
        # The subkeys keyword argument deletes both secret and public keys.
        temp_gpg.delete_keys(key, secret=True, subkeys=True)

    def getkey(self, name):
        for key in self.gpg.list_keys():
            for uid in key['uids']:
                if name in uid:
                    return key['fingerprint']
        return None

    def export_pubkey(self, name):
        fingerprint = self.getkey(name)
        if fingerprint:
            return self.gpg.export_keys(fingerprint)
        else:
            return None

    def encrypt(self, plaintext, fingerprints, output=None):
        # Verify the output path
        if output:
            current_app.storage.verify(output)

        if not isinstance(fingerprints, (list, tuple)):
            fingerprints = [fingerprints, ]
        # Remove any spaces from provided fingerprints GPG outputs fingerprints
        # with spaces for readability, but requires the spaces to be removed
        # when using fingerprints to specify recipients.
        fingerprints = [fpr.replace(' ', '') for fpr in fingerprints]

        if not _is_stream(plaintext):
            plaintext = _make_binary_stream(plaintext, "utf_8")

        out = self.gpg.encrypt(plaintext,
                               *fingerprints,
                               output=output,
                               always_trust=True,
                               armor=False)
        if out.ok:
            return out.data
        else:
            raise CryptoException(out.stderr)

    def decrypt(self, secret, ciphertext):
        """
        >>> crypto = current_app.crypto_util
        >>> key = crypto.genkeypair('randomid', 'randomid')
        >>> message = u'Buenos días, mundo hermoso!'
        >>> ciphertext = crypto.encrypt(message, str(key))
        >>> crypto.decrypt('randomid', ciphertext) == message.encode('utf-8')
        True
        """
        hashed_codename = self.hash_codename(secret,
                                             salt=self.scrypt_gpg_pepper)
        data = self.gpg.decrypt(ciphertext, passphrase=hashed_codename).data

        return data.decode('utf-8')


def clean(s, also=''):
    """
    >>> clean("[]")
    Traceback (most recent call last):
      ...
    CryptoException: invalid input: []
    >>> clean("Helloworld")
    'Helloworld'
    """
    for c in s:
        if c not in DICEWARE_SAFE_CHARS and c not in also:
            raise CryptoException("invalid input: {0}".format(s))
    # scrypt.hash requires input of type str. Since the wordlist is all ASCII
    # characters, this conversion is not problematic
    return str(s)
