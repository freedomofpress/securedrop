# -*- coding: utf-8 -*-
import io
import os
import pytest
import re

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import crypto_util
import models

from crypto_util import CryptoUtil, CryptoException
from db import db


def test_word_list_does_not_contain_empty_strings(journalist_app):
    assert '' not in journalist_app.crypto_util.get_wordlist('en')
    assert '' not in journalist_app.crypto_util.nouns
    assert '' not in journalist_app.crypto_util.adjectives


def test_clean():
    ok = (' !#%$&)(+*-1032547698;:=?@acbedgfihkjmlonqpsrutwvyxzABCDEFGHIJ'
          'KLMNOPQRSTUVWXYZ')
    invalids = ['foo bar`', 'bar baz~']

    assert crypto_util.clean(ok) == ok

    for invalid in invalids:
        with pytest.raises(CryptoException) as err:
            crypto_util.clean(invalid)
        assert 'invalid input: {}'.format(invalid) in str(err)


def test_encrypt_success(source_app, config, test_source):
    message = 'test'

    with source_app.app_context():
        ciphertext = source_app.crypto_util.encrypt(
            message,
            [source_app.crypto_util.getkey(test_source['filesystem_id']),
             config.JOURNALIST_KEY],
            source_app.storage.path(test_source['filesystem_id'],
                                    'somefile.gpg'))

        assert isinstance(ciphertext, str)
        assert ciphertext != message
        assert len(ciphertext) > 0


def test_encrypt_failure(source_app, test_source):
    with source_app.app_context():
        with pytest.raises(CryptoException) as err:
            source_app.crypto_util.encrypt(
                str(os.urandom(1)),
                [],
                source_app.storage.path(test_source['filesystem_id'],
                                        'other.gpg'))
        assert 'no terminal at all requested' in str(err)


def test_encrypt_without_output(source_app, config, test_source):
    """We simply do not specify the option output keyword argument
    to crypto_util.encrypt() here in order to confirm encryption
    works when it defaults to `None`.
    """
    message = 'test'
    with source_app.app_context():
        ciphertext = source_app.crypto_util.encrypt(
            message,
            [source_app.crypto_util.getkey(test_source['filesystem_id']),
             config.JOURNALIST_KEY])
        plaintext = source_app.crypto_util.decrypt(
            test_source['codename'],
            ciphertext)

    assert plaintext == message


def test_encrypt_binary_stream(source_app, config, test_source):
    """Generally, we pass unicode strings (the type form data is
    returned as) as plaintext to crypto_util.encrypt(). These have
    to be converted to "binary stream" types (such as `file`) before
    we can actually call gnupg.GPG.encrypt() on them. This is done
    in crypto_util.encrypt() with an `if` branch that uses
    `gnupg._util._is_stream(plaintext)` as the predicate, and calls
    `gnupg._util._make_binary_stream(plaintext)` if necessary. This
    test ensures our encrypt function works even if we provide
    inputs such that this `if` branch is skipped (i.e., the object
    passed for `plaintext` is one such that
    `gnupg._util._is_stream(plaintext)` returns `True`).
    """
    with source_app.app_context():
        with io.open(os.path.realpath(__file__)) as fh:
            ciphertext = source_app.crypto_util.encrypt(
                fh,
                [source_app.crypto_util.getkey(test_source['filesystem_id']),
                 config.JOURNALIST_KEY],
                source_app.storage.path(test_source['filesystem_id'],
                                        'somefile.gpg'))
        plaintext = source_app.crypto_util.decrypt(test_source['codename'],
                                                   ciphertext)

    with io.open(os.path.realpath(__file__)) as fh:
        assert fh.read() == plaintext


def test_encrypt_fingerprints_not_a_list_or_tuple(source_app, test_source):
    """If passed a single fingerprint as a string, encrypt should
    correctly place that string in a list, and encryption/
    decryption should work as intended."""
    message = 'test'

    with source_app.app_context():
        ciphertext = source_app.crypto_util.encrypt(
            message,
            source_app.crypto_util.getkey(test_source['filesystem_id']),
            source_app.storage.path(test_source['filesystem_id'],
                                    'somefile.gpg'))
        plaintext = source_app.crypto_util.decrypt(test_source['codename'],
                                                   ciphertext)

    assert plaintext == message


def test_basic_encrypt_then_decrypt_multiple_recipients(source_app,
                                                        config,
                                                        test_source):
    message = 'test'

    with source_app.app_context():
        ciphertext = source_app.crypto_util.encrypt(
            message,
            [source_app.crypto_util.getkey(test_source['filesystem_id']),
             config.JOURNALIST_KEY],
            source_app.storage.path(test_source['filesystem_id'],
                                    'somefile.gpg'))
        plaintext = source_app.crypto_util.decrypt(test_source['codename'],
                                                   ciphertext)

        assert plaintext == message

        # Since there's no way to specify which key to use for
        # decryption to python-gnupg, we delete the `source`'s key and
        # ensure we can decrypt with the `config.JOURNALIST_KEY`.
        source_app.crypto_util.delete_reply_keypair(
            test_source['filesystem_id'])
        plaintext = source_app.crypto_util.gpg.decrypt(ciphertext).data

        assert plaintext == message


def verify_genrandomid(app, locale):
    id = app.crypto_util.genrandomid(locale=locale)
    id_words = id.split()

    assert crypto_util.clean(id) == id
    assert len(id_words) == CryptoUtil.DEFAULT_WORDS_IN_RANDOM_ID

    for word in id_words:
        assert word in app.crypto_util.get_wordlist(locale)


def test_genrandomid_default_locale_is_en(source_app):
    verify_genrandomid(source_app, 'en')


def test_get_wordlist(source_app, config):
    locales = []
    wordlists_path = os.path.join(config.SECUREDROP_ROOT, 'wordlists')
    for f in os.listdir(wordlists_path):
        if f.endswith('.txt') and f != 'en.txt':
            locales.append(f.split('.')[0])

    with source_app.app_context():
        list_en = source_app.crypto_util.get_wordlist('en')
        for locale in locales:
            assert source_app.crypto_util.get_wordlist(locale) != list_en
            verify_genrandomid(source_app, locale)
            assert source_app.crypto_util.get_wordlist('unknown') == list_en


def test_hash_codename(source_app):
    codename = source_app.crypto_util.genrandomid()
    hashed_codename = source_app.crypto_util.hash_codename(codename)

    assert re.compile('^[2-7A-Z]{103}=$').match(hashed_codename)


def test_display_id(source_app):
    id = source_app.crypto_util.display_id()
    id_words = id.split()

    assert len(id_words) == 2
    assert id_words[0] in source_app.crypto_util.adjectives
    assert id_words[1] in source_app.crypto_util.nouns


def test_genkeypair(source_app):
    with source_app.app_context():
        codename = source_app.crypto_util.genrandomid()
        filesystem_id = source_app.crypto_util.hash_codename(codename)
        journalist_filename = source_app.crypto_util.display_id()
        source = models.Source(filesystem_id, journalist_filename)
        db.session.add(source)
        db.session.commit()
        source_app.crypto_util.genkeypair(source.filesystem_id, codename)

        assert source_app.crypto_util.getkey(filesystem_id) is not None


def test_delete_reply_keypair(source_app, test_source):
    fid = test_source['filesystem_id']
    source_app.crypto_util.delete_reply_keypair(fid)
    assert source_app.crypto_util.getkey(fid) is None


def test_delete_reply_keypair_no_key(source_app):
    """No exceptions should be raised when provided a filesystem id that
    does not exist.
    """
    source_app.crypto_util.delete_reply_keypair('Reality Winner')


def test_getkey(source_app, test_source):
    assert (source_app.crypto_util.getkey(test_source['filesystem_id'])
            is not None)
