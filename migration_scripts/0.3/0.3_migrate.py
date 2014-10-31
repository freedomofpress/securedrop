#!/usr/bin/python2.7
"""
This script should be copied to a running SecureDrop 0.3 instance, along with
the output of `0.2.1_collect.py`. When run (as root), it migrates all of the
information from the 0.2.1 instance to create a matching 0.3 instance.
"""

import sys
import os
import re
import zipfile
import subprocess
import sqlite3
import shutil
from datetime import datetime
from operator import itemgetter
import calendar
import traceback

def migrate_config_file(zf):
    print "* Migrating values from old config file..."

    old_conf = zf.read('var/chroot/source/var/www/securedrop/config.py')
    new_config_fname = "/var/www/securedrop/config.py"
    new_conf = open(new_config_fname).read()

    # Back up new config
    with open(new_config_fname + '.bak', 'w') as config_backup:
        config_backup.write(new_conf)

    # Substitute values in new config with values from old config
    subs = [
        (r"JOURNALIST_KEY=('.*')", r"^(JOURNALIST_KEY = )('.*')"),
        (r"SCRYPT_ID_PEPPER=('.*')", r"^(SCRYPT_ID_PEPPER = )('.*')"),
        (r"SCRYPT_GPG_PEPPER=('.*')", r"^(SCRYPT_GPG_PEPPER = )('.*')")
    ]

    for sub in subs:
        old_value_repl = r"\1{}".format(re.search(sub[0], old_conf).groups()[0])
        new_conf = re.sub(sub[1], old_value_repl, new_conf, flags=re.MULTILINE)

    # Write out migrated config
    with open(new_config_fname, 'w') as new_conf_fp:
        new_conf_fp.write(new_conf)


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


def extract_to_path(archive, member, path):
    """
    Extract from the zip archive `archive` the member `member` and write it to
    `path`, preserving file metadata.
    """
    # Create all upper directories if necessary
    upperdirs = os.path.dirname(path)
    if upperdirs and not os.path.exists(upperdirs):
        os.makedirs(upperdirs)

    with archive.open(member) as source, \
         file(path, "wb") as target:
        shutil.copyfileobj(source, target)

    # Update the timestamps as well (as best we can, thanks, conversion to
    # localtime). This only actually works if the .zip was created on a
    # machine where the timezone was set to UTC, but it might be good
    # enough since we just need the relative order of timestamps (they will
    # all be normalized anyway).
    if hasattr(member, 'date_time'):
        timestamp = calendar.timegm(member.date_time)
        os.utime(path, (timestamp, timestamp))


def migrate_securedrop_root(zf):
    print "* Migrating directories from SECUREDROP_ROOT..."

    # Restore the original source directories and key files
    for zi in zf.infolist():
        if "var/securedrop/store" in zi.filename:
            extract_to_path(zf, zi, replace_prefix(zi.filename,
                "var/securedrop/store", "/var/lib/securedrop/store"))
        elif "var/securedrop/keys" in zi.filename:
            # TODO: is it a bad idea to migrate the random_seed from the
            # previous installation?
            extract_to_path(zf, zi, replace_prefix(zi.filename,
                "var/securedrop/keys", "/var/lib/securedrop/keys"))

    subprocess.call(['chown', '-R', 'www-data:www-data', "/var/lib/securedrop"])


def migrate_database(zf):
    print "* Migrating database..."

    extract_to_path(zf, "var/chroot/document/var/www/securedrop/db.sqlite", "db.old.sqlite")
    conn = sqlite3.connect("db.old.sqlite")
    c = conn.cursor()
    sources = c.execute("SELECT * FROM sources").fetchall()
    os.remove("db.old.sqlite")

    # Fill in the rest of the sources. Since sources were only added to the
    # database if their codename was changed by the journalist, we need to fill
    # in the rest by examining all of the filesystem designations in the source
    # directory and re-generating the codenames.
    #
    # Note: Must be called after /var/lib/securedrop/store is populated
    from crypto_util import displayid
    # Generate a list of the filesystem ids that have journalist designations
    # store din the database, since they are already known and should not be
    # generated from the filesystem id
    already_processed = set([ source[0] for source in sources ])
    for fs_id in os.listdir("/var/lib/securedrop/store"):
        if fs_id in already_processed:
            continue
        sources.append((fs_id, displayid(fs_id)))

    # Import current application's config so we can easily populate the db
    sys.path.append("/var/www/securedrop")
    import config
    from db import Source, Submission, db_session

    # Copy from db.py to compute filesystem-safe journalist filenames
    def journalist_filename(s):
        valid_chars = 'abcdefghijklmnopqrstuvwxyz1234567890-_'
        return ''.join([c for c in s.lower().replace(' ', '_') if c in valid_chars])

    # Migrate rows to new database with SQLAlchemy ORM
    for source in sources:
        migrated_source = Source(source[0], source[1])
        source_dir = os.path.join("/var/lib/securedrop/store", source[0])

        # Can infer "flagged" state by looking for _FLAG files in store
        if "_FLAG" in os.listdir(source_dir):
            # Mark the migrated source as flagged
            migrated_source.flagged = True
            # Delete the _FLAG file
            os.remove(os.path.join(source_dir, "_FLAG"))

        # Sort the submissions by the date of submission so we can infer the
        # correct interaction_count for the new filenames later, and so we can
        # set source.last_updated to the time of the most recently uploaded
        # submission in the store now.
        submissions = []
        for fn in os.listdir(source_dir):
            submissions.append((fn, os.path.getmtime(os.path.join(source_dir, fn))))
        # Sort by submission time
        submissions.sort(key=itemgetter(1))

        if len(submissions) > 0:
            migrated_source.last_updated = datetime.utcfromtimestamp(submissions[-1][1])
        else:
            # The source will have the default .last_updated of utcnow(), which
            # might be a little confusing, but it's the best we can do.
            pass

        # Since the concept of "pending" is introduced in 0.3, set all migrated
        # sources from 0.2.1 to not be pending. Otherwise, we can't distinguish
        # between sources who created an account but never submitted anything
        # and sources who just didn't have any stored submissions/replies at
        # the time of migration. To avoid stopping journalists from replying to
        # previous known sources, we set all migrated sources to not be pending
        # so they will apppear in the document interface.
        migrated_source.pending = False

        # Set source.interaction_count to the number of current submissions for
        # each source. This is not techncially, correct, but since we can't
        # know how many submissions have been deleted it will give us a
        # reasonable, monotonically increasing basis for future increments to
        # the interaction_count.
        migrated_source.interaction_count = len(submissions)

        # Add and commit the source to the db so they will have a primary key
        # assigned to use with the ForeignKey relationship with their
        # submissions
        db_session.add(migrated_source)
        db_session.commit()

        # submissions are now sorted by date, so we can just loop over them to
        # infer the interaction counts
        for count, submission in enumerate(submissions):
            # TODO Possible concern: submission filenames. Should we migrate
            # them to the current naming scheme? What about the extensions
            # ("msg.gpg" or "doc.zip.gpg", used in `documents_messages_count`
            # among other places)?

            fn = submission[0]

            if fn.startswith('reply-'):
                new_fn = "{0}-reply.gpg".format(count+1)
            else:
                new_fn = "{0}-{1}-{2}".format(count+1, journalist_filename(source[1]), "msg.gpg" if fn.endswith("msg.gpg") else "doc.zip.gpg")

            # Move to the new filename
            os.rename(os.path.join(source_dir, fn),
                      os.path.join(source_dir, new_fn))

            # Add a submission for this source
            migrated_submission = Submission(migrated_source, new_fn)
            # Assume that all submissions that are being migrated have already
            # been downloaded
            migrated_submission.downloaded = True
            db_session.add(migrated_submission)
            db_session.commit()


def migrate_custom_header_image(zf):
    print "* Migrating custom header image..."
    extract_to_path(zf,
        "var/chroot/source/var/www/securedrop/static/i/securedrop.png",
        "/var/www/securedrop/static/i/securedrop.png")
    subprocess.call(['chown', '-R', 'www-data:www-data', "/var/www/securedrop/static/i/securedrop.png"])


def migrate_tor_files(zf):
    print "* Migrating source interface .onion..."

    tor_root_dir = "/var/lib/tor"
    ths_root_dir = os.path.join(tor_root_dir, "services")

    # For now, we're going to re-provision the monitor and SSH hidden services.
    # The only hidden service whose address we want to maintain is the source
    # interface. Modify the code below to migrate other hidden services as well.

    # Restore source interface hidden sevice key to maintain the original
    # .onion address
    source_ths_dir = os.path.join(ths_root_dir, "source")

    # Delete the files created by ansible
    for fn in os.listdir(source_ths_dir):
        os.remove(os.path.join(source_ths_dir, fn))

    # Extract the original source interface THS key
    extract_to_path(zf,
        "var/chroot/source/var/lib/tor/hidden_service/private_key",
        os.path.join(source_ths_dir, "private_key"))

    # chmod the files so they're owned by debian-tor:debian-tor
    subprocess.call(['chown', '-R', 'debian-tor:debian-tor', source_ths_dir])
    # Reload Tor to trigger registering the old Tor Hidden Services
    subprocess.call(['service', 'tor', 'reload'])


def main():
    if len(sys.argv) <= 1:
        print "Usage: 0.3_migrate.py <filename>\n\n    <filename>\tPath to a SecureDrop 0.2.1 backup .zip file created by 0.2.1_collect.py"
        sys.exit(1)

    try:
        zf_fn = sys.argv[1]
        with zipfile.ZipFile(zf_fn, 'r') as zf:
            migrate_config_file(zf)
            migrate_securedrop_root(zf)
            migrate_database(zf)
            migrate_custom_header_image(zf)
            migrate_tor_files(zf)
    except:
        print "\n!!! Something went wrong, please file an issue.\n"
        print traceback.format_exc()
    else:
        print "Done!"

if __name__ == "__main__":
    main()
