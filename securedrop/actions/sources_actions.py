from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import models
from actions.exceptions import NotFoundError
from actions.pagination import SupportsPagination
from encryption import EncryptionManager, GpgKeyNotFoundError
from sqlalchemy.orm import Query, Session
from store import Storage


class SearchSourcesOrderByEnum(str, Enum):
    # Not needed yet; only here if we ever need to order the results. For example:
    # LAST_UPDATED_DESC = "LAST_UPDATED_DESC"
    pass


@dataclass(frozen=True)
class SearchSourcesFilters:
    # The default values for the filters below are meant to match the most common
    # "use case" when searching sources. Also, using None means "don't enable this filter"
    filter_by_is_pending: Optional[bool] = False
    filter_by_is_starred: Optional[bool] = None
    filter_by_is_deleted: Optional[bool] = False
    filter_by_was_updated_after: Optional[datetime] = None


class SearchSourcesAction(SupportsPagination):
    def __init__(
        self,
        db_session: Session,
        filters: SearchSourcesFilters = SearchSourcesFilters(),
        order_by: Optional[SearchSourcesOrderByEnum] = None,
    ):
        self._db_session = db_session
        self._filters = filters
        if order_by:
            raise NotImplementedError("The order_by argument is not implemented")

    def create_query(self) -> Query:
        query = self._db_session.query(models.Source)

        if self._filters.filter_by_is_deleted is True:
            query = query.filter(models.Source.deleted_at.isnot(None))
        elif self._filters.filter_by_is_deleted is False:
            query = query.filter(models.Source.deleted_at.is_(None))
        else:
            # filter_by_is_deleted is None; nothing to do
            pass

        if self._filters.filter_by_is_pending is not None:
            query = query.filter_by(pending=self._filters.filter_by_is_pending)

        if self._filters.filter_by_is_starred is not None:
            query = query.filter(models.Source.is_starred == self._filters.filter_by_is_starred)

        if self._filters.filter_by_was_updated_after is not None:
            query = query.filter(
                models.Source.last_updated > self._filters.filter_by_was_updated_after
            )

        if self._filters.filter_by_is_pending in [None, False]:
            # Never return sources with a None last_updated field unless "pending" sources
            #  were explicitly requested
            query = query.filter(models.Source.last_updated.isnot(None))

        return query


class GetSingleSourceAction:
    def __init__(
        self,
        db_session: Session,
        # The two arguments are mutually exclusive
        filesystem_id: Optional[str] = None,
        uuid: Optional[str] = None,
    ) -> None:
        self._db_session = db_session
        if uuid and filesystem_id:
            raise ValueError("uuid and filesystem_id are mutually exclusive")
        if uuid is None and filesystem_id is None:
            raise ValueError("At least one of uuid and filesystem_id must be supplied")

        self._filesystem_id = filesystem_id
        self._uuid = uuid

    def perform(self) -> models.Source:
        source: Optional[models.Source]
        if self._uuid:
            source = self._db_session.query(models.Source).filter_by(uuid=self._uuid).one_or_none()
        elif self._filesystem_id:
            source = (
                self._db_session.query(models.Source)
                .filter_by(filesystem_id=self._filesystem_id)
                .one_or_none()
            )
        else:
            raise ValueError("Should never happen")

        if source is None:
            raise NotFoundError()
        else:
            return source


class DeleteSingleSourceAction:
    """Delete a source and all of its submissions and GPG key."""

    def __init__(
        self,
        db_session: Session,
        source: models.Source,
    ) -> None:
        self._db_session = db_session
        self._source = source

    def perform(self) -> None:
        # Delete the source's collection of submissions
        path = Path(Storage.get_default().path(self._source.filesystem_id))
        if path.exists():
            Storage.get_default().move_to_shredder(path.as_posix())

        # Delete the source's reply keypair, if it exists
        try:
            EncryptionManager.get_default().delete_source_key_pair(self._source.filesystem_id)
        except GpgKeyNotFoundError:
            pass

        # Delete their entry in the db
        self._db_session.delete(self._source)
        self._db_session.commit()
