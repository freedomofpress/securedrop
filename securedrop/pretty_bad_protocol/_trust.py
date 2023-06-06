# -*- coding: utf-8 -*-
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

'''Functions for handling trustdb and trust calculations.

The functions within this module take an instance of :class:`gnupg.GPGBase` or
a suitable subclass as their first argument.
'''

from __future__ import absolute_import

import os

from .      import _util
from ._util import log

def _create_trustdb(cls):
    """Create the trustdb file in our homedir, if it doesn't exist."""
    trustdb = os.path.join(cls.homedir, 'trustdb.gpg')
    if not os.path.isfile(trustdb):
        log.info("GnuPG complained that your trustdb file was missing. %s"
                 % "This is likely due to changing to a new homedir.")
        log.info("Creating trustdb.gpg file in your GnuPG homedir.")
        cls.fix_trustdb(trustdb)

def export_ownertrust(cls, trustdb=None):
    """Export ownertrust to a trustdb file.

    If there is already a file named :file:`trustdb.gpg` in the current GnuPG
    homedir, it will be renamed to :file:`trustdb.gpg.bak`.

    :param string trustdb: The path to the trustdb.gpg file. If not given,
                           defaults to ``'trustdb.gpg'`` in the current GnuPG
                           homedir.
    """
    if trustdb is None:
        trustdb = os.path.join(cls.homedir, 'trustdb.gpg')

    try:
        os.rename(trustdb, trustdb + '.bak')
    except (OSError, IOError) as err:
        log.debug(str(err))

    export_proc = cls._open_subprocess(['--export-ownertrust'])
    tdb = open(trustdb, 'wb')
    _util._threaded_copy_data(export_proc.stdout, tdb)
    export_proc.wait()

def import_ownertrust(cls, trustdb=None):
    """Import ownertrust from a trustdb file.

    :param str trustdb: The path to the trustdb.gpg file. If not given,
                        defaults to :file:`trustdb.gpg` in the current GnuPG
                        homedir.
    """
    if trustdb is None:
        trustdb = os.path.join(cls.homedir, 'trustdb.gpg')

    import_proc = cls._open_subprocess(['--import-ownertrust'])

    try:
        tdb = open(trustdb, 'rb')
    except (OSError, IOError):
        log.error("trustdb file %s does not exist!" % trustdb)

    _util._threaded_copy_data(tdb, import_proc.stdin)
    import_proc.wait()

def fix_trustdb(cls, trustdb=None):
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
        trustdb = os.path.join(cls.homedir, 'trustdb.gpg')
    export_proc = cls._open_subprocess(['--export-ownertrust'])
    import_proc = cls._open_subprocess(['--import-ownertrust'])
    _util._threaded_copy_data(export_proc.stdout, import_proc.stdin)
    export_proc.wait()
    import_proc.wait()
