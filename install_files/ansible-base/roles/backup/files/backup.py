#!/opt/venvs/securedrop-app-code/bin/python
"""
This script is copied to the App server (to /tmp) and run by the Ansible playbook,
typically via `securedrop-admin`.

The backup file in the format sd-backup-$TIMESTAMP.tar.gz is then copied to the
Admin Workstation by the playbook, and removed on the server. For further
information and limitations, see https://docs.securedrop.org/en/stable/backup_and_restore.html
"""

import os
import tarfile
from datetime import datetime


def main():
    backup_filename = "sd-backup-{}.tar.gz".format(datetime.utcnow().strftime("%Y-%m-%d--%H-%M-%S"))

    # This code assumes everything is in the default locations.
    sd_data = "/var/lib/securedrop"

    sd_code = "/var/www/securedrop"
    sd_config = os.path.join(sd_code, "config.py")
    sd_custom_logo = os.path.join(sd_code, "static/i/custom_logo.png")

    tor_hidden_services = "/var/lib/tor/services"
    torrc = "/etc/tor/torrc"

    with tarfile.open(backup_filename, "w:gz") as backup:
        backup.add(sd_config)

        # If no custom logo has been configured, the file will not exist
        if os.path.exists(sd_custom_logo):
            backup.add(sd_custom_logo)
        backup.add(sd_data)
        backup.add(tor_hidden_services)
        backup.add(torrc)

    print(backup_filename)


if __name__ == "__main__":
    main()
