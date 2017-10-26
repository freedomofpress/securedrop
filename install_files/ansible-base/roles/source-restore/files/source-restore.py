#!/usr/bin/python2.7
"""
This script and backup archive should be copied to the App server and run by
the Ansible playbook. When run (as root), it restores only source identities
to the machine it's run on.

python source-restore.py sources-backup-DATETIME.json
"""

import grp
import json
import os
import pwd
import subprocess
import sys

import gnupg
from sqlalchemy.exc import IntegrityError

import config
from db import db_session, Source
import store


def verify_args():
    usage = """
    Usage: source-restore.py <backup file>

    <backup file>  Path to a SecureDrop source backup"
    """
    if len(sys.argv) != 2:
        print(usage)
        sys.exit(1)

    if not os.path.exists(sys.argv[1]):
        print("<backup file> '{}' not found".format(sys.argv(1)))
        sys.exit(1)

    if os.geteuid() != 0:
        print("This program must be run as root!")
        sys.exit(1)


def restore_source(source):
    gpg = gnupg.GPG(binary='gpg2', homedir=config.GPG_KEY_DIR)
    gpg.import_keys(source['gpg_key'])

    # Make all files in gpg home folder owned by www-data
    gpg_files = [f for f in os.listdir(config.GPG_KEY_DIR)
        if os.path.isdir(os.path.join(config.GPG_KEY_DIR, f))]

    for gpg_file in gpg_files:
        uid = pwd.getpwnam("www-data").pw_uid
        gid = grp.getgrnam("www-data").gr_gid
        os.chown(gpg_file, uid, gid)

    # Make directory for source documents and ensure it has the right
    # permissions
    source_folder = store.path(source['filesystem_id'])
    if not os.path.exists(source_folder):
        os.mkdir(source_folder)
        uid = pwd.getpwnam("www-data").pw_uid
        gid = grp.getgrnam("www-data").gr_gid
        path = store.path(source_folder)
        os.chown(path, uid, gid)

    try:
        new_source = Source(
            filesystem_id=source['filesystem_id'],
            journalist_designation=source['journalist_designation'],
            pending=False)
        db_session.add(new_source)
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        print 'Source already restored: "{}". Skipping...'.format(
            source['journalist_designation'])


def main():
    verify_args()

    with open(sys.argv[1], 'r') as infile:
        sources = json.load(infile)

    for source in sources:
        restore_source(source)

    # Reload Tor and the web server so they pick up the new configuration
    # If the process exits with a non-zero return code, raises an exception.
    subprocess.check_call(['service', 'apache2', 'restart'])
    subprocess.check_call(['service', 'tor', 'reload'])


if __name__ == "__main__":
    main()
