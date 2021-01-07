import os
from base64 import b32encode
from typing import TYPE_CHECKING

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf import scrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models

if TYPE_CHECKING:
    from crypto_util import CryptoUtil
    from passphrases import DicewarePassphrase
    from store import Storage


class SourceUser:
    """A source user and their associated data derived from their passphrase."""

    def __init__(self, db_record: models.Source, filesystem_id: str, gpg_secret: str) -> None:
        self.gpg_secret = gpg_secret
        self.filesystem_id = filesystem_id
        self.db_record_id = db_record.id  # We don't store the actual record to force a refresh

    def get_db_record(self) -> models.Source:
        return models.Source.query.get(self.db_record_id)


class SourcePassphraseCollisionError(Exception):
    """Tried to create a Source with a passphrase already used by another Source."""


class SourceDesignationCollisionError(Exception):
    """Tried to create a Source with a journalist designation already used by another Source."""


def create_source_user(
    db_session: Session,
    source_passphrase: "DicewarePassphrase",
    source_app_crypto_util: "CryptoUtil",
    source_app_storage: "Storage",
) -> SourceUser:
    # Derive the source's info from their passphrase
    # TODO(AD): This will be updated in my next PR to not take params from the CryptoUtil instance
    scrypt_manager = _SourceScryptManager(
        salt_for_gpg_secret=source_app_crypto_util.scrypt_gpg_pepper.encode(),
        salt_for_filesystem_id=source_app_crypto_util.scrypt_id_pepper.encode(),
        scrypt_n=source_app_crypto_util.scrypt_params["N"],
        scrypt_r=source_app_crypto_util.scrypt_params["r"],
        scrypt_p=source_app_crypto_util.scrypt_params["p"],
    )
    filesystem_id = scrypt_manager.derive_source_filesystem_id(source_passphrase)
    gpg_secret = scrypt_manager.derive_source_gpg_secret(source_passphrase)

    # Create a designation for the source
    try:
        journalist_designation = source_app_crypto_util.display_id()
    except ValueError:
        raise SourceDesignationCollisionError()

    # Store the source in the DB
    source_db_record = models.Source(filesystem_id, journalist_designation)
    db_session.add(source_db_record)
    try:
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        raise SourcePassphraseCollisionError(
            "Passphrase {} is already used by another Source".format(source_passphrase)
        )
    # Create the source's folder
    os.mkdir(source_app_storage.path(filesystem_id))

    # All done
    return SourceUser(source_db_record, filesystem_id, gpg_secret)


class _SourceScryptManager:
    def __init__(
        self,
        salt_for_gpg_secret: bytes,
        salt_for_filesystem_id: bytes,
        scrypt_n: int,
        scrypt_r: int,
        scrypt_p: int,
    ) -> None:
        if salt_for_gpg_secret == salt_for_filesystem_id:
            raise ValueError("scrypt_id_pepper == scrypt_gpg_pepper")

        self._salt_for_gpg_secret = salt_for_gpg_secret
        self._salt_for_filesystem_id = salt_for_filesystem_id
        self._scrypt_n = scrypt_n
        self._scrypt_r = scrypt_r
        self._scrypt_p = scrypt_p
        self._backend = default_backend()

    def derive_source_gpg_secret(self, source_passphrase: "DicewarePassphrase") -> str:
        scrypt_for_gpg_secret = scrypt.Scrypt(
            length=64,
            salt=self._salt_for_gpg_secret,
            n=self._scrypt_n,
            r=self._scrypt_r,
            p=self._scrypt_p,
            backend=self._backend,
        )
        hashed_passphrase = scrypt_for_gpg_secret.derive(source_passphrase.encode("utf-8"))
        return b32encode(hashed_passphrase).decode("utf-8")

    def derive_source_filesystem_id(self, source_passphrase: "DicewarePassphrase") -> str:
        scrypt_for_filesystem_id = scrypt.Scrypt(
            length=64,
            salt=self._salt_for_filesystem_id,
            n=self._scrypt_n,
            r=self._scrypt_r,
            p=self._scrypt_p,
            backend=self._backend,
        )
        hashed_passphrase = scrypt_for_filesystem_id.derive(source_passphrase.encode("utf-8"))
        return b32encode(hashed_passphrase).decode("utf-8")
