from typing import Any, List

import pytest
from utils import create_get_descriptive_title_function


class FakeContext:
    def __init__(self, h1_text: str, expected_result: Any):
        self.blocks = {
            "body": [
                lambda _: [h1_text, expected_result],
            ]
        }

        self.name = self.__class__.__name__


class FakeLogger:
    def __init__(self, failure_expected: bool):
        self.failure_expected = failure_expected

    def error(self, _: Any) -> None:
        assert self.failure_expected


def add_attribute(heading: str) -> str:
    index = heading.find(">")
    return heading[:index] + ' key = "value"' + heading[index:]


def heading_examples() -> List[str]:
    simple_heading_examples = [
        "<h1>",  # simplest exact match
        " <h1>",  # leading blankspace
        "<h1> ",  # trailing blankspace
        " <h1> ",  # leading and trailing blankspace
    ]

    attributed_heading_examples = [add_attribute(example) for example in simple_heading_examples]

    return simple_heading_examples + attributed_heading_examples


@pytest.mark.parametrize("heading_example", heading_examples())
def test_h1_block_is_found(heading_example: str) -> None:
    expected_result = "unique text is unique"
    context = FakeContext(heading_example, expected_result)
    get_descriptive_title = create_get_descriptive_title_function(FakeLogger(False))
    assert get_descriptive_title(context) == expected_result


def test_missing_tag_logs_error_and_returns_usable_value() -> None:
    context = FakeContext("Not a tag", "Not actually expected")
    get_descriptive_title = create_get_descriptive_title_function(FakeLogger(True))
    assert isinstance(get_descriptive_title(context), str)
