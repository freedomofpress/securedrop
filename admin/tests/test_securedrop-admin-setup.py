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
import pytest
import subprocess

import bootstrap


class TestSecureDropAdmin(object):

    def test_verbose(self, capsys):
        bootstrap.setup_logger(verbose=True)
        bootstrap.sdlog.debug('VISIBLE')
        out, err = capsys.readouterr()
        assert 'VISIBLE' in out

    def test_not_verbose(self, capsys):
        bootstrap.setup_logger(verbose=False)
        bootstrap.sdlog.debug('HIDDEN')
        bootstrap.sdlog.info('VISIBLE')
        out, err = capsys.readouterr()
        assert 'HIDDEN' not in out
        assert 'VISIBLE' in out

    def test_run_command(self):
        for output_line in bootstrap.run_command(
                ['/bin/echo', 'something']):
            assert output_line.strip() == b'something'

        lines = []
        with pytest.raises(subprocess.CalledProcessError):
            for output_line in bootstrap.run_command(
                    ['sh', '-c',
                     'echo in stdout ; echo in stderr >&2 ; false']):
                lines.append(output_line.strip())
        assert lines[0] == b'in stdout'
        assert lines[1] == b'in stderr'

    def test_install_pip_dependencies_up_to_date(self, caplog):
        args = argparse.Namespace()
        bootstrap.install_pip_dependencies(args, ['/bin/echo'])
        assert 'securedrop-admin are up-to-date' in caplog.text

    def test_install_pip_dependencies_upgraded(self, caplog):
        args = argparse.Namespace()
        bootstrap.install_pip_dependencies(
            args, ['/bin/echo', 'Successfully installed'])
        assert 'securedrop-admin upgraded' in caplog.text

    def test_install_pip_dependencies_fail(self, caplog):
        args = argparse.Namespace()
        with pytest.raises(subprocess.CalledProcessError):
            bootstrap.install_pip_dependencies(
                args, ['/bin/sh', '-c',
                       'echo in stdout ; echo in stderr >&2 ; false'])
        assert 'Failed to install' in caplog.text
        assert 'in stdout' in caplog.text
        assert 'in stderr' in caplog.text
