from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Query


@dataclass(frozen=True)
class PaginationConfig:
    page_size: int
    page_number: int

    def __post_init__(self) -> None:
        if self.page_size < 1:
            raise ValueError("Received a page_size that's less than 1")
        if self.page_number < 0:
            raise ValueError("Received a page_number that's less than 0")


class SupportsPagination(ABC):

    @abstractmethod
    def create_query(self) -> Query:
        pass


    def perform(self, paginate_results_with_config: Optional[PaginationConfig] = None):
        query = self.create_query()

        if paginate_results_with_config:
            offset = paginate_results_with_config.page_size * paginate_results_with_config.page_number
            limit = paginate_results_with_config.page_size
            query = query.offset(offset).limit(limit).all()

        return query.all()
