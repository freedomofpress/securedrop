#!/usr/bin/python2.7
"""

This script should be copied to the App server and ran by the anisble
plabook. When run (as root), it collects all of the necessary information
to backup the 0.3 system and stores it in /tmp/sd-backup-0.3-TIME_STAMP.zip.gpg

"""

import sys
import os
import io
import zipfile
from datetime import datetime
# Import the application config.py file
sys.path.append("/var/www/securedrop")
import config  # noqa: F403
import gnupg  # noqa: F403

TOR_SERVICES = "/var/lib/tor/services"
TOR_CONFIG = "/etc/tor/torrc"


def collect_config_file(zf):
    config_file_path = os.path.join(config.SECUREDROP_ROOT, "config.py")
    zf.write(config_file_path)


def collect_securedrop_data_root(zf):
    # The store and key dirs are shared between both interfaces
    for root, dirs, files in os.walk(config.SECUREDROP_DATA_ROOT):
        for name in files:
            zf.write(os.path.join(root, name))


def collect_custom_header_image(zf):
    # The custom header image is copied over the deafult `static/i/logo.png`.
    zf.write(os.path.join(config.SECUREDROP_ROOT, "static/i/logo.png"))


def collect_tor_files(zf):
    # All of the tor Onion Service private keys are stored in the THS specific
    # subdirectory `/var/lib/tor/services` backing up this directory will back
    # up all of the THS and ATHS required keys needed to restore all the hidden
    # services on that system.
    for root, dirs, files in os.walk(TOR_SERVICES):
        for name in files:
            zf.write(os.path.join(root, name))

    # The tor config file has the ATHS client names required to restore
    # the ATHS info. These names are also in the the specific client_key file
    # but backing up this file makes it easier than parsing the files during a
    # restore.
    zf.write(TOR_CONFIG)


def encrypt_zip_file(zf_fn):
    # Encrypt the backup zip file with the application's gpg public key
    gpg = gnupg.GPG(binary='gpg2', homedir=config.GPG_KEY_DIR)
    e_fn = '{}.gpg'.format(zf_fn)

    stream = io.open(zf_fn, "rb")
    gpg.encrypt_file(stream, config.JOURNALIST_KEY, always_trust='True',
                     output=e_fn)


def main():
    # name append a timestamp to the sd-backup zip filename
    dt = str(datetime.utcnow().strftime("%Y-%m-%d--%H-%M-%S"))
    zf_fn = 'sd-backup-{}.zip'.format(dt)
    with zipfile.ZipFile(zf_fn, 'w') as zf:
        collect_config_file(zf)
        collect_securedrop_data_root(zf)
        collect_custom_header_image(zf)
        collect_tor_files(zf)
    encrypt_zip_file(zf_fn)
    print(zf_fn)


if __name__ == "__main__":
    main()
