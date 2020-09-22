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
                                     shell=True).decode('utf-8').strip()
    except subprocess.CalledProcessError:
        id = None

    # dirty hack to unreliably detect Tails 4.0~beta2
    if id == 'Debian':
        if os.uname()[1] == 'amnesia':
            id = 'Tails'

    return id == 'Tails'


def clean_up_tails3_venv(virtualenv_dir=VENV_DIR):
    """
    Tails 3.x, based on debian stretch uses libpython3.5, whereas Tails 4.x is
    based on Debian Buster and uses libpython3.7. This means that the Tails 3.x
    virtualenv will not work under Tails 4.x, and will need to be destroyed and
    rebuilt. We can detect if the version of libpython is 3.5 in the
    admin/.venv3/ folder, and delete it if that's the case. This will ensure a
    smooth upgrade from Tails 3.x to Tails 4.x.
    """
    if is_tails():
        try:
            dist = subprocess.check_output('lsb_release --codename --short',
                                           shell=True).strip()
        except subprocess.CalledProcessError:
            dist = None

        # tails4 is based on buster
        if dist == b'buster':
            python_lib_path = os.path.join(virtualenv_dir, "lib/python3.5")
            if os.path.exists(os.path.join(python_lib_path)):
                sdlog.info(
                    "Tails 3 Python 3 virtualenv detected. "
                    "Removing it."
                )
                shutil.rmtree(virtualenv_dir)
                sdlog.info("Tails 3 Python 3 virtualenv deleted.")


def checkenv(args):
    clean_up_tails3_venv(VENV_DIR)
    if not os.path.exists(os.path.join(VENV_DIR, "bin/activate")):
        sdlog.error('Please run "securedrop-admin setup".')
        sys.exit(1)


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
                   libpython3-dev",
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


def envsetup(args, virtualenv_dir=VENV_DIR):
    """Installs Admin tooling required for managing SecureDrop. Specifically:

        * updates apt-cache
        * installs apt packages for Python virtualenv
        * creates virtualenv
        * installs pip packages inside virtualenv

    The virtualenv is created within the Persistence volume in Tails, so that
    Ansible is available to the Admin on subsequent boots without requiring
    installation of packages again.
    """
    # clean up Tails 3.x venv when migrating to Tails 4.x
    clean_up_tails3_venv(virtualenv_dir)

    # virtualenv doesnt exist? Install dependencies and create
    if not os.path.exists(virtualenv_dir):

        install_apt_dependencies(args)

        # Technically you can create a virtualenv from within python
        # but pip can only be run over Tor on Tails, and debugging that
        # along with instaling a third-party dependency is not worth
        # the effort here.
        sdlog.info("Setting up virtualenv")
        try:
            sdlog.debug(subprocess.check_output(
                maybe_torify() + ['virtualenv',
                                  '--python=python3',
                                  virtualenv_dir
                                  ],
                stderr=subprocess.STDOUT))
        except subprocess.CalledProcessError as e:
            sdlog.debug(e.output)
            sdlog.error(("Unable to create virtualenv. Check network settings"
                         " and try again."))
            sdlog.debug("Cleaning up virtualenv")
            if os.path.exists(virtualenv_dir):
                shutil.rmtree(virtualenv_dir)
            raise
    else:
        sdlog.info("Virtualenv already exists, not creating")

    if args.t:
        install_pip_dependencies(args, pip_install_cmd=[
            os.path.join(VENV_DIR, 'bin', 'pip3'),
            'install',
            '--no-deps',
            '-r', os.path.join(DIR, 'requirements-testinfra.txt'),
            '--require-hashes',
            '-U', '--upgrade-strategy', 'only-if-needed', ],
            desc="dependencies with verification support")
    else:
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
        '--no-deps',
        # Specify requirements file.
        '-r', os.path.join(DIR, 'requirements.txt'),
        '--require-hashes',
        # Make sure to upgrade packages only if necessary.
        '-U', '--upgrade-strategy', 'only-if-needed', ],
        desc="Python dependencies"
):
    """
    Install Python dependencies via pip into virtualenv.
    """

    sdlog.info("Checking {} for securedrop-admin".format(desc))
    try:
        pip_output = subprocess.check_output(maybe_torify() + pip_install_cmd,
                                             stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        sdlog.debug(e.output)
        sdlog.error(("Failed to install {}. Check network"
                     " connection and try again.".format(desc)))
        raise

    sdlog.debug(pip_output)
    if "Successfully installed" in str(pip_output):
        sdlog.info("{} for securedrop-admin upgraded".format(desc))
    else:
        sdlog.info("{} for securedrop-admin are up-to-date".format(desc))


def parse_argv(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', default=False,
                        help="Increase verbosity on output")
    parser.add_argument('-t', action='store_true', default=False,
                        help="Install additional test dependencies")
    parser.set_defaults(func=envsetup)

    subparsers = parser.add_subparsers()

    envsetup_parser = subparsers.add_parser(
        'envsetup',
        help='Set up the admin virtualenv.'
    )
    envsetup_parser.set_defaults(func=envsetup)

    checkenv_parser = subparsers.add_parser(
        'checkenv',
        help='Check that the admin virtualenv is properly set up.'
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
