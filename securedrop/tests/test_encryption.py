from pathlib import Path
from unittest.mock import MagicMock

import pytest
from db import db
from encryption import EncryptionManager, GpgDecryptError, GpgKeyNotFoundError
from passphrases import PassphraseGenerator
from redis import Redis
from source_user import create_source_user
from tests import utils

import redwood
from redwood import RedwoodError


class TestEncryptionManager:
    def test_get_default(self, config):
        # Given an encryption manager
        encryption_mgr = EncryptionManager.get_default()
        assert encryption_mgr
        # When using the encryption manager to fetch the journalist public key
        # It succeeds
        assert redwood.is_valid_public_key(encryption_mgr.get_journalist_public_key())

    def test_get_gpg_source_public_key(self, test_source):
        # Given a source user with a key pair in the gpg keyring
        source_user = test_source["source_user"]
        encryption_mgr = EncryptionManager.get_default()
        utils.create_legacy_gpg_key(encryption_mgr, source_user, test_source["source"])

        # When using the encryption manager to fetch the source user's public key
        # It succeeds
        source_pub_key = encryption_mgr.get_source_public_key(source_user.filesystem_id)
        assert redwood.is_valid_public_key(source_pub_key)

        # And the key's fingerprint was saved to Redis
        source_key_fingerprint = encryption_mgr._redis.hget(
            encryption_mgr.REDIS_FINGERPRINT_HASH, source_user.filesystem_id
        )
        assert source_key_fingerprint

        # And the public key was saved to Redis
        assert encryption_mgr._redis.hget(encryption_mgr.REDIS_KEY_HASH, source_key_fingerprint)

    def test_get_gpg_source_public_key_wrong_id(self, test_source):
        # Given an encryption manager
        encryption_mgr = EncryptionManager.get_default()

        # When using the encryption manager to fetch a key for an invalid filesystem id
        # It fails
        with pytest.raises(GpgKeyNotFoundError):
            encryption_mgr.get_source_public_key("1234test")

    def test_delete_gpg_source_key_pair(self, source_app, test_source):
        # Given a source user with a key pair in the gpg keyring
        source_user = test_source["source_user"]
        encryption_mgr = EncryptionManager.get_default()
        utils.create_legacy_gpg_key(encryption_mgr, source_user, test_source["source"])
        assert encryption_mgr.get_source_public_key(source_user.filesystem_id)

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

    def test_delete_source_key_pair_pinentry_status_is_handled(
        self, source_app, test_source, mocker, capsys
    ):
        """
        Regression test for https://github.com/freedomofpress/securedrop/issues/4294
        """
        # Given a source user with a key pair in the gpg keyring
        source_user = test_source["source_user"]
        encryption_mgr = EncryptionManager.get_default()
        utils.create_legacy_gpg_key(encryption_mgr, source_user, test_source["source"])
        assert encryption_mgr.get_source_public_key(source_user.filesystem_id)

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

    def test_encrypt_source_message(self, config, tmp_path):
        # Given an encryption manager
        encryption_mgr = EncryptionManager.get_default()

        # And a message to be submitted by a source
        message = "s3cr3t message"

        # When the source tries to encrypt the message
        # It succeeds
        encrypted_message_path = tmp_path / "message.gpg"
        encryption_mgr.encrypt_source_message(
            message_in=message, encrypted_message_path_out=encrypted_message_path
        )

        # And the output file doesn't contain the message plaintext
        encrypted_message = encrypted_message_path.read_bytes()
        assert message.encode() not in encrypted_message

        # And the journalist is able to decrypt the message
        decrypted_message = utils.decrypt_as_journalist(encrypted_message).decode()
        assert decrypted_message == message

    def test_encrypt_source_file(self, config, tmp_path):
        # Given an encryption manager
        encryption_mgr = EncryptionManager.get_default()

        # And a file to be submitted by a source - we use this python file
        file_to_encrypt_path = Path(__file__)

        # When the source tries to encrypt the file
        # It succeeds
        encrypted_file_path = tmp_path / "file.gpg"
        with file_to_encrypt_path.open("rb") as fh:
            encryption_mgr.encrypt_source_file(
                file_in=fh,
                encrypted_file_path_out=encrypted_file_path,
            )

        # And the output file doesn't contain the file plaintext
        encrypted_file = encrypted_file_path.read_bytes()
        assert file_to_encrypt_path.read_bytes() not in encrypted_file

        # And the journalist is able to decrypt the file
        decrypted_file = utils.decrypt_as_journalist(encrypted_file)
        assert decrypted_file == file_to_encrypt_path.read_bytes()

    def test_encrypt_and_decrypt_journalist_reply(
        self, source_app, test_source, tmp_path, app_storage
    ):
        # Given a source user
        source_user1 = test_source["source_user"]
        source1 = test_source["source"]
        encryption_mgr = EncryptionManager.get_default()

        # And another source user
        with source_app.app_context():
            source_user2 = create_source_user(
                db_session=db.session,
                source_passphrase=PassphraseGenerator.get_default().generate_passphrase(),
                source_app_storage=app_storage,
            )
        source_user2.get_db_record()

        # When the journalist tries to encrypt a reply to source1
        # It succeeds
        journalist_reply = "s3cr3t message"
        encrypted_reply_path = tmp_path / "reply.gpg"
        encryption_mgr.encrypt_journalist_reply(
            for_source=source1,
            reply_in=journalist_reply,
            encrypted_reply_path_out=encrypted_reply_path,
        )

        # And the output file doesn't contain the reply plaintext
        encrypted_reply = encrypted_reply_path.read_bytes()
        assert journalist_reply.encode() not in encrypted_reply

        # And source1 is able to decrypt the reply
        decrypted_reply = encryption_mgr.decrypt_journalist_reply(
            for_source_user=source_user1,
            ciphertext_in=encrypted_reply,
        )
        assert decrypted_reply == journalist_reply

        # And source2 is NOT able to decrypt the reply
        with pytest.raises(RedwoodError):
            encryption_mgr.decrypt_journalist_reply(
                for_source_user=source_user2,
                ciphertext_in=encrypted_reply,
            )

        # And the journalist is able to decrypt their own reply
        decrypted_reply_for_journalist = utils.decrypt_as_journalist(encrypted_reply)
        assert decrypted_reply_for_journalist.decode() == journalist_reply

    def test_gpg_encrypt_and_decrypt_journalist_reply(
        self, source_app, test_source, tmp_path, app_storage
    ):
        # Given a source user with a key pair in the gpg keyring
        source_user1 = test_source["source_user"]
        source1 = test_source["source"]
        encryption_mgr = EncryptionManager.get_default()
        utils.create_legacy_gpg_key(encryption_mgr, source_user1, source1)

        # And another source with a key pair in the gpg keyring
        with source_app.app_context():
            source_user2 = create_source_user(
                db_session=db.session,
                source_passphrase=PassphraseGenerator.get_default().generate_passphrase(),
                source_app_storage=app_storage,
            )
            source2 = source_user2.get_db_record()
            utils.create_legacy_gpg_key(encryption_mgr, source_user2, source2)

            # When the journalist tries to encrypt a reply to source1
            # It succeeds
            journalist_reply = "s3cr3t message"
            encrypted_reply_path = tmp_path / "reply.gpg"
            encryption_mgr.encrypt_journalist_reply(
                for_source=source1,
                reply_in=journalist_reply,
                encrypted_reply_path_out=encrypted_reply_path,
            )

            # And the output file doesn't contain the reply plaintext
            encrypted_reply = encrypted_reply_path.read_bytes()
            assert journalist_reply.encode() not in encrypted_reply

            # And source1 is able to decrypt the reply
            decrypted_reply = encryption_mgr.decrypt_journalist_reply(
                for_source_user=source_user1,
                ciphertext_in=encrypted_reply,
            )
            assert decrypted_reply == journalist_reply

            # And source2 is NOT able to decrypt the reply
            with pytest.raises(GpgDecryptError):
                encryption_mgr.decrypt_journalist_reply(
                    for_source_user=source_user2,
                    ciphertext_in=encrypted_reply,
                )

        # Amd the reply can't be decrypted without providing the source1's gpg secret
        result = encryption_mgr.gpg().decrypt(
            # For GPG 2.1+, a non-null passphrase _must_ be passed to decrypt()
            encrypted_reply,
            passphrase="test 123",
        )
        assert not result.ok

        # And the journalist is able to decrypt their reply
        decrypted_reply_for_journalist = utils.decrypt_as_journalist(encrypted_reply).decode()
        assert decrypted_reply_for_journalist == journalist_reply

    def test_get_source_secret_key_from_gpg(self, test_source, tmp_path, config):
        source_user = test_source["source_user"]
        source = test_source["source"]

        encryption_mgr = EncryptionManager(
            gpg_key_dir=tmp_path,
            journalist_pub_key=(config.SECUREDROP_DATA_ROOT / "journalist.pub"),
            redis=Redis(decode_responses=True, **config.REDIS_KWARGS),
        )
        new_fingerprint = utils.create_legacy_gpg_key(encryption_mgr, source_user, source)
        secret_key = encryption_mgr.get_source_secret_key_from_gpg(
            new_fingerprint, source_user.gpg_secret
        )
        assert secret_key.splitlines()[0] == "-----BEGIN PGP PRIVATE KEY BLOCK-----"
        # Now try an invalid passphrase
        with pytest.raises(GpgKeyNotFoundError):
            encryption_mgr.get_source_secret_key_from_gpg(new_fingerprint, "not correct passphrase")
        # Now if we get a garbage response from GPG
        mock_gpg = MagicMock()
        mock_gpg.export_keys.return_value = "definitely not a gpg secret key"
        encryption_mgr._gpg = mock_gpg
        with pytest.raises(GpgKeyNotFoundError):
            encryption_mgr.get_source_secret_key_from_gpg(new_fingerprint, source_user.gpg_secret)
