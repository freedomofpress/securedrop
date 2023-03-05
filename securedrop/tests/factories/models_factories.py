from datetime import datetime
from typing import List, Optional

import models
from encryption import EncryptionManager
from passphrases import PassphraseGenerator
from source_user import create_source_user


class SourceFactory:
    @staticmethod
    def create(
        db_session,
        app_storage,
        *,
        pending: bool = False,
        is_starred: bool = False,
        deleted_at: Optional[datetime] = None,
    ) -> models.Source:
        passphrase = PassphraseGenerator.get_default().generate_passphrase()
        source_user = create_source_user(
            db_session=db_session,
            source_passphrase=passphrase,
            source_app_storage=app_storage,
        )
        EncryptionManager.get_default().generate_source_key_pair(source_user)

        source = source_user.get_db_record()
        source.pending = pending

        if is_starred:
            star = models.SourceStar(
                source=source,
                starred=is_starred,
            )
            db_session.add(star)

        if deleted_at:
            source.deleted_at = deleted_at

        db_session.commit()
        return source

    @classmethod
    def create_batch(
        cls,
        db_session,
        app_storage,
        records_count: int,
        *,
        pending: bool = False,
        is_starred: bool = False,
        deleted_at: Optional[datetime] = None,
    ) -> List[models.Source]:
        created_sources = []
        for _ in range(records_count):
            source = cls.create(
                db_session, app_storage, pending=pending, deleted_at=deleted_at, is_starred=is_starred,
            )
            created_sources.append(source)
        return created_sources
