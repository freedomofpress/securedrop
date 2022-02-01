import typing
from contextlib import contextmanager
from pathlib import Path

import pytest as pytest

from db import db
from encryption import EncryptionManager, GpgKeyNotFoundError, GpgEncryptError, GpgDecryptError
from datetime import datetime
from passphrases import PassphraseGenerator
from source_user import create_source_user


class TestEncryptionManager:
    def test_get_default(self, config):
        encryption_mgr = EncryptionManager.get_default()
        assert encryption_mgr
        assert encryption_mgr.get_journalist_public_key()

    def test_generate_source_key_pair(self, setup_journalist_key_and_gpg_folder,
                                      source_app, app_storage):
        # Given a source user
        with source_app.app_context():
            source_user = create_source_user(
                db_session=db.session,
                source_passphrase=PassphraseGenerator.get_default().generate_passphrase(),
                source_app_storage=app_storage,
            )

        # And an encryption manager
        journalist_key_fingerprint, gpg_key_dir = setup_journalist_key_and_gpg_folder
        encryption_mgr = EncryptionManager(
            gpg_key_dir=gpg_key_dir, journalist_key_fingerprint=journalist_key_fingerprint
        )

        # When using the encryption manager to generate a key pair for this source user
        # It succeeds
        encryption_mgr.generate_source_key_pair(source_user)

        # And the newly-created key's fingerprint was added to Redis
        fingerprint_in_redis = encryption_mgr._redis.hget(
            encryption_mgr.REDIS_FINGERPRINT_HASH, source_user.filesystem_id
        )
        assert fingerprint_in_redis
        source_key_fingerprint = encryption_mgr.get_source_key_fingerprint(
            source_user.filesystem_id
        )
        assert fingerprint_in_redis == source_key_fingerprint

        # And the user's newly-generated public key can be retrieved
        assert encryption_mgr.get_source_public_key(source_user.filesystem_id)

        # And the key has a hardcoded creation date to avoid leaking information about when sources
        # first created their account
        source_key_details = encryption_mgr._get_source_key_details(source_user.filesystem_id)
        assert source_key_details
        creation_date = _parse_gpg_date_string(source_key_details["date"])
        assert creation_date.date() == EncryptionManager.DEFAULT_KEY_CREATION_DATE

        # And the user's key does not expire
        assert source_key_details["expires"] == ""

    def test_get_source_public_key(self, test_source):
        # Given a source user with a key pair in the default encryption manager
        source_user = test_source["source_user"]
        encryption_mgr = EncryptionManager.get_default()

        # When using the encryption manager to fetch the source user's public key
        # It succeeds
        source_pub_key = encryption_mgr.get_source_public_key(source_user.filesystem_id)
        assert source_pub_key
        assert source_pub_key.startswith("-----BEGIN PGP PUBLIC KEY BLOCK----")

        # And the key's fingerprint was saved to Redis
        source_key_fingerprint = encryption_mgr._redis.hget(
            encryption_mgr.REDIS_FINGERPRINT_HASH, source_user.filesystem_id
        )
        assert source_key_fingerprint

        # And the public key was saved to Redis
        assert encryption_mgr._redis.hget(encryption_mgr.REDIS_KEY_HASH, source_key_fingerprint)

    def test_get_journalist_public_key(self, setup_journalist_key_and_gpg_folder):
        # Given an encryption manager
        journalist_key_fingerprint, gpg_key_dir = setup_journalist_key_and_gpg_folder
        encryption_mgr = EncryptionManager(
            gpg_key_dir=gpg_key_dir, journalist_key_fingerprint=journalist_key_fingerprint
        )

        # When using the encryption manager to fetch the journalist public key
        # It succeeds
        journalist_pub_key = encryption_mgr.get_journalist_public_key()
        assert journalist_pub_key
        assert journalist_pub_key.startswith("-----BEGIN PGP PUBLIC KEY BLOCK----")

    def test_get_source_public_key_wrong_id(self, setup_journalist_key_and_gpg_folder):
        # Given an encryption manager
        journalist_key_fingerprint, gpg_key_dir = setup_journalist_key_and_gpg_folder
        encryption_mgr = EncryptionManager(
            gpg_key_dir=gpg_key_dir, journalist_key_fingerprint=journalist_key_fingerprint
        )

        # When using the encryption manager to fetch a key for an invalid filesystem id
        # It fails
        with pytest.raises(GpgKeyNotFoundError):
            encryption_mgr.get_source_public_key("1234test")

    def test_delete_source_key_pair(self, source_app, test_source):
        # Given a source user with a key pair in the default encryption manager
        source_user = test_source["source_user"]
        encryption_mgr = EncryptionManager.get_default()

        # When using the encryption manager to delete this source user's key pair
        # It succeeds
        encryption_mgr.delete_source_key_pair(source_user.filesystem_id)

        # And the user's key information can no longer be retrieved
        with pytest.raises(GpgKeyNotFoundError):
            encryption_mgr.get_source_public_key(source_user.filesystem_id)

        with pytest.raises(GpgKeyNotFoundError):
            encryption_mgr.get_source_key_fingerprint(source_user.filesystem_id)

        with pytest.raises(GpgKeyNotFoundError):
            encryption_mgr._get_source_key_details(source_user.filesystem_id)

    def test_delete_source_key_pair_on_journalist_key(self, setup_journalist_key_and_gpg_folder):
        # Given an encryption manager
        journalist_key_fingerprint, gpg_key_dir = setup_journalist_key_and_gpg_folder
        encryption_mgr = EncryptionManager(
            gpg_key_dir=gpg_key_dir, journalist_key_fingerprint=journalist_key_fingerprint
        )

        # When trying to delete the journalist key via the encryption manager
        # It fails
        with pytest.raises(GpgKeyNotFoundError):
            encryption_mgr.delete_source_key_pair(journalist_key_fingerprint)

    def test_delete_source_key_pair_pinentry_status_is_handled(
        self, source_app, test_source, mocker, capsys
    ):
        """
        Regression test for https://github.com/freedomofpress/securedrop/issues/4294
        """
        # Given a source user with a key pair in the default encryption manager
        source_user = test_source["source_user"]
        encryption_mgr = EncryptionManager.get_default()

        # And a gpg binary that will trigger the issue described in #4294
        mocker.patch(
            "pretty_bad_protocol._util._separate_keyword",
            return_value=("PINENTRY_LAUNCHED", "does not matter"),
        )

        # When using the encryption manager to delete this source user's key pair
        # It succeeds
        encryption_mgr.delete_source_key_pair(source_user.filesystem_id)

        # And the user's key information can no longer be retrieved
        with pytest.raises(GpgKeyNotFoundError):
            encryption_mgr.get_source_key_fingerprint(source_user.filesystem_id)

        # And the bug fix was properly triggered
        captured = capsys.readouterr()
        assert "ValueError: Unknown status message: 'PINENTRY_LAUNCHED'" not in captured.err

    def test_encrypt_source_message(self, setup_journalist_key_and_gpg_folder, tmp_path):
        # Given an encryption manager
        journalist_key_fingerprint, gpg_key_dir = setup_journalist_key_and_gpg_folder
        encryption_mgr = EncryptionManager(
            gpg_key_dir=gpg_key_dir, journalist_key_fingerprint=journalist_key_fingerprint
        )

        # And a message to be submitted by a source
        message = "s3cr3t message"

        # When the source tries to encrypt the message
        # It succeeds
        encrypted_message_path = tmp_path / "message.gpg"
        encryption_mgr.encrypt_source_message(
            message_in=message, encrypted_message_path_out=encrypted_message_path
        )

        # And the output file contains the encrypted data
        encrypted_message = encrypted_message_path.read_bytes()
        assert encrypted_message

        # And the journalist is able to decrypt the message
        with import_journalist_private_key(encryption_mgr):
            decrypted_message = encryption_mgr._gpg.decrypt(encrypted_message).data
        assert decrypted_message.decode() == message

        # And the source or anyone else is NOT able to decrypt the message
        # For GPG 2.1+, a non-null passphrase _must_ be passed to decrypt()
        assert not encryption_mgr._gpg.decrypt(encrypted_message, passphrase="test 123").ok

    def test_encrypt_source_file(self, setup_journalist_key_and_gpg_folder, tmp_path):
        # Given an encryption manager
        journalist_key_fingerprint, gpg_key_dir = setup_journalist_key_and_gpg_folder
        encryption_mgr = EncryptionManager(
            gpg_key_dir=gpg_key_dir, journalist_key_fingerprint=journalist_key_fingerprint
        )

        # And a file to be submitted by a source - we use this python file
        file_to_encrypt_path = Path(__file__)
        with file_to_encrypt_path.open() as file_to_encrypt:

            # When the source tries to encrypt the file
            # It succeeds
            encrypted_file_path = tmp_path / "file.gpg"
            encryption_mgr.encrypt_source_file(
                file_in=file_to_encrypt,
                encrypted_file_path_out=encrypted_file_path,
            )

            # And the output file contains the encrypted data
            encrypted_file = encrypted_file_path.read_bytes()
            assert encrypted_file

        # And the journalist is able to decrypt the file
        with import_journalist_private_key(encryption_mgr):
            decrypted_file = encryption_mgr._gpg.decrypt(encrypted_file).data
        assert decrypted_file.decode() == file_to_encrypt_path.read_text()

        # And the source or anyone else is NOT able to decrypt the file
        # For GPG 2.1+, a non-null passphrase _must_ be passed to decrypt()
        assert not encryption_mgr._gpg.decrypt(encrypted_file, passphrase="test 123").ok

    def test_encrypt_and_decrypt_journalist_reply(self, source_app, test_source,
                                                  tmp_path, app_storage):
        # Given a source user with a key pair in the default encryption manager
        source_user1 = test_source["source_user"]
        encryption_mgr = EncryptionManager.get_default()

        # And another source with a key pair in the default encryption manager
        with source_app.app_context():
            source_user2 = create_source_user(
                db_session=db.session,
                source_passphrase=PassphraseGenerator.get_default().generate_passphrase(),
                source_app_storage=app_storage,
            )
        encryption_mgr.generate_source_key_pair(source_user2)

        # When the journalist tries to encrypt a reply to source1
        # It succeeds
        journalist_reply = "s3cr3t message"
        encrypted_reply_path = tmp_path / "reply.gpg"
        encryption_mgr.encrypt_journalist_reply(
            for_source_with_filesystem_id=source_user1.filesystem_id,
            reply_in=journalist_reply,
            encrypted_reply_path_out=encrypted_reply_path,
        )

        # And the output file contains the encrypted data
        encrypted_reply = encrypted_reply_path.read_bytes()
        assert encrypted_reply

        # And source1 is able to decrypt the reply
        decrypted_reply = encryption_mgr.decrypt_journalist_reply(
            for_source_user=source_user1, ciphertext_in=encrypted_reply
        )
        assert decrypted_reply
        assert decrypted_reply == journalist_reply

        # And source2 is NOT able to decrypt the reply
        with pytest.raises(GpgDecryptError):
            encryption_mgr.decrypt_journalist_reply(
                for_source_user=source_user2, ciphertext_in=encrypted_reply
            )

        # Amd the reply can't be decrypted without providing the source1's gpg secret
        result = encryption_mgr._gpg.decrypt(
            # For GPG 2.1+, a non-null passphrase _must_ be passed to decrypt()
            encrypted_reply,
            passphrase="test 123",
        )
        assert not result.ok

        # And the journalist is able to decrypt their reply
        with import_journalist_private_key(encryption_mgr):
            decrypted_reply_for_journalist = encryption_mgr._gpg.decrypt(
                # For GPG 2.1+, a non-null passphrase _must_ be passed to decrypt()
                encrypted_reply,
                passphrase="test 123",
            ).data
        assert decrypted_reply_for_journalist.decode() == journalist_reply

    def test_encrypt_fails(self, setup_journalist_key_and_gpg_folder, tmp_path):
        # Given an encryption manager
        journalist_key_fingerprint, gpg_key_dir = setup_journalist_key_and_gpg_folder
        encryption_mgr = EncryptionManager(
            gpg_key_dir=gpg_key_dir, journalist_key_fingerprint=journalist_key_fingerprint
        )

        # When trying to encrypt some data without providing any recipient
        # It fails and the right exception is raised
        with pytest.raises(GpgEncryptError) as exc:
            encryption_mgr._encrypt(
                using_keys_with_fingerprints=[],
                plaintext_in="test",
                ciphertext_path_out=tmp_path / "encrypt_fails",
            )
        assert "no terminal at all requested" in str(exc)


def _parse_gpg_date_string(date_string: str) -> datetime:
    """Parse a date string returned from `gpg --with-colons --list-keys` into a datetime.

    The format of the date strings is complicated; see gnupg doc/DETAILS for a
    full explanation.

    Key details:
    - The creation date of the key is given in UTC.
    - the date is usually printed in seconds since epoch, however, we are
    migrating to an ISO 8601 format (e.g. "19660205T091500"). A simple
    way to detect the new format is to scan for the 'T'.
    """
    if "T" in date_string:
        dt = datetime.strptime(date_string, "%Y%m%dT%H%M%S")
    else:
        dt = datetime.utcfromtimestamp(int(date_string))
    return dt


@contextmanager
def import_journalist_private_key(
    encryption_mgr: EncryptionManager,
) -> typing.Generator[None, None, None]:
    """Import the journalist secret key so the encryption_mgr can decrypt data for the journalist.

    The journalist secret key is removed at the end of this context manager in order to not impact
    other decryption-related tests.
    """
    # Import the journalist private key
    journalist_private_key_path = Path(__file__).parent / "files" / "test_journalist_key.sec"
    encryption_mgr._gpg.import_keys(journalist_private_key_path.read_text())
    journalist_secret_key_fingerprint = "C1C4E16BB24E4F4ABF37C3A6C3E7C4C0A2201B2A"

    yield

    # Make sure to remove the journalist private key to not impact the other tests
    encryption_mgr._gpg_for_key_deletion.delete_keys(
        fingerprints=journalist_secret_key_fingerprint, secret=True, subkeys=False
    )

    # Double check that the journlist private key was removed
    is_journalist_secret_key_available = False
    for key in encryption_mgr._gpg.list_keys(secret=True):
        for uid in key["uids"]:
            if "SecureDrop Test" in uid:
                is_journalist_secret_key_available = True
                break
    assert not is_journalist_secret_key_available
