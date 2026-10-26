"""Shared logging helpers for the SecureDrop Flask applications.

These prevent log injection (splitting one log record into multiple forged
lines) by escaping control characters that originate in request-controlled
data such as usernames, form fields, and URL paths.
"""

import logging
import re

# WSGI PATH_INFO, form fields, and other request-derived values may contain
# arbitrary control characters; replace them with visible escapes so they
# can't split a log line.
_unsafe_char_re = re.compile(r"[\x00-\x1f\x7f]")


def sanitize_control_chars(value: str) -> str:
    """Return ``value`` with control characters replaced by visible escapes."""
    return _unsafe_char_re.sub(lambda c: f"\\x{ord(c.group()):02x}", value)


class SanitizingFilter(logging.Filter):
    """A ``logging.Filter`` that escapes control characters in the final,
    rendered message, so no log record emitted through this logger can be
    split into multiple lines by request-controlled data."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        sanitized = sanitize_control_chars(message)
        if sanitized != message:
            # Replacing msg/args means any later %-formatting by handlers is a
            # no-op (the message is already fully rendered and safe).
            record.msg = sanitized
            record.args = None
        return True
