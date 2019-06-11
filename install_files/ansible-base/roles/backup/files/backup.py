#!/usr/bin/python2.7
"""
This script is copied to the App server and run by the Ansible playbook. When
run (as root), it collects all of the necessary information to backup the 0.3
system and stores it in /tmp/sd-backup-0.3-TIME_STAMP.tar.gz.
"""

from datetime import datetime
import os
import tarfile


def main():
    backup_filename = 'sd-backup-{}.tar.gz'.format(
        datetime.utcnow().strftime("%Y-%m-%d--%H-%M-%S"))

    # This code assumes everything is in the default locations.
    sd_data = '/var/lib/securedrop'

    sd_code = '/var/www/securedrop'
    sd_config = os.path.join(sd_code, "config.py")
    sd_custom_logo = os.path.join(sd_code, "static/i/logo.png")

    tor_hidden_services = "/var/lib/tor/services"
    torrc = "/etc/tor/torrc"

    with tarfile.open(backup_filename, 'w:gz') as backup:
        backup.add(sd_config)
        backup.add(sd_custom_logo)
        backup.add(sd_data)
        backup.add(tor_hidden_services)
        backup.add(torrc)

    print(backup_filename)


if __name__ == "__main__":
    main()
