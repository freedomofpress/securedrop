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
import errno
import logging
import os
import subprocess


def shred(path, delete=True):
    # type: (str, bool) -> None
    """
    Run shred on the file at the given path.

    Args:
        path (str): The path to the file to shred.
        delete (bool): Whether to unlink the file after shredding.

    Returns:
        None

    Raises:
        subprocess.CalledProcessError: If shred's return code is not zero.
        EnvironmentError: If shred is not available.
    """

    if not os.path.exists(path):
        raise EnvironmentError(path)

    if not os.path.isfile(path):
        raise ValueError("The shred function only works on files.")
    cmd = ["shred", "-z", "-n", "30"]
    if delete:
        cmd.append("-u")
    cmd.append(path)
    subprocess.check_call(cmd)


def secure_delete(path):
    # type: (str) -> None
    """
    Securely deletes the file at ``path``.

    Args:
        path (str): The path to the file to delete.

    Returns:
        str: A string signaling success to rq.

    Raises:
        subprocess.CalledProcessError: If shred's return code is not zero.
        EnvironmentError: If shred is not available.
    """
    path = os.path.abspath(path)

    directories = []
    targets = []
    if not os.path.isdir(path):
        targets.append(path)
    else:
        for directory, subdirs, files in os.walk(path):
            directories.append(directory)
            directories.extend([os.path.abspath(os.path.join(directory, s)) for s in subdirs])
            for f in files:
                targets.append(os.path.abspath(os.path.join(directory, f)))

    for t in targets:
        shred(t)

    directories_to_remove = set(directories)
    for d in reversed(sorted(directories_to_remove)):
        os.rmdir(d)


def check_secure_delete_capability():
    # type: () -> bool
    """
    Checks the availability of the program we use for secure deletion.

    Returns:
        bool: True if the program is available, otherwise False.
    """
    try:
        subprocess.check_output(["shred", "--help"])
        return True
    except EnvironmentError as e:
        if e.errno != errno.ENOENT:
            raise
        logging.error("The shred utility is missing.")
    except subprocess.CalledProcessError as e:
        logging.error("The shred utility is broken: %s %s", e, e.output)
    return False
