#!/usr/bin/python2.7
"""
This script should be copied to a running SecureDrop 0.3 instance, along with
the output of `0.2.1_collect.py`. When run (as root), it migrates all of the
information from the 0.2.1 instance to create a matching 0.3 instance.
"""

import sys
import os
import re
import tarfile
import subprocess
import sqlite3
import shutil
from datetime import datetime
from operator import itemgetter
import calendar
import traceback


def migrate_config_file(backup):
    print "* Migrating values from old config file..."

    # Back up new config just in case something goes horribly wrong
    config_fn = "/var/www/securedrop/config.py"
    shutil.copy(config_fn, config_fn + '.backup')

    # Substitute values in new config with values from old config
    old_config = backup.extractfile('var/chroot/source/var/www/securedrop/config.py').read()
    new_config = open(config_fn, 'r').read()
    subs = [
        (r"JOURNALIST_KEY=('.*')", r"^(JOURNALIST_KEY = )('.*')"),
        (r"SCRYPT_ID_PEPPER=('.*')", r"^(SCRYPT_ID_PEPPER = )('.*')"),
        (r"SCRYPT_GPG_PEPPER=('.*')", r"^(SCRYPT_GPG_PEPPER = )('.*')")
    ]
    for sub in subs:
        old_value_repl = r"\1{}".format(re.search(sub[0], old_config).groups()[0])
        new_config = re.sub(sub[1], old_value_repl, new_config, flags=re.MULTILINE)

    # Write out migrated config
    with open(config_fn, 'w') as config:
        config.write(new_config)

    # Restart Apache so the web application picks up the changes to config.py
    subprocess.call(["service", "apache2", "restart"])


def extract_tree_to(tar, selector, dest):
    # http://stackoverflow.com/a/15171308/1093000
    if type(selector) is str:
        prefix = selector
        selector = lambda m: m.name.startswith(prefix)
    members = [m for m in tar.getmembers() if selector(m)]
    for m in members:
        m.name = m.name[len(prefix):]
    tar.extractall(path=dest, members=members)


def extract_file_to(tar, src, dst):
    src_member = tar.getmember(src)
    # Hack member name to change where it gets extracted to
    src_member.name = dst
    tar.extract(src_member)


def migrate_securedrop_root(backup):
    print "* Migrating directories from SECUREDROP_ROOT..."
    extract_tree_to(backup, "var/securedrop/", "/var/lib/securedrop")
    subprocess.call(['chown', '-R', 'www-data:www-data', "/var/lib/securedrop"])


def migrate_database(backup):
    print "* Migrating database..."

    # Get the sources table from the 0.2.1 instance's db
    old_db = backup.getmember("var/chroot/document/var/www/securedrop/db.sqlite")
    old_db.name = "db.old.sqlite"
    backup.extract(old_db)
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
    from old_crypto_util import displayid
    # Generate a list of the filesystem ids that have journalist designations
    # stored in the database, since they are already known and should not be
    # generated from the filesystem id
    already_processed = set([source[0] for source in sources])
    for fs_id in os.listdir("/var/lib/securedrop/store"):
        if fs_id in already_processed:
            continue
        sources.append((fs_id, displayid(fs_id)))

    # Import current application's config so we can easily populate the db
    sys.path.append("/var/www/securedrop")
    import config
    from db import Source, Journalist, Submission, Reply, db_session, init_db

    # We need to be able to link replies to the Journalist that sent
    # them. Since this information was not recorded in 0.2.1, we
    # arbitrarily say all replies were sent by an arbitrary journalist
    # that is present on this system. Since this information is not
    # currently exposed in the UI, this does not create a problem (for
    # now).
    if len(Journalist.query.all()) == 0:
        print "!!! FATAL: You must create a journalist account before running this migration."
        print "           Run ./manage.py add_admin and try again."
        sys.exit(1)
    else:
        arbitrary_journalist = Journalist.query.all()[0]

    # Back up current database just in case
    shutil.copy("/var/lib/securedrop/db.sqlite",
                "/var/lib/securedrop/db.sqlite.bak")

    # Copied from db.py to compute filesystem-safe journalist filenames
    def journalist_filename(s):
        valid_chars = 'abcdefghijklmnopqrstuvwxyz1234567890-_'
        return ''.join([c for c in s.lower().replace(' ', '_') if c in valid_chars])

    # Migrate rows to new database with SQLAlchemy ORM
    for source in sources:
        migrated_source = Source(source[0], source[1])
        source_dir = os.path.join("/var/lib/securedrop/store", source[0])

        # It appears that there was a bug in 0.2.1 where sources with changed
        # names were not always successfully removed from the database. Skip
        # any sources that didn't have files copied for them, they were deleted
        # and are in the database erroneously.
        if not os.path.isdir(source_dir):
            continue

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
        replies = []
        for fn in os.listdir(source_dir):
            append_to = submissions
            if fn.startswith('reply-'):
                append_to = replies
            append_to.append((fn, os.path.getmtime(os.path.join(source_dir, fn))))

        # Sort by submission time
        submissions.sort(key=itemgetter(1))
        replies.sort(key=itemgetter(1))

        if len(submissions) > 0:
            migrated_source.last_updated = datetime.utcfromtimestamp(submissions[-1][1])
        else:
            # The source will have the default .last_updated of utcnow(), which
            # might be a little confusing, but it's the best we can do.
            pass

        # Since the concept of "pending" is introduced in 0.3, it's tricky to
        # figure out how to set this value. We can't distinguish between sources
        # who created an account but never submitted anything and sources who
        # had been active, but didn't have any stored submissions or replies at
        # the time of migration.
        #
        # After having explored the options, I think the best thing to do here
        # is set pending to True if there are no submissions or replies. Sources
        # who created an account but never submitted anything won't create noise
        # in the list, and sources who are active can probably be expected to
        # log back in relatively soon and so will automatially reappear once
        # they submit something new.
        if len(submissions + replies) == 0:
            migrated_source.pending = True
        else:
            migrated_source.pending = False

        # Set source.interaction_count to the number of current submissions for
        # each source. This is not technicially correct, but since we can't
        # know how many submissions have been deleted it will give us a
        # reasonable, monotonically increasing basis for future increments to
        # the interaction_count.
        migrated_source.interaction_count = len(submissions) + len(replies)

        # Add and commit the source to the db so they will have a primary key
        # assigned to use with the ForeignKey relationship with their
        # submissions
        db_session.add(migrated_source)
        db_session.commit()

        # Combine everything into one list, sorted by date, so we can
        # correctly set the interaction counts for each file.
        everything = submissions + replies
        everything.sort(key=itemgetter(1))
        for count, item in enumerate(everything):
            # Rename the file to fit the new file naming scheme used by 0.3
            fn = item[0]

            if fn.startswith('reply-'):
                new_fn = "{0}-{1}-reply.gpg".format(count+1, journalist_filename(source[1]))
            else:
                new_fn = "{0}-{1}-{2}".format(count+1, journalist_filename(source[1]), "msg.gpg" if fn.endswith("msg.gpg") else "doc.zip.gpg")

            # Move to the new filename
            os.rename(os.path.join(source_dir, fn),
                      os.path.join(source_dir, new_fn))

            # Add a database entry for this item
            db_entry = None

            if fn.startswith('reply-'):
                migrated_reply = Reply(arbitrary_journalist, migrated_source, new_fn)
                db_entry = migrated_reply
            else:
                migrated_submission = Submission(migrated_source, new_fn)
                # Assume that all submissions that are being migrated
                # have already been downloaded
                migrated_submission.downloaded = True
                db_entry = migrated_submission

            db_session.add(db_entry)
            db_session.commit()

    # chown the database file to the securedrop user
    subprocess.call(['chown', 'www-data:www-data', "/var/lib/securedrop/db.sqlite"])


def migrate_custom_header_image(backup):
    print "* Migrating custom header image..."
    extract_file_to(backup,
                    "var/chroot/source/var/www/securedrop/static/i/securedrop.png",
                    "/var/www/securedrop/static/i/logo.png")
    subprocess.call(['chown', '-R', 'www-data:www-data', "/var/www/securedrop/static/i/logo.png"])


def migrate_tor_files(backup):
    print "* Migrating source interface .onion..."

    tor_root_dir = "/var/lib/tor"
    ths_root_dir = os.path.join(tor_root_dir, "services")

    # For now, we're going to re-provision the monitor and SSH
    # hidden services. The only hidden service whose address
    # we want to maintain is the source interface. Modify the
    # code below to migrate other hidden services as well.

    # Restore source interface hidden sevice key to maintain the original
    # .onion address
    source_ths_dir = os.path.join(ths_root_dir, "source")

    # Delete the files created by ansible
    for fn in os.listdir(source_ths_dir):
        os.remove(os.path.join(source_ths_dir, fn))

    # Extract the original source interface THS key
    extract_file_to(backup,
                    "var/chroot/source/var/lib/tor/hidden_service/private_key",
                    os.path.join(source_ths_dir, "private_key"))

    # chmod the files so they're owned by debian-tor:debian-tor
    subprocess.call(['chown', '-R', 'debian-tor:debian-tor', source_ths_dir])
    # Reload Tor to trigger registering the migrated Tor Hidden Service address
    subprocess.call(['service', 'tor', 'reload'])


def main():
    if len(sys.argv) <= 1:
        print "Usage: 0.3_migrate.py <backup filename>"
        sys.exit(1)

    try:
        backup_fn = sys.argv[1]
        with tarfile.open(backup_fn, 'r:*') as backup:
            migrate_config_file(backup)
            migrate_securedrop_root(backup)
            migrate_database(backup)
            migrate_custom_header_image(backup)
            migrate_tor_files(backup)
    except SystemExit as e:
        pass
    except:
        print "\n!!! Something went wrong, please file an issue.\n"
        print traceback.format_exc()
    else:
        print "Done!"

if __name__ == "__main__":
    main()
