import os

from base64 import b32encode
from functools import lru_cache
from pathlib import Path
from random import SystemRandom
from typing import Optional, List
from typing import TYPE_CHECKING

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf import scrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models

if TYPE_CHECKING:
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


class InvalidPassphraseError(Exception):
    pass


def authenticate_source_user(
    db_session: Session, supplied_passphrase: "DicewarePassphrase"
) -> SourceUser:
    """Try to authenticate a Source user using the passphrase they supplied via the login form."""
    # Validate the passphrase: does it map to an actual Source record in the DB?
    scrypt_manager = _SourceScryptManager.get_default()
    source_filesystem_id = scrypt_manager.derive_source_filesystem_id(supplied_passphrase)
    source_db_record = (
        db_session.query(models.Source)
        .filter_by(
            filesystem_id=source_filesystem_id,
            deleted_at=None,
        )
        .one_or_none()
    )
    if source_db_record is None:
        raise InvalidPassphraseError()

    source_gpg_secret = scrypt_manager.derive_source_gpg_secret(supplied_passphrase)
    return SourceUser(source_db_record, source_filesystem_id, source_gpg_secret)


class SourcePassphraseCollisionError(Exception):
    """Tried to create a Source with a passphrase already used by another Source."""


class SourceDesignationCollisionError(Exception):
    """Tried to create a Source with a journalist designation already used by another Source."""


def create_source_user(
    db_session: Session,
    source_passphrase: "DicewarePassphrase",
    source_app_storage: "Storage",
) -> SourceUser:
    # Derive the source's info from their passphrase
    scrypt_manager = _SourceScryptManager.get_default()
    filesystem_id = scrypt_manager.derive_source_filesystem_id(source_passphrase)
    gpg_secret = scrypt_manager.derive_source_gpg_secret(source_passphrase)

    # Create a unique journalist designation for the source
    # TODO: Add unique=True to models.Source.journalist_designation to enforce uniqueness
    #  as the logic below has a race condition (time we check VS time when we add to the DB)
    designation_generation_attempts = 0
    valid_designation = None
    designation_generator = _DesignationGenerator.get_default()
    while designation_generation_attempts < 50:
        # Generate a designation
        designation_generation_attempts += 1
        new_designation = designation_generator.generate_journalist_designation()

        # Check to see if it's already used by an existing source
        existing_source_with_same_designation = db_session.query(
            models.Source
        ).filter_by(journalist_designation=new_designation).one_or_none()
        if not existing_source_with_same_designation:
            # The designation is not already used - good to go
            valid_designation = new_designation
            break

    if not valid_designation:
        # Could not generate a designation that is not already used
        raise SourceDesignationCollisionError()

    # Store the source in the DB
    source_db_record = models.Source(
        filesystem_id=filesystem_id, journalist_designation=valid_designation
    )
    db_session.add(source_db_record)
    try:
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        raise SourcePassphraseCollisionError(
            "Passphrase already used by another Source (filesystem_id {})".format(filesystem_id)
        )

    # Create the source's folder
    os.mkdir(source_app_storage.path(filesystem_id))

    # All done
    return SourceUser(source_db_record, filesystem_id, gpg_secret)


_default_scrypt_mgr: Optional["_SourceScryptManager"] = None


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

    # Use @lru_cache to not recompute the same values over and over for the same user
    @lru_cache
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

    @lru_cache
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

    @classmethod
    def get_default(cls) -> "_SourceScryptManager":
        # Late import so _SourceScryptManager can be used without a config.py in the parent folder
        from sdconfig import config

        global _default_scrypt_mgr
        if _default_scrypt_mgr is None:
            _default_scrypt_mgr = cls(
                salt_for_gpg_secret=config.SCRYPT_GPG_PEPPER.encode("utf-8"),
                salt_for_filesystem_id=config.SCRYPT_ID_PEPPER.encode("utf-8"),
                scrypt_n=config.SCRYPT_PARAMS["N"],
                scrypt_r=config.SCRYPT_PARAMS["r"],
                scrypt_p=config.SCRYPT_PARAMS["p"],
            )
        return _default_scrypt_mgr


_default_designation_generator: Optional["_DesignationGenerator"] = None


class _DesignationGenerator:

    def __init__(self, nouns: List[str], adjectives: List[str]):
        self._random_generator = SystemRandom()

        # Ensure that there are no empty lists or empty strings
        if not nouns:
            raise ValueError("Nouns word list is empty")
        shortest_noun = min(nouns, key=len)
        shortest_noun_length = len(shortest_noun)
        if shortest_noun_length < 1:
            raise ValueError("Nouns word list contains an empty string")

        if not adjectives:
            raise ValueError("Adjectives word list is empty")
        shortest_adjective = min(adjectives, key=len)
        shortest_adjective_length = len(shortest_adjective)
        if shortest_adjective_length < 1:
            raise ValueError("Adjectives word list contains an empty string")

        self._nouns = nouns
        self._adjectives = adjectives

    def generate_journalist_designation(self) -> str:
        random_adjective = self._random_generator.choice(self._adjectives)
        random_noun = self._random_generator.choice(self._nouns)
        return f"{random_adjective} {random_noun}"

    @classmethod
    def get_default(cls) -> "_DesignationGenerator":
        # Late import so _SourceScryptManager can be used without a config.py in the parent folder
        from sdconfig import config

        global _default_designation_generator
        if _default_designation_generator is None:
            # Parse the nouns and adjectives files from the config
            nouns = Path(config.NOUNS).read_text().strip().splitlines()
            adjectives = Path(config.ADJECTIVES).read_text().strip().splitlines()

            # Create the generator
            _default_designation_generator = cls(nouns=nouns, adjectives=adjectives)

        return _default_designation_generator
