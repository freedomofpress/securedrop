import logging

import pytest
from sdlog import SanitizingFilter, sanitize_control_chars


def test_sanitize_control_chars_escapes_newlines_and_control_characters():
    assert sanitize_control_chars("foo\nbar\rbaz\x00\x7f") == "foo\\x0abar\\x0dbaz\\x00\\x7f"
    assert sanitize_control_chars("/totally/normal") == "/totally/normal"


def test_sanitizing_filter_escapes_rendered_message():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Login for '%s' failed",
        args=("evil\nuser",),
        exc_info=None,
    )

    assert SanitizingFilter().filter(record) is True
    assert record.getMessage() == "Login for 'evil\\x0auser' failed"
    # The message must not contain a raw newline once rendered
    assert "\n" not in record.getMessage()


def test_sanitizing_filter_leaves_clean_records_untouched():
    msg = "a clean %s message"
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=("clean",),
        exc_info=None,
    )

    assert SanitizingFilter().filter(record) is True
    # msg/args are preserved so handlers still do %-formatting
    assert record.msg == msg
    assert record.args == ("clean",)
    assert record.getMessage() == "a clean clean message"


@pytest.mark.parametrize(
    "evil",
    [
        "username\nWARNING forged log line",
        "username\r\nWARNING forged log line",
        "user\x00name",
    ],
)
def test_sanitizing_filter_blocks_end_to_end(evil):
    logger = logging.getLogger("test_sanitizing_filter")
    logger.setLevel(logging.INFO)
    records = []

    class CapturingHandler(logging.NullHandler):
        def emit(self, record):
            records.append(record)

    handler = CapturingHandler()
    logger.addHandler(handler)
    logger.addFilter(SanitizingFilter())
    try:
        logger.info("Login for '%s' failed", evil)
    finally:
        logger.removeHandler(handler)
        logger.removeFilter(SanitizingFilter())

    assert len(records) == 1
    message = records[0].getMessage()
    assert "\n" not in message
    assert "\r" not in message
    assert "\x00" not in message
    assert "forged" in message  # content preserved, just escaped
