# -*- coding: utf-8 -*-
from datetime import datetime
from hypothesis import given
from hypothesis.strategies import text
import io
import os
import pytest
import re

from flask import url_for, session

from passphrases import PassphraseGenerator
from source_user import create_source_user, SourceUser

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import crypto_util

from crypto_util import CryptoUtil, CryptoException
from db import db


def test_word_list_does_not_contain_empty_strings(journalist_app):
    assert '' not in journalist_app.crypto_util.nouns
    assert '' not in journalist_app.crypto_util.adjectives


def test_encrypt_success(source_app, config, test_source):
    message = 'test'

    with source_app.app_context():
        ciphertext = source_app.crypto_util.encrypt(
            message,
            [source_app.crypto_util.get_fingerprint(test_source['filesystem_id']),
             config.JOURNALIST_KEY],
            source_app.storage.path(test_source['filesystem_id'],
                                    'somefile.gpg'))

        assert isinstance(ciphertext, bytes)
        assert ciphertext.decode('utf-8') != message
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
            [source_app.crypto_util.get_fingerprint(test_source['filesystem_id']),
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
                [source_app.crypto_util.get_fingerprint(test_source['filesystem_id']),
                 config.JOURNALIST_KEY],
                source_app.storage.path(test_source['filesystem_id'],
                                        'somefile.gpg'))
        plaintext = source_app.crypto_util.decrypt(test_source['codename'],
                                                   ciphertext)

    with io.open(os.path.realpath(__file__)) as fh:
        assert fh.read() == plaintext


def test_basic_encrypt_then_decrypt_multiple_recipients(source_app,
                                                        config,
                                                        test_source):
    message = 'test'

    with source_app.app_context():
        ciphertext = source_app.crypto_util.encrypt(
            message,
            [source_app.crypto_util.get_fingerprint(test_source['filesystem_id']),
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
        plaintext = source_app.crypto_util.gpg.decrypt(ciphertext).data.decode('utf-8')

        assert plaintext == message


def test_hash_codename(source_app):
    codename = PassphraseGenerator.get_default().generate_passphrase()
    hashed_codename = source_app.crypto_util.hash_codename(codename)

    assert re.compile('^[2-7A-Z]{103}=$').match(hashed_codename)


def test_display_id(source_app):
    id = source_app.crypto_util.display_id()
    id_words = id.split()

    assert len(id_words) == 2
    assert id_words[0] in source_app.crypto_util.adjectives
    assert id_words[1] in source_app.crypto_util.nouns


def test_display_id_designation_collisions(source_app):
    with source_app.test_client() as app:
        app.get(url_for('main.generate'))
        source_app.crypto_util.adjectives = source_app.crypto_util.adjectives[:1]
        source_app.crypto_util.nouns = source_app.crypto_util.nouns[:1]
        tab_id = next(iter(session['codenames'].keys()))
        app.post(url_for('main.create'), data={'tab_id': tab_id}, follow_redirects=True)

        with pytest.raises(ValueError) as err:
            source_app.crypto_util.display_id()

        assert 'Could not generate unique journalist designation for new source' in str(err)


def test_genkeypair(source_app):
    with source_app.app_context():
        source_user = create_source_user(
            db_session=db.session,
            source_passphrase=PassphraseGenerator.get_default().generate_passphrase(),
            source_app_storage=source_app.storage,
            source_app_crypto_util=source_app.crypto_util,
        )
        source_app.crypto_util.genkeypair(source_user)

        assert source_app.crypto_util.get_fingerprint(source_user.filesystem_id) is not None


def parse_gpg_date_string(date_string):
    """Parse a date string returned from `gpg --with-colons --list-keys` into a
    datetime.

    The format of the date strings is complicated; see gnupg doc/DETAILS for a
    full explanation.

    Key details:
    - The creation date of the key is given in UTC.
    - the date is usually printed in seconds since epoch, however, we are
    migrating to an ISO 8601 format (e.g. "19660205T091500"). A simple
    way to detect the new format is to scan for the 'T'.
    """
    if 'T' in date_string:
        dt = datetime.strptime(date_string, "%Y%m%dT%H%M%S")
    else:
        dt = datetime.utcfromtimestamp(int(date_string))
    return dt


def test_reply_keypair_creation_and_expiration_dates(source_app):
    with source_app.app_context():
        source_user = create_source_user(
            db_session=db.session,
            source_passphrase=PassphraseGenerator.get_default().generate_passphrase(),
            source_app_storage=source_app.storage,
            source_app_crypto_util=source_app.crypto_util,
        )
        source_app.crypto_util.genkeypair(source_user)

        # crypto_util.get_fingerprint only returns the fingerprint of the key. We need
        # the full output of gpg.list_keys() to check the creation and
        # expire dates.
        #
        # TODO: it might be generally useful to refactor crypto_util.get_fingerprint so
        # it always returns the entire key dictionary instead of just the
        # fingerprint (which is always easily extracted from the entire key
        # dictionary).
        new_key_fingerprint = source_app.crypto_util.get_fingerprint(source_user.filesystem_id)
        new_key = [key for key in source_app.crypto_util.gpg.list_keys()
                   if new_key_fingerprint == key['fingerprint']][0]

        # All keys should share the same creation date to avoid leaking
        # information about when sources first created accounts.
        creation_date = parse_gpg_date_string(new_key['date'])
        assert (creation_date.date() ==
                CryptoUtil.DEFAULT_KEY_CREATION_DATE)

        # Reply keypairs should not expire
        expire_date = new_key['expires']
        assert expire_date == ''


def test_delete_reply_keypair(source_app, test_source):
    fid = test_source['filesystem_id']
    source_app.crypto_util.delete_reply_keypair(fid)
    assert source_app.crypto_util.get_fingerprint(fid) is None


def test_delete_reply_keypair_pinentry_status_is_handled(source_app, test_source,
                                                         mocker, capsys):
    """
    Regression test for https://github.com/freedomofpress/securedrop/issues/4294
    """
    fid = test_source['filesystem_id']

    # Patch private python-gnupg method to reproduce the issue in #4294
    mocker.patch('pretty_bad_protocol._util._separate_keyword',
                 return_value=('PINENTRY_LAUNCHED', 'does not matter'))

    source_app.crypto_util.delete_reply_keypair(fid)

    captured = capsys.readouterr()
    assert "ValueError: Unknown status message: 'PINENTRY_LAUNCHED'" not in captured.err
    assert source_app.crypto_util.get_fingerprint(fid) is None


def test_delete_reply_keypair_no_key(source_app):
    """No exceptions should be raised when provided a filesystem id that
    does not exist.
    """
    source_app.crypto_util.delete_reply_keypair('Reality Winner')


def test_delete_reply_keypair_non_source(source_app):
    """
    Checks that a non-source key is not deleted by delete_reply_keypair.
    """
    name = "SecureDrop Test/Development (DO NOT USE IN PRODUCTION)"
    with pytest.raises(ValueError) as excinfo:
        source_app.crypto_util.delete_reply_keypair(name)
    assert "source key not found" in str(excinfo.value)
    assert source_app.crypto_util.get_fingerprint(name)


def test_get_fingerprint(source_app, test_source):
    assert (source_app.crypto_util.get_fingerprint(test_source['filesystem_id'])
            is not None)

    # check that a non-existent key returns None
    assert source_app.crypto_util.get_fingerprint('x' * 50) is None


def test_get_pubkey(source_app, test_source):
    begin_pgp = '-----BEGIN PGP PUBLIC KEY BLOCK----'

    # check that a filesystem_id exports the pubkey
    pubkey = source_app.crypto_util.get_pubkey(test_source['filesystem_id'])
    assert pubkey.startswith(begin_pgp)

    # check that a non-existent identifer exports None
    pubkey = source_app.crypto_util.get_pubkey('x' * 50)
    assert pubkey is None


@given(
    name=text(alphabet=crypto_util.DICEWARE_SAFE_CHARS),
    secret=text(alphabet=crypto_util.DICEWARE_SAFE_CHARS),
    message=text()
)
def test_encrypt_then_decrypt_gives_same_result(
        source_app,
        test_source,
        name,
        secret,
        message
):
    """Test that encrypting, then decrypting a string gives the original string.

    This is the first test case using `hypothesis`:
    https://hypothesis.readthedocs.io
    """
    crypto = source_app.crypto_util
    # TODO(AD): To be removed in my next PR
    source_user = SourceUser(
        db_record=test_source["source"],
        filesystem_id=test_source["filesystem_id"],
        gpg_secret=crypto.hash_codename(secret, salt=crypto.scrypt_gpg_pepper)
    )
    key = crypto.genkeypair(source_user)
    ciphertext = crypto.encrypt(message, [str(key)])
    decrypted_text = crypto.decrypt(secret, ciphertext)

    assert decrypted_text == message
