#!/usr/bin/python2.7
"""
This script is copied to the App server and run by the Ansible playbook. When
run (as root), it collects all of the necessary information to backup the 0.3
system and stores it in /tmp/sd-backup-0.3-TIME_STAMP.tar.gz.
"""

from datetime import datetime
import os
import tarfile


def try_add(backup, file_path):
    try:
        backup.add(file_path)
    except OSError as e:
        if e.errno == 2:  # file not found
            print('File missing: {}'.format(file_path))
        else:
            raise e


def main():
    backup_filename = 'sd-backup-{}.tar.gz'.format(
        datetime.utcnow().strftime("%Y-%m-%d--%H-%M-%S"))

    # This code assumes everything is in the default locations.
    sd_data = '/var/lib/securedrop'

    sd_code = '/var/www/securedrop'
    sd_config_py = os.path.join(sd_code, "config.py")
    sd_source_config = "/etc/securedrop/source-config.json"
    sd_journalist_config = "/etc/securedrop/journalist-config.json"
    sd_custom_logo = os.path.join(sd_code, "static/i/logo.png")

    tor_hidden_services = "/var/lib/tor/services"
    torrc = "/etc/tor/torrc"

    all_configs = [sd_config_py, sd_source_config, sd_journalist_config]

    with tarfile.open(backup_filename, 'w:gz') as backup:
        # Some of these configs may not be present because a migration may
        # have failed, so we want to avoid failing to do a backup if any
        # aren't present.
        for config_file in all_configs:
            try_add(backup, config_file)

        backup.add(sd_custom_logo)
        backup.add(sd_data)
        backup.add(tor_hidden_services)
        backup.add(torrc)

    print backup_filename


if __name__ == "__main__":
    main()
