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
import imp

securedrop_root = "/var/chroot/source/var/www/securedrop"
config_file_path = os.path.join(securedrop_root, "config.py")
config = imp.load_source('config', config_file_path)

def collect_config_file(zf):
    zf.write(config_file_path)

def collect_securedrop_root(zf):
    # In 0.2.1, all of SecureDrop's state was stored in
    # `config.SECUREDROP_ROOT`. In 0.3, this was changed to
    # `config.SECUREDROP_DATA_ROOT` and `config.SECUREDROP_ROOT` in config.py
    # now refers to the code root.
    relative_path_re = r'^{}/(.*)'.format(config.SECUREDROP_ROOT)
    for root, dirs, files in os.walk(config.SECUREDROP_ROOT):
        relative_path = os.path.join("securedrop",
                re.match(relative_path_re, root).groups(0))
        for name in files:
            zf.write(os.path.join(root, name),
                     arcname=os.path.join(relative_path, name))

def collect_custom_header_image(zf):
    if config.CUSTOM_HEADER_IMAGE:
        zf.write(os.path.join(securedrop_root,
            os.path.join("static/i", config.CUSTOM_HEADER_IMAGE)))

def collect_tor_files(zf):
    tor_files = [
        ("/etc/tor/torrc", "torrc"),
        ("/var/lib/tor/hidden_services/client_keys", "app-ssh-client_keys"),
        ("/var/chroot/source/var/lib/tor/hidden_services/private_key", "app-source-private_key"),
        ("/var/chroot/document/var/lib/tor/hidden_services/client_keys", "app-document-client_keys"),
    ]

    for tor_file in tor_files:
        zf.write(tor_file[0], arcname=os.path.join("tor_files", tor_file[1]))

def main():
    zf_fn = "/tmp/sd-migrate-0.2.1.zip"
    with zipfile.ZipFile(zf_fn, 'w') as zf:
        collect_config_file(zf)
        collect_securedrop_root(zf)
        collect_custom_header_image(zf)
        collect_tor_files(zf)

if __name__ == "__main__":
    main()
