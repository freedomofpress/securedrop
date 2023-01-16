from itertools import count
from logging import Logger
from typing import Callable

from jinja2.runtime import Context
from jinja2.utils import pass_context


def create_get_descriptive_title_function(logger: Logger) -> Callable[[], str]:
    @pass_context
    def get_descriptive_title(context: Context) -> str:
        for block_func in context.blocks["body"]:
            block = list(block_func(context))
            for (possibly_h1_tag, next_index) in zip(block, count(1)):
                if "<h1" in possibly_h1_tag:
                    return block[next_index]

        logger.error(f"No h1 block found on page {context.name}, returning empty string!")
        return ""

    # The mypy ignore is because the pass_context decorator passes in the context automatically,
    # so the type hint is correct but mypy doesn't understand this. The noqa is because flake6
    # throws an error when the mypy ignore specifies the error code.
    return get_descriptive_title  # type: ignore [return-value] # noqa: F723
