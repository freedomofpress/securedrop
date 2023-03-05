from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session

import models


@dataclass
class PaginationConfig:
    # TODO: Validate and reject negative numbers
    page_size: int
    page_number: int


class SupportsPagination:

    @abstractmethod
    def create_query(self):
        pass

    @abstractmethod
    def perform(self, paginate_results_with_config: Optional[PaginationConfig] = None):
        pass


# TODO
class SearchSourcesOrderByEnum(str, Enum):
    pass


@dataclass(frozen=True)
class SearchSourcesFilters:
    # The default values for the filters below are meant to match the most common
    # "use case" when searching sources. Also, using None means "don't enable this filter"
    filter_by_is_pending: Optional[bool] = False
    filter_by_is_starred: Optional[bool] = None
    filter_by_was_updated_after: Optional[datetime] = None


class SearchSourcesAction(SupportsPagination):
    def __init__(
        self,
        db_session: Session,
        filters: SearchSourcesFilters = SearchSourcesFilters(),
        order_by: Optional[SearchSourcesOrderByEnum] = None
    ):
        self._db_session = db_session
        self._filters = filters

    def create_query(self):
        query = self._db_session.query(models.Source).filter(
            # Never return deleted sources via this action
            models.Source.deleted_at.is_(None),
        )

        if self._filters.filter_by_is_pending is not None:
            query = query.filter_by(pending=self._filters.filter_by_is_pending)

        if self._filters.filter_by_is_starred is not None:
            query = query.filter(models.Source.is_starred == self._filters.filter_by_is_starred)

        if self._filters.filter_by_was_updated_after is not None:
            query = query.filter(models.Source.last_updated > self._filters.filter_by_was_updated_after)

        return query

    def perform(self, paginate_results_with_config: Optional[PaginationConfig] = None):
        query = self.create_query()
        if paginate_results_with_config:
            # TODO:
            pass

        return query.all()


# TODO
class GetSingleSourceAction:
    def __init__(
        self,
        db_session: Session,
        uuid,
        filesystem_id,
    ):
        if uuid and filesystem_id:
            raise ValueError("Can only specify one of uuid and filesystem_id")


class DeleteSourcesAction:
    pass
