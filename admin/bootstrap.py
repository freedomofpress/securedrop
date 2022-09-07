# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2013-2018 Freedom of the Press Foundation & al
# Copyright (C) 2018 Loic Dachary <loic@dachary.org>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import argparse
import logging
import os
import shutil
import subprocess
import sys
from typing import Iterator, List

sdlog = logging.getLogger(__name__)

DIR = os.path.dirname(os.path.realpath(__file__))
VENV_DIR = os.path.join(DIR, ".venv3")


def setup_logger(verbose: bool = False) -> None:
    """Configure logging handler"""
    # Set default level on parent
    sdlog.setLevel(logging.DEBUG)
    level = logging.DEBUG if verbose else logging.INFO

    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    stdout.setLevel(level)
    sdlog.addHandler(stdout)


def run_command(command: List[str]) -> Iterator[bytes]:
    """
    Wrapper function to display stdout for running command,
    similar to how shelling out in a Bash script displays rolling output.

    Yields a list of the stdout from the `command`, and raises a
    CalledProcessError if `command` returns non-zero.
    """
    popen = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if popen.stdout is None:
        raise EnvironmentError("Could not run command: None stdout")
    for stdout_line in iter(popen.stdout.readline, b""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)


def is_tails() -> bool:
    with open("/etc/os-release") as f:
        return "TAILS_PRODUCT_NAME" in f.read()


def clean_up_old_tails_venv(virtualenv_dir: str = VENV_DIR) -> None:
    """
    When upgrading major Tails versions, we need to rebuild the virtualenv
    against the correct Python version. We can detect if the Tails
    version matches the correct Python version - if not, delete the
    venv, so it'll get recreated.
    """
    if is_tails():
        with open("/etc/os-release") as f:
            os_release = f.readlines()
            for line in os_release:
                if line.startswith("TAILS_VERSION_ID="):
                    version = line.split("=")[1].strip().strip('"')
                    if version.startswith("5."):
                        # Tails 5 is based on Python 3.9
                        python_lib_path = os.path.join(virtualenv_dir, "lib/python3.7")
                        if os.path.exists(python_lib_path):
                            sdlog.info("Tails 4 virtualenv detected. Removing it.")
                            shutil.rmtree(virtualenv_dir)
                            sdlog.info("Tails 4 virtualenv deleted.")
                    break


def checkenv(args: argparse.Namespace) -> None:
    clean_up_old_tails_venv(VENV_DIR)
    if not os.path.exists(os.path.join(VENV_DIR, "bin/activate")):
        sdlog.error('Please run "securedrop-admin setup".')
        sys.exit(1)


def maybe_torify() -> List[str]:
    if is_tails():
        return ["torify"]
    else:
        return []


def install_apt_dependencies(args: argparse.Namespace) -> None:
    """
    Install apt dependencies in Tails. In order to install Ansible in
    a virtualenv, first there are a number of Python prerequisites.
    """
    sdlog.info("Installing SecureDrop Admin dependencies")
    sdlog.info(
        (
            "You'll be prompted for the temporary Tails admin password,"
            " which was set on Tails login screen"
        )
    )

    apt_command = [
        "sudo",
        "su",
        "-c",
        "apt-get update && \
                   apt-get -q -o=Dpkg::Use-Pty=0 install -y \
                   python3-virtualenv \
                   python3-yaml \
                   python3-pip \
                   virtualenv \
                   libffi-dev \
                   libssl-dev \
                   libpython3-dev",
    ]

    try:
        # Print command results in real-time, to keep Admin apprised
        # of progress during long-running command.
        for output_line in run_command(apt_command):
            print(output_line.decode("utf-8").rstrip())
    except subprocess.CalledProcessError:
        # Tails supports apt persistence, which was used by SecureDrop
        # under Tails 2.x. If updates are being applied, don't try to pile
        # on with more apt requests.
        sdlog.error(
            ("Failed to install apt dependencies. Check network" " connection and try again.")
        )
        raise


def envsetup(args: argparse.Namespace, virtualenv_dir: str = VENV_DIR) -> None:
    """Installs Admin tooling required for managing SecureDrop. Specifically:

        * updates apt-cache
        * installs apt packages for Python virtualenv
        * creates virtualenv
        * installs pip packages inside virtualenv

    The virtualenv is created within the Persistence volume in Tails, so that
    Ansible is available to the Admin on subsequent boots without requiring
    installation of packages again.
    """
    # clean up old Tails venv on major upgrades
    clean_up_old_tails_venv(virtualenv_dir)

    # virtualenv doesnt exist? Install dependencies and create
    if not os.path.exists(virtualenv_dir):

        install_apt_dependencies(args)

        # Technically you can create a virtualenv from within python
        # but pip can only be run over Tor on Tails, and debugging that
        # along with instaling a third-party dependency is not worth
        # the effort here.
        sdlog.info("Setting up virtualenv")
        try:
            sdlog.debug(
                subprocess.check_output(
                    maybe_torify() + ["virtualenv", "--python=python3", virtualenv_dir],
                    stderr=subprocess.STDOUT,
                )
            )
        except subprocess.CalledProcessError as e:
            sdlog.debug(e.output)
            sdlog.error(("Unable to create virtualenv. Check network settings" " and try again."))
            sdlog.debug("Cleaning up virtualenv")
            if os.path.exists(virtualenv_dir):
                shutil.rmtree(virtualenv_dir)
            raise
    else:
        sdlog.info("Virtualenv already exists, not creating")

    if args.t:
        install_pip_dependencies(
            args,
            requirements_file="requirements-testinfra.txt",
            desc="dependencies with verification support",
        )
    else:
        install_pip_dependencies(args)

    if os.path.exists(os.path.join(DIR, "setup.py")):
        install_pip_self(args)

    sdlog.info("Finished installing SecureDrop dependencies")


def install_pip_self(args: argparse.Namespace) -> None:
    pip_install_cmd = [os.path.join(VENV_DIR, "bin", "pip3"), "install", "-e", DIR]
    try:
        subprocess.check_output(maybe_torify() + pip_install_cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        sdlog.debug(e.output)
        sdlog.error("Unable to install self, run with -v for more information")
        raise


def install_pip_dependencies(
    args: argparse.Namespace,
    requirements_file: str = "requirements.txt",
    desc: str = "Python dependencies",
) -> None:
    """
    Install Python dependencies via pip into virtualenv.
    """
    pip_install_cmd = [
        os.path.join(VENV_DIR, "bin", "pip3"),
        "install",
        "--no-deps",
        "-r",
        os.path.join(DIR, requirements_file),
        "--require-hashes",
        "-U",
        "--upgrade-strategy",
        "only-if-needed",
    ]

    sdlog.info("Checking {} for securedrop-admin".format(desc))
    try:
        pip_output = subprocess.check_output(
            maybe_torify() + pip_install_cmd, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        sdlog.debug(e.output)
        sdlog.error(
            ("Failed to install {}. Check network" " connection and try again.".format(desc))
        )
        raise

    sdlog.debug(pip_output)
    if "Successfully installed" in str(pip_output):
        sdlog.info("{} for securedrop-admin upgraded".format(desc))
    else:
        sdlog.info("{} for securedrop-admin are up-to-date".format(desc))


def parse_argv(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", action="store_true", default=False, help="Increase verbosity on output"
    )
    parser.add_argument(
        "-t", action="store_true", default=False, help="Install additional test dependencies"
    )
    parser.set_defaults(func=envsetup)

    subparsers = parser.add_subparsers()

    envsetup_parser = subparsers.add_parser("envsetup", help="Set up the admin virtualenv.")
    envsetup_parser.set_defaults(func=envsetup)

    checkenv_parser = subparsers.add_parser(
        "checkenv", help="Check that the admin virtualenv is properly set up."
    )
    checkenv_parser.set_defaults(func=checkenv)

    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_argv(sys.argv[1:])
    setup_logger(args.v)

    try:
        args.func(args)
    except Exception:
        sys.exit(1)
    else:
        sys.exit(0)
