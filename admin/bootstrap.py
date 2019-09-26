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
import subprocess
import sys

sdlog = logging.getLogger(__name__)

DIR = os.path.dirname(os.path.realpath(__file__))
VENV_DIR = os.path.join(DIR, ".venv3")


def setup_logger(verbose=False):
    """ Configure logging handler """
    # Set default level on parent
    sdlog.setLevel(logging.DEBUG)
    level = logging.DEBUG if verbose else logging.INFO

    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    stdout.setLevel(level)
    sdlog.addHandler(stdout)


def run_command(command):
    """
    Wrapper function to display stdout for running command,
    similar to how shelling out in a Bash script displays rolling output.

    Yields a list of the stdout from the `command`, and raises a
    CalledProcessError if `command` returns non-zero.
    """
    popen = subprocess.Popen(command,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    for stdout_line in iter(popen.stdout.readline, b""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)


def is_tails():
    try:
        id = subprocess.check_output('lsb_release --id --short',
                                     shell=True).strip()
    except subprocess.CalledProcessError:
        id = None

    # dirty hack to unreliably detect Tails 4.0~beta2
    if id == 'Debian':
        if os.uname()[1] == 'amnesia':
            id = 'Tails'

    return id == 'Tails'


def maybe_torify():
    if is_tails():
        return ['torify']
    else:
        return []


def install_apt_dependencies(args):
    """
    Install apt dependencies in Tails. In order to install Ansible in
    a virtualenv, first there are a number of Python prerequisites.
    """
    sdlog.info("Installing SecureDrop Admin dependencies")
    sdlog.info(("You'll be prompted for the temporary Tails admin password,"
                " which was set on Tails login screen"))

    apt_command = ['sudo', 'su', '-c',
                   "apt-get update && \
                   apt-get -q -o=Dpkg::Use-Pty=0 install -y \
                   python3-virtualenv \
                   python3-yaml \
                   python3-pip \
                   ccontrol \
                   virtualenv \
                   libffi-dev \
                   libssl-dev \
                   libpython3.5-dev",
                   ]

    try:
        # Print command results in real-time, to keep Admin apprised
        # of progress during long-running command.
        for output_line in run_command(apt_command):
            print(output_line.decode('utf-8').rstrip())
    except subprocess.CalledProcessError:
        # Tails supports apt persistence, which was used by SecureDrop
        # under Tails 2.x. If updates are being applied, don't try to pile
        # on with more apt requests.
        sdlog.error(("Failed to install apt dependencies. Check network"
                     " connection and try again."))
        raise


def envsetup(args):
    """Installs Admin tooling required for managing SecureDrop. Specifically:

        * updates apt-cache
        * installs apt packages for Python virtualenv
        * creates virtualenv
        * installs pip packages inside virtualenv

    The virtualenv is created within the Persistence volume in Tails, so that
    Ansible is available to the Admin on subsequent boots without requiring
    installation of packages again.
    """
    # virtualenv doesnt exist? Install dependencies and create
    if not os.path.exists(VENV_DIR):

        install_apt_dependencies(args)

        # Technically you can create a virtualenv from within python
        # but pip can only be run over tor on tails, and debugging that
        # along with instaling a third-party dependency is not worth
        # the effort here.
        sdlog.info("Setting up virtualenv")
        try:
            sdlog.debug(subprocess.check_output(
                maybe_torify() + ['virtualenv', '--python=python3', VENV_DIR],
                stderr=subprocess.STDOUT))
        except subprocess.CalledProcessError as e:
            sdlog.debug(e.output)
            sdlog.error(("Unable to create virtualenv. Check network settings"
                         " and try again."))
            raise
    else:
        sdlog.info("Virtualenv already exists, not creating")

    install_pip_dependencies(args)
    if os.path.exists(os.path.join(DIR, 'setup.py')):
        install_pip_self(args)

    sdlog.info("Finished installing SecureDrop dependencies")


def install_pip_self(args):
    pip_install_cmd = [
        os.path.join(VENV_DIR, 'bin', 'pip3'),
        'install', '-e', DIR
    ]
    try:
        subprocess.check_output(maybe_torify() + pip_install_cmd,
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        sdlog.debug(e.output)
        sdlog.error("Unable to install self, run with -v for more information")
        raise


def install_pip_dependencies(args, pip_install_cmd=[
        os.path.join(VENV_DIR, 'bin', 'pip3'),
        'install',
        # Specify requirements file.
        '-r', os.path.join(DIR, 'requirements.txt'),
        '--require-hashes',
        # Make sure to upgrade packages only if necessary.
        '-U', '--upgrade-strategy', 'only-if-needed',
]):
    """
    Install Python dependencies via pip into virtualenv.
    """

    sdlog.info("Checking Python dependencies for securedrop-admin")
    try:
        pip_output = subprocess.check_output(maybe_torify() + pip_install_cmd,
                                             stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        sdlog.debug(e.output)
        sdlog.error(("Failed to install pip dependencies. Check network"
                     " connection and try again."))
        raise

    sdlog.debug(pip_output)
    if "Successfully installed" in str(pip_output):
        sdlog.info("Python dependencies for securedrop-admin upgraded")
    else:
        sdlog.info("Python dependencies for securedrop-admin are up-to-date")


def parse_argv(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', default=False,
                        help="Increase verbosity on output")
    parser.set_defaults(func=envsetup)

    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_argv(sys.argv[1:])
    setup_logger(args.v)
    if args.v:
        args.func(args)
    else:
        try:
            args.func(args)
        except Exception:
            sys.exit(1)
        else:
            sys.exit(0)
