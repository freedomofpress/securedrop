#!/usr/bin/python2.7
"""
This script is copied to the Mon server and run by the Ansible playbook. When
run (as root), it collects all of the necessary information to backup the 0.3
system and stores it in /tmp/sd-backup-mon-0.3-TIME_STAMP.tar.gz.
"""

from datetime import datetime
import os
import tarfile

def main():
    backup_filename = 'sd-mon-backup-{}.tar.gz'.format(
        datetime.utcnow().strftime("%Y-%m-%d--%H-%M-%S"))

    # This code assumes everything is in the default locations.
    authenticated_tor_hidden_service = "/var/lib/tor/services/ssh"
    torrc = "/etc/tor/torrc"

    with tarfile.open(backup_filename, 'w:gz') as backup:
        backup.add(authenticated_tor_hidden_service)
        backup.add(torrc)

    print backup_filename

if __name__ == "__main__":
    main()
