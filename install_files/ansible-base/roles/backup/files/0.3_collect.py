#!/usr/bin/python2.7
"""

This script should be copied to the App server and ran by the anisble
plabook. When run (as root), it collects all of the necessary information
to backup the 0.3 system and stores it in /tmp/sd-backup-0.3-TIME_STAMP.zip

"""

import sys
import os
import re
import zipfile
from datetime import datetime
import functools

securedrop_code = "/var/www/securedrop"
securedrop_data = "/var/lib/securedrop"
tor_services    = "/var/lib/tor/services"
tor_config      = "/etc/tor/torrc"

def collect_config_file(zf):
    config_file_path = os.path.join(securedrop_code, "config.py")
    zf.write(config_file_path)

def collect_securedrop_data(zf):
    # The store and key dirs are shared between both interfaces
    for root, dirs, files in os.walk(securedrop_data):
        for name in files:
            zf.write(os.path.join(root, name))

def collect_custom_header_image(zf):
    # The custom header image is copied over the deafult `static/i/logo.png`.
    zf.write(os.path.join(securedrop_code, "static/i/logo.png"))

def collect_tor_files(zf):
    # All of the tor hidden service private keys are stored in the THS specific
    # subdirectory `/var/lib/tor/services` backing up this directory will back
    # up all of the THS and ATHS required keys needed to restore all the hidden
    # services on that system.
    for root, dirs, files in os.walk(tor_services):
        for name in files:
            zf.write(os.path.join(root, name))

    # The tor config file has the ATHS client names required to restore
    # the ATHS info. These names are also in the the specific client_key file
    # but backing up this file makes it easier than parsing the files during a
    # restore.
    zf.write(tor_config)

def main():
    # name append a timestamp to the sd-backup zip filename
    dt = str(datetime.utcnow().strftime("%Y-%m-%d--%H-%M-%S"))
    zf_fn = 'sd-backup-'+dt+'.zip'
    with zipfile.ZipFile(zf_fn, 'w') as zf:
        collect_config_file(zf)
        collect_securedrop_data(zf)
        collect_custom_header_image(zf)
        collect_tor_files(zf)
    print zf_fn

if __name__ == "__main__":
    main()

