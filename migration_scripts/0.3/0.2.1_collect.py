#!/usr/bin/python2.7
"""

This script should be copied to a running SecureDrop 0.2.1 instance. When run
(as root), it collects all of the necessary information to migrate the system
to 0.3 and stores it in /tmp/sd-migrate-0.2.1.zip

"""

import sys
import os
import re
import zipfile

# Arbitrarily pick the source chroot jail (doesn't matter)
securedrop_root = "/var/chroot/source/var/www/securedrop"

def collect_config_file(zf):
    config_file_path = os.path.join(securedrop_root, "config.py")
    zf.write(config_file_path)

def collect_securedrop_root(zf):
    # The store and key dirs are shared between the chroot jails in 0.2.1, and
    # are both linked from /var/securedrop
    for root, dirs, files in os.walk("/var/securedrop"):
        for name in files:
            zf.write(os.path.join(root, name))

def collect_database(zf):
    # Copy the db file, which is only present in the document interface's
    # chroot jail in 0.2.1
    zf.write("/var/chroot/document/var/www/securedrop/db.sqlite")

def collect_custom_header_image(zf):
    # 0.2.1's deployment didn't actually use config.CUSTOM_HEADER_IMAGE - it
    # just overwrote the default header image, `static/i/securedrop.png`.
    zf.write(os.path.join(securedrop_root, "static/i/securedrop.png"))

def collect_tor_files(zf):
    tor_files = [
        "/etc/tor/torrc",
        "/var/lib/tor/hidden_service/client_keys",
        "/var/chroot/source/var/lib/tor/hidden_service/private_key",
        "/var/chroot/document/var/lib/tor/hidden_service/client_keys",
    ]

    for tor_file in tor_files:
        # Since the 0.2.1 install process was occasionally somewaht ad
        # hoc, the SSH ATHS was not always set up. We treat that as a
        # non-fatal error and continue.
        if not os.path.isfile(tor_file) and tor_file == "/var/lib/tor/hidden_service/client_keys":
            print "!\tWarning: expected file '{}' not found. Continuing anyway.".format(tor_file)
            continue
        zf.write(tor_file)

def main():
    if len(sys.argv) <= 1:
        print "Usage: 0.2.1_collect.py <filename>\n\n    <filename>\tLocation to save the .zip backup"
        sys.exit(1)

    zf_fn = sys.argv[1]
    with zipfile.ZipFile(zf_fn, 'w') as zf:
        collect_config_file(zf)
        collect_securedrop_root(zf)
        collect_database(zf)
        collect_custom_header_image(zf)
        collect_tor_files(zf)

if __name__ == "__main__":
    main()
