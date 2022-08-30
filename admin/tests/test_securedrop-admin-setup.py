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
import os
import subprocess

import bootstrap
import mock
import pytest


class TestSecureDropAdmin(object):
    def test_verbose(self, capsys):
        bootstrap.setup_logger(verbose=True)
        bootstrap.sdlog.debug("VISIBLE")
        out, err = capsys.readouterr()
        assert "VISIBLE" in out

    def test_not_verbose(self, capsys):
        bootstrap.setup_logger(verbose=False)
        bootstrap.sdlog.debug("HIDDEN")
        bootstrap.sdlog.info("VISIBLE")
        out, err = capsys.readouterr()
        assert "HIDDEN" not in out
        assert "VISIBLE" in out

    def test_run_command(self):
        for output_line in bootstrap.run_command(["/bin/echo", "something"]):
            assert output_line.strip() == b"something"

        lines = []
        with pytest.raises(subprocess.CalledProcessError):
            for output_line in bootstrap.run_command(
                ["sh", "-c", "echo in stdout ; echo in stderr >&2 ; false"]
            ):
                lines.append(output_line.strip())
        assert lines[0] == b"in stdout"
        assert lines[1] == b"in stderr"

    def test_install_pip_dependencies_up_to_date(self, caplog):
        args = argparse.Namespace()
        with mock.patch.object(subprocess, "check_output", return_value=b"up to date"):
            bootstrap.install_pip_dependencies(args)
        assert "securedrop-admin are up-to-date" in caplog.text

    def test_install_pip_dependencies_upgraded(self, caplog):
        args = argparse.Namespace()
        with mock.patch.object(subprocess, "check_output", return_value=b"Successfully installed"):
            bootstrap.install_pip_dependencies(args)
        assert "securedrop-admin upgraded" in caplog.text

    def test_install_pip_dependencies_fail(self, caplog):
        args = argparse.Namespace()
        with mock.patch.object(
            subprocess,
            "check_output",
            side_effect=subprocess.CalledProcessError(returncode=2, cmd="", output=b"failed"),
        ):
            with pytest.raises(subprocess.CalledProcessError):
                bootstrap.install_pip_dependencies(args)
        assert "Failed to install" in caplog.text

    def test_python3_buster_venv_deleted_in_bullseye(self, tmpdir, caplog):
        venv_path = str(tmpdir)
        python_lib_path = os.path.join(str(tmpdir), "lib/python3.7")
        os.makedirs(python_lib_path)
        with mock.patch("bootstrap.is_tails", return_value=True):
            with mock.patch("builtins.open", mock.mock_open(read_data='TAILS_VERSION_ID="5.0"')):
                bootstrap.clean_up_old_tails_venv(venv_path)
                assert "Tails 4 virtualenv detected." in caplog.text
                assert "Tails 4 virtualenv deleted." in caplog.text
                assert not os.path.exists(venv_path)

    def test_python3_bullseye_venv_not_deleted_in_bullseye(self, tmpdir, caplog):
        venv_path = str(tmpdir)
        python_lib_path = os.path.join(venv_path, "lib/python3.9")
        os.makedirs(python_lib_path)
        with mock.patch("bootstrap.is_tails", return_value=True):
            with mock.patch("subprocess.check_output", return_value="bullseye"):
                bootstrap.clean_up_old_tails_venv(venv_path)
                assert "Tails 4 virtualenv detected" not in caplog.text
                assert os.path.exists(venv_path)

    def test_python3_buster_venv_not_deleted_in_buster(self, tmpdir, caplog):
        venv_path = str(tmpdir)
        python_lib_path = os.path.join(venv_path, "lib/python3.7")
        os.makedirs(python_lib_path)
        with mock.patch("bootstrap.is_tails", return_value=True):
            with mock.patch("subprocess.check_output", return_value="buster"):
                bootstrap.clean_up_old_tails_venv(venv_path)
                assert os.path.exists(venv_path)

    def test_venv_cleanup_subprocess_exception(self, tmpdir, caplog):
        venv_path = str(tmpdir)
        python_lib_path = os.path.join(venv_path, "lib/python3.7")
        os.makedirs(python_lib_path)
        with mock.patch("bootstrap.is_tails", return_value=True):
            with mock.patch(
                "subprocess.check_output", side_effect=subprocess.CalledProcessError(1, ":o")
            ):
                bootstrap.clean_up_old_tails_venv(venv_path)
                assert os.path.exists(venv_path)

    def test_envsetup_cleanup(self, tmpdir, caplog):
        venv = os.path.join(str(tmpdir), "empty_dir")
        args = ""
        with pytest.raises(subprocess.CalledProcessError):
            with mock.patch(
                "subprocess.check_output", side_effect=self.side_effect_venv_bootstrap(venv)
            ):
                bootstrap.envsetup(args, venv)
                assert not os.path.exists(venv)
                assert "Cleaning up virtualenv" in caplog.text

    def side_effect_venv_bootstrap(self, venv_path):
        # emulate the venv being created, and raise exception to simulate
        # failure in virtualenv creation
        os.makedirs(venv_path)
        raise subprocess.CalledProcessError(1, ":o")
