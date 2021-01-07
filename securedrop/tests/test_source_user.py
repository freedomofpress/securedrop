from unittest import mock

import pytest

from db import db
from passphrases import PassphraseGenerator
from source_user import SourceDesignationCollisionError
from source_user import SourcePassphraseCollisionError
from source_user import _SourceScryptManager
from source_user import create_source_user


class TestSourceUser:
    def test_create_source_user(self, source_app):
        # Given a passphrase
        passphrase = PassphraseGenerator.get_default().generate_passphrase()

        # When trying to create a new source user with this passphrase, it succeeds
        source_user = create_source_user(
            db_session=db.session,
            source_passphrase=passphrase,
            source_app_crypto_util=source_app.crypto_util,
            source_app_storage=source_app.storage,
        )
        assert source_user
        assert source_user.get_db_record()

    def test_create_source_user_passphrase_collision(self, source_app):
        # Given a source in the DB
        passphrase = PassphraseGenerator.get_default().generate_passphrase()
        create_source_user(
            db_session=db.session,
            source_passphrase=passphrase,
            source_app_crypto_util=source_app.crypto_util,
            source_app_storage=source_app.storage,
        )

        # When trying to create another with the same passphrase, it fails
        with pytest.raises(SourcePassphraseCollisionError):
            create_source_user(
                db_session=db.session,
                source_passphrase=passphrase,
                source_app_crypto_util=source_app.crypto_util,
                source_app_storage=source_app.storage,
            )

    def test_create_source_user_designation_collision(self, source_app):
        # Given a source in the DB
        create_source_user(
            db_session=db.session,
            source_passphrase=PassphraseGenerator.get_default().generate_passphrase(),
            source_app_crypto_util=source_app.crypto_util,
            source_app_storage=source_app.storage,
        )

        # And the next generated journalist designation will be identical to this source's
        with mock.patch.object(source_app.crypto_util, "display_id", side_effect=ValueError):
            # When trying to create another source, it fails, because the designation is the same
            with pytest.raises(SourceDesignationCollisionError):
                create_source_user(
                    db_session=db.session,
                    source_passphrase=PassphraseGenerator.get_default().generate_passphrase(),
                    source_app_crypto_util=source_app.crypto_util,
                    source_app_storage=source_app.storage,
                )


class TestSourceScryptManager:
    def test(self):
        # Given a passphrase
        passphrase = "rehydrate flaring study raven fence extenuate linguist"

        # When deriving the passphrase's filesystem ID and GPG secret
        scrypt_mgr = _SourceScryptManager(
            salt_for_gpg_secret="YrPAwKMyWN66Y2WNSt+FS1KwfysMHwPISG0wmpb717k=".encode(),
            salt_for_filesystem_id="mEFXIwvxoBqjyxc/JypLdvgMRNRjApoaM0OBNrxJM2E=".encode(),
            scrypt_n=2 ** 1,
            scrypt_r=1,
            scrypt_p=1,
        )
        filesystem_id = scrypt_mgr.derive_source_filesystem_id(passphrase)
        gpg_secret = scrypt_mgr.derive_source_gpg_secret(passphrase)

        # It succeeds and the right values are returned
        expected_filesystem_id = "7A7N4GSAB6NRZLUYOTHVYWJGOYIFS24TRC5FQQUSSXCWTF7MJQ7W3QTQLHUFHTKHYO3ONKJ6RSWPS6OI2PFCIW3KI4UZVKGZ3GAIKXI="  # noqa: E501
        assert expected_filesystem_id == filesystem_id

        expected_gpg_secret = "AWCRZVPA6YTQ2A3552LZJW3VO7L3ZONDFT6A6VPRGPGQQSNENRLA3EVRW4LZYNSUV5QIKNFZMJ2BMOVORG43ZETV5ZCRQKLJNOC2BXY="  # noqa: E501
        assert expected_gpg_secret == gpg_secret
