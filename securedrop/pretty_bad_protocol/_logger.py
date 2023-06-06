#
# This file is part of python-gnupg, a Python interface to GnuPG.
# Copyright © 2013 Isis Lovecruft, <isis@leap.se> 0xA3ADB67A2CDB8B35
#           © 2013 Andrej B.
#           © 2013 LEAP Encryption Access Project
#           © 2008-2012 Vinay Sajip
#           © 2005 Steve Traugott
#           © 2004 A.M. Kuchling
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the included LICENSE file for details.

"""Logging module for python-gnupg."""

import logging
from datetime import datetime
from functools import wraps
from logging import NullHandler

GNUPG_STATUS_LEVEL = 9


def status(self, message, *args, **kwargs):
    """LogRecord for GnuPG internal status messages."""
    if self.isEnabledFor(GNUPG_STATUS_LEVEL):
        self._log(GNUPG_STATUS_LEVEL, message, args, **kwargs)


@wraps(logging.Logger)
def create_logger(level=logging.NOTSET):
    """Create a logger for python-gnupg at a specific message level.

    :type level: :obj:`int` or :obj:`str`
    :param level: A string or an integer for the lowest level to include in
                  logs.

    **Available levels:**

    ==== ======== ========================================
    int   str     description
    ==== ======== ========================================
    0    NOTSET   Disable all logging.
    9    GNUPG    Log GnuPG's internal status messages.
    10   DEBUG    Log module level debuging messages.
    20   INFO     Normal user-level messages.
    30   WARN     Warning messages.
    40   ERROR    Error messages and tracebacks.
    50   CRITICAL Unhandled exceptions and tracebacks.
    ==== ======== ========================================
    """
    # Add the GNUPG_STATUS_LEVEL LogRecord to all Loggers in the module:
    logging.addLevelName(GNUPG_STATUS_LEVEL, "GNUPG")
    logging.Logger.status = status

    handler = NullHandler()

    log = logging.getLogger("gnupg")
    log.addHandler(handler)
    log.setLevel(level)
    log.info("Log opened: %s UTC" % datetime.ctime(datetime.utcnow()))
    return log
