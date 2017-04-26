#!/usr/bin/python2.7
"""
This script should be copied to a running SecureDrop 0.2.1 instance. When run
(as root), it collects all of the necessary information to migrate the system
to 0.3 and stores it in the .tar.gz file specified in the first argument.
"""

import sys
import os
import re
import tarfile


# Arbitrarily pick the source chroot jail (doesn't matter)
securedrop_root = "/var/chroot/source/var/www/securedrop"


def collect_config_file(backup):
    config_file = os.path.join(securedrop_root, "config.py")
    backup.add(config_file)
    return config_file


def collect_securedrop_root(backup):
    # The store and key dirs are shared between the chroot jails in
    # 0.2.1, and are both linked from /var/securedrop
    securedrop_root = "/var/securedrop"
    backup.add(securedrop_root)
    return securedrop_root


def collect_database(backup):
    # Copy the db file, which is only present in the journalist interface's
    # chroot jail in 0.2.1
    db_file = "/var/chroot/document/var/www/securedrop/db.sqlite"
    backup.add(db_file)
    return db_file


def collect_custom_header_image(backup):
    # 0.2.1's deployment didn't actually use
    # config.CUSTOM_HEADER_IMAGE - it just overwrote the default
    # header image, `static/i/securedrop.png`.
    header_image = os.path.join(securedrop_root, "static/i/securedrop.png")
    backup.add(header_image)
    return header_image


def collect_tor_files(backup):
    tor_files = [
        "/etc/tor/torrc",
        "/var/lib/tor/hidden_service/client_keys",
        "/var/chroot/source/var/lib/tor/hidden_service/private_key",
        "/var/chroot/document/var/lib/tor/hidden_service/client_keys",
    ]
    collected = []
    for tor_file in tor_files:
        # Since the 0.2.1 install process was occasionally somewaht ad
        # hoc, the SSH ATHS was not always set up. We treat that as a
        # non-fatal error and continue.
        if (not os.path.isfile(tor_file)
            and tor_file == "/var/lib/tor/hidden_service/client_keys"):
            print ("[!] Warning: expected file '{}' not found. "
                   "Continuing anyway.".format(tor_file))
            continue
        backup.add(tor_file)
        collected.append(tor_file)

    return ', '.join(collected)


def main():
    if len(sys.argv) <= 1:
        print "Usage: 0.2.1_collect.py <backup filename>"
        sys.exit(1)

    backup_filename = sys.argv[1]
    if not backup_filename.endswith(".tar.gz"):
        backup_filename += ".tar.gz"

    backup_fns = [
        collect_config_file,
        collect_securedrop_root,
        collect_database,
        collect_custom_header_image,
        collect_tor_files
    ]

    print "Backing up..."
    with tarfile.open(backup_filename, 'w:gz') as backup:
        for fn in backup_fns:
            print "[+] Collected {}".format(fn(backup))

    print "Done!"

if __name__ == "__main__":
    main()
