from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Query


@dataclass(frozen=True)
class PaginationConfig:
    page_size: int
    page_number: int

    def __post_init__(self) -> None:
        if self.page_size < 0:
            raise ValueError("Received a negative page_size")
        if self.page_number < 0:
            raise ValueError("Received a negative page_number")


class SupportsPagination(ABC):

    @abstractmethod
    def create_query(self) -> Query:
        pass

    @abstractmethod
    def perform(self, paginate_results_with_config: Optional[PaginationConfig] = None):
        pass
