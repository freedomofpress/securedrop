#!/usr/bin/python2.7
"""

This script and decrypted backup zip should be copied to the App server
and run by the anisble plabook. When run (as root), it restores the 0.3
backup file.

python 0.3_restore.py sd-backup-TIMESTAMP.zip

"""

import sys
import os
import re
import zipfile
import subprocess
import shutil
from datetime import datetime
from operator import itemgetter
import calendar
import traceback


def replace_prefix(path, p1, p2):
    """
    Replace p1 in path with p2

    >>> replace_prefix("/tmp/files/foo.bar", "/tmp", "/home/me")
    "home/me/files/foo.bar"
    """
    common_prefix = os.path.commonprefix([path, p1])
    if common_prefix:
        assert path.find(common_prefix) == 0
        # +1 so chop off the next path separator, which otherwise becomes a
        # leading path separate and confuses os.path.join
        path = path[len(common_prefix)+1:]
    return os.path.join(p2, path)


def extract_to_path(archive, member, path, user):
    """
    Extract from the zip archive `archive` the member `member` and write it to
    `path`, preserving file metadata and chown'ing the file using `user`
    """
    # Create all upper directories if necessary
    upperdirs = os.path.dirname(path)
    if upperdirs and not os.path.exists(upperdirs):
        os.makedirs(upperdirs)

    with archive.open(member) as source, file(path, "wb") as target:
        shutil.copyfileobj(source, target)

    # Update the timestamps as well (as best we can, thanks, conversion to
    # localtime). This only actually works if the .zip was created on a
    # machine where the timezone was set to UTC, but it might be good
    # enough since we just need the relative order of timestamps (they will
    # all be normalized anyway).
    if hasattr(member, 'date_time'):
        timestamp = calendar.timegm(member.date_time)
        os.utime(path, (timestamp, timestamp))

    ug = "{}:{}".format(user, user)
    subprocess.call(['chown', '-R', ug, path])


def restore_config_file(zf):
    print "* Migrating SecureDrop config file from backup..."

    # Restore the original config file
    for zi in zf.infolist():
        if "var/www/securedrop/config.py" in zi.filename:
            extract_to_path(zf, "var/www/securedrop/config.py",
                            "/var/www/securedrop/config.py", "www-data")


def restore_securedrop_root(zf):
    print "* Migrating directories from SECUREDROP_ROOT..."

    # Restore the original source directories and key files
    for zi in zf.infolist():
        if "var/lib/securedrop/store" in zi.filename:
            extract_to_path(zf, zi,
                            replace_prefix(zi.filename,
                                           "var/lib/securedrop/store",
                                           "/var/lib/securedrop/store"),
                            "www-data")
        elif "var/lib/securedrop/keys" in zi.filename:
            # TODO: is it a bad idea to migrate the random_seed from the
            # previous installation?
            extract_to_path(zf, zi,
                            replace_prefix(zi.filename,
                                           "var/lib/securedrop/keys",
                                           "/var/lib/securedrop/keys"),
                            "www-data")


def restore_database(zf):
    print "* Migrating database..."

    extract_to_path(zf, "var/lib/securedrop/db.sqlite",
                    "/var/lib/securedrop/db.sqlite", "www-data")


def restore_custom_header_image(zf):
    print "* Migrating custom header image..."
    extract_to_path(zf,
                    "var/www/securedrop/static/i/logo.png",
                    "/var/www/securedrop/static/i/logo.png", "www-data")


def restore_tor_files(zf):
    tor_root_dir = "/var/lib/tor"
    ths_root_dir = os.path.join(tor_root_dir, "services")
    source_ths_dir = os.path.join(ths_root_dir, "source")
    journalist_ths_dir = os.path.join(ths_root_dir, "journalist")

    print "* Deleting previous source THS interface..."

    for fn in os.listdir(source_ths_dir):
        os.remove(os.path.join(source_ths_dir, fn))

    print "* Deleting previous journalist ATHS interface..."

    for fn in os.listdir(journalist_ths_dir):
        os.remove(os.path.join(journalist_ths_dir, fn))

    print "* Migrating source and journalist interface .onion..."

    for zi in zf.infolist():
        if "var/lib/tor/services/source" in zi.filename:
            extract_to_path(zf, zi,
                            replace_prefix(zi.filename,
                                           "var/lib/tor/services/source",
                                           "/var/lib/tor/services/source"),
                            "debian-tor")
        elif "var/lib/tor/services/journalist" in zi.filename:
            extract_to_path(zf, zi,
                            replace_prefix(zi.filename,
                                           "var/lib/tor/services/journalist",
                                           "/var/lib/tor/services/journalist"),
                            "debian-tor")

    # Reload Tor to trigger registering the old Tor Hidden Services
    # reloading Tor compared to restarting tor will not break the current tor
    # connections for SSH
    subprocess.call(['service', 'tor', 'reload'])


def main():
    if len(sys.argv) <= 1:
        print ("Usage: 0.3_restore.py <filename>\n\n"
               "    <filename>\tPath to a SecureDrop 0.3 backup .zip file"
               "created by 0.3_collect.py")
        sys.exit(1)

    try:
        zf_fn = sys.argv[1]
        with zipfile.ZipFile(zf_fn, 'r') as zf:
            restore_config_file(zf)
            restore_securedrop_root(zf)
            restore_database(zf)
            restore_custom_header_image(zf)
            restore_tor_files(zf)
    except:
        print "\n!!! Something went wrong, please file an issue.\n"
        print traceback.format_exc()
    else:
        print "Done!"

if __name__ == "__main__":
    main()
