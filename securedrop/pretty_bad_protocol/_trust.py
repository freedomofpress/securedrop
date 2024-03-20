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

"""Functions for handling trustdb and trust calculations.

The functions within this module take an instance of :class:`gnupg.GPGBase` or
a suitable subclass as their first argument.
"""


import os

from . import _util
from ._util import log


def _create_trustdb(cls):  # type: ignore[no-untyped-def]
    """Create the trustdb file in our homedir, if it doesn't exist."""
    trustdb = os.path.join(cls.homedir, "trustdb.gpg")
    if not os.path.isfile(trustdb):
        log.info(
            "GnuPG complained that your trustdb file was missing. {}".format(
                "This is likely due to changing to a new homedir."
            )
        )
        log.info("Creating trustdb.gpg file in your GnuPG homedir.")
        cls.fix_trustdb(trustdb)


def fix_trustdb(cls, trustdb=None):  # type: ignore[no-untyped-def]
    """Attempt to repair a broken trustdb.gpg file.

    GnuPG>=2.0.x has this magical-seeming flag: `--fix-trustdb`. You'd think
    it would fix the the trustdb. Hah! It doesn't. Here's what it does
    instead::

      (gpg)~/code/python-gnupg $ gpg2 --fix-trustdb
      gpg: You may try to re-create the trustdb using the commands:
      gpg:   cd ~/.gnupg
      gpg:   gpg2 --export-ownertrust > otrust.tmp
      gpg:   rm trustdb.gpg
      gpg:   gpg2 --import-ownertrust < otrust.tmp
      gpg: If that does not work, please consult the manual

    Brilliant piece of software engineering right there.

    :param str trustdb: The path to the trustdb.gpg file. If not given,
                        defaults to :file:`trustdb.gpg` in the current GnuPG
                        homedir.
    """
    if trustdb is None:
        trustdb = os.path.join(cls.homedir, "trustdb.gpg")
    export_proc = cls._open_subprocess(["--export-ownertrust"])
    import_proc = cls._open_subprocess(["--import-ownertrust"])
    _util._threaded_copy_data(export_proc.stdout, import_proc.stdin)
    export_proc.wait()
    import_proc.wait()
