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

from __future__ import absolute_import

from . import gnupg
from . import copyleft
from . import _ansistrm
from . import _logger
from . import _meta
from . import _parsers
from . import _util
from .gnupg import GPG
from ._version import get_versions

__version__ = get_versions()['version']
__authors__ = copyleft.authors
__license__ = copyleft.full_text
__copyleft__ = copyleft.copyright

gnupg.__version__ = __version__
gnupg.__authors__ = __authors__
gnupg.__licence__ = __license__
gnupg.__copyleft__ = __copyleft__

gnupg._logger = _logger
gnupg._meta = _meta
gnupg._parsers = _parsers
gnupg._util = _util

## do not set __package__ = "gnupg", else we will end up with
## gnupg.<*allofthethings*>
__all__ = ["GPG", "_util", "_parsers", "_meta", "_logger"]

del absolute_import
del copyleft
del get_versions
del _version
