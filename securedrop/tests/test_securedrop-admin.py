# -*- coding: utf-8 -*-
#
# SecureDrop whistleblower submission system
# Copyright (C) 2017 Loic Dachary <loic@dachary.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import argparse
import imp
from os.path import abspath, dirname, join, realpath
import pytest
import subprocess

here = abspath(join(dirname(realpath(__file__))))
securedrop_admin = imp.load_source('sa', here + '/../securedrop-admin')


class TestSecureDropAdmin(object):

    def test_verbose(self, capsys):
        securedrop_admin.setup_logger(verbose=True)
        securedrop_admin.sdlog.debug('VISIBLE')
        out, err = capsys.readouterr()
        assert 'VISIBLE' in out

    def test_not_verbose(self, capsys):
        securedrop_admin.setup_logger(verbose=False)
        securedrop_admin.sdlog.debug('HIDDEN')
        securedrop_admin.sdlog.info('VISIBLE')
        out, err = capsys.readouterr()
        assert 'HIDDEN' not in out
        assert 'VISIBLE' in out
