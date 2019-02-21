#!/usr/bin/python2.7
"""
This script and backup archive should be copied to the App server and run by
the Ansible playbook. When run (as root), it restores the contents of the 0.3
backup file to the machine it's run on.

python restore.py sd-backup-TIMESTAMP.tar.gz
"""

import os
import subprocess
import sys
import tarfile


def verify_args():
    usage = """
Usage: restore.py <backup file>

    <backup file>  Path to a SecureDrop 0.3 backup created by backup.py"
    """
    if len(sys.argv) != 2:
        print(usage)
        sys.exit(1)

    if not os.path.exists(sys.argv[1]):
        print("<backup file> '{}' not found".format(sys.argv[1]))
        sys.exit(1)

    if os.geteuid() != 0:
        print("This program must be run as root!")
        sys.exit(1)


def main():
    verify_args()

    with tarfile.open(sys.argv[1], 'r:*') as backup:
        # This assumes that both the old installation (source of the backup)
        # and the new installation (destination of the restore) used the
        # default paths for various locations.
        backup.extractall(path='/')

    # Apply database migrations (if backed-up version < version to restore)
    subprocess.check_call(['dpkg-reconfigure', 'securedrop-app-code'])

    # Update the configs
    subprocess.check_call(['dpkg-reconfigure', 'securedrop-config'])

    # Reload Tor and the web server so they pick up the new configuration
    # If the process exits with a non-zero return code, raises an exception.
    subprocess.check_call(['service', 'apache2', 'restart'])
    subprocess.check_call(['service', 'tor', 'reload'])


if __name__ == "__main__":
    main()
