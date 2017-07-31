#!/usr/bin/python2.7

from datetime import datetime
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import traceback


def backup_app():
    tar_fn = 'backup-app-{}.tar.bz2'.format(datetime.now().strftime("%Y-%m-%d--%H-%M-%S"))
    with tarfile.open(tar_fn, 'w:bz2') as t:
        t.add('/var/lib/securedrop/')
        t.add('/var/lib/tor/services/')
        t.add('/var/www/securedrop/config.py')
        try:
            t.add('/var/www/securedrop/static/i/logo.png')
        except OSError:
            print "[!] Expected but non-essential file ('logo.png') not found. Continuing..."
    print "**  Backed up system to {} before migrating.".format(tar_fn)


def backup_mon():
    # The only thing we have to back up for the monitor server is the SSH ATHS cert.
    # All other required values are available in prod-specific.yml from the installation.
    tar_fn = 'backup-mon-{}.tar.bz2'.format(datetime.now().strftime("%Y-%m-%d--%H-%M-%S"))
    with tarfile.open(tar_fn, 'w:bz2') as t:
        t.add('/var/lib/tor/services/')
    print "**  Backed up system to {} before migrating.".format(tar_fn)


def secure_unlink(path):
    subprocess.check_call(['srm', '-r', path])


def cleanup_deleted_sources(store_dir, c):
    """
    In 0.3pre and 0.3, there were two bugs that could potentially lead
    to the source directory failing to be deleted when a source was
    deleted from the Journalist Interface. We clean up these leftover
    directories as part of the migration.

    These sources can be identified because they have a source_dir in
    the store_dir, but no corresponding Source entry in the database.

    See https://github.com/freedomofpress/securedrop/pull/944 for context.
    """
    for source_dir in os.listdir(store_dir):
        try:
            source = c.execute("SELECT * FROM sources WHERE filesystem_id=?",
                (source_dir,)).fetchone()
            if not source:
                print "Deleting source with no db entry ('{}')...".format(source_dir)
                secure_unlink(os.path.join(store_dir, source_dir))
        except Exception as e:
            print "\n!!  Error occurred cleaning up deleted sources for source {}".format(source_dir)
            print "Source had {} submissions".format(len(os.listdir(os.path.join(store_dir, source_dir))))
            print traceback.format_exc()


def get_db_connection():
    db_path = "/var/lib/securedrop/db.sqlite"
    assert os.path.isfile(db_path)
    conn = sqlite3.connect(db_path)
    return conn, conn.cursor()


def migrate_app_db():
    store_dir = "/var/lib/securedrop/store"
    conn, c = get_db_connection()

    # Before modifying the database, clean up any source directories that were
    # left on the filesystem after the sources were deleted.
    cleanup_deleted_sources(store_dir, c)

    # To get CREATE TABLE from SQLAlchemy:
    # >>> import db
    # >>> from sqlalchemy.schema import CreateTable
    # >>> print CreateTable(db.Journalist.__table__).compile(db.engine)
    # Or, add `echo=True` to the engine constructor.
    # CREATE TABLE replies
    c.execute("""
CREATE TABLE replies (
	id INTEGER NOT NULL,
	journalist_id INTEGER,
	source_id INTEGER,
	filename VARCHAR(255) NOT NULL,
	size INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(journalist_id) REFERENCES journalists (id),
	FOREIGN KEY(source_id) REFERENCES sources (id)
)""")

    # Fill in replies from the replies in STORE_DIR at the time of the migration
    #
    # Caveats:
    #
    # 1. Before we added the `replies` table, we did not keep track of which
    # journalist wrote the reply. There is no way for us to reverse-engineer
    # that information, so the migration will default to saying they were all
    # created by the first journalist (arbitrarily). Since we do not surface
    # this in the UI yet anyway, it should not be a big deal.
    #
    # 2. We do not try to get the order of the (autoincrementing primary key)
    # reply_id to match the order in which the replies were created (which could
    # be inferred from the file timestamps, since we only normalize submission
    # timestamps and not reply timestamps) since this order is not used anywhere
    # in the code.

    # Copy from db.py to compute filesystem-safe journalist filenames
    def journalist_filename(s):
        valid_chars = 'abcdefghijklmnopqrstuvwxyz1234567890-_'
        return ''.join([c for c in s.lower().replace(' ', '_') if c in valid_chars])

    reply_id = 1
    for source_dir in os.listdir(store_dir):
        try:
            source_id, journalist_designation = c.execute(
                "SELECT id, journalist_designation FROM sources WHERE filesystem_id=?",
                (source_dir,)).fetchone()
        except sqlite3.Error as e:
            print "!!\tError occurred migrating replies for source {}".format(source_dir)
            print traceback.format_exc()
            continue

        for filename in os.listdir(os.path.join(store_dir, source_dir)):
            if "-reply.gpg" not in filename:
                continue

            # Rename the reply file from 0.3pre convention to 0.3 convention
            interaction_count = filename.split('-')[0]
            new_filename = "{}-{}-reply.gpg".format(interaction_count,
                journalist_filename(journalist_designation))
            os.rename(os.path.join(store_dir, source_dir, filename),
                      os.path.join(store_dir, source_dir, new_filename))

            # need id, journalist_id, source_id, filename, size
            journalist_id = 1 # *shrug*
            full_path = os.path.join(store_dir, source_dir, new_filename)
            size = os.stat(full_path).st_size
            c.execute("INSERT INTO replies VALUES (?,?,?,?,?)",
                      (reply_id, journalist_id, source_id, new_filename, size))
            reply_id += 1 # autoincrement for next reply

    # CREATE TABLE journalist_login_attempts
    c.execute("""
CREATE TABLE journalist_login_attempt (
	id INTEGER NOT NULL,
	timestamp DATETIME,
	journalist_id INTEGER,
	PRIMARY KEY (id),
	FOREIGN KEY(journalist_id) REFERENCES journalists (id)
)""")

    # ALTER TABLE journalists, add last_token column
    c.execute("""ALTER TABLE journalists ADD COLUMN last_token VARCHAR(6)""")

    # Save changes and close connection
    conn.commit()
    conn.close()


def app_db_migrated():
    """To make the upgrade role idempotent, we need to skip migrating the
    database if it has already been modified. The best way to do this
    is to check whether the last sql command in `migrate_app_db`
    (ALTER TABLE to add the last_token column to the journalists
    table) succeeded. If so, we can assume the database app migration
    succeeded and can safely skip doing it again.

    """
    conn, c = get_db_connection()
    journalist_tables = c.execute('PRAGMA table_info(journalists)').fetchall()
    table_names = set([table[1] for table in journalist_tables])
    return 'last_token' in table_names


def main():
    if len(sys.argv) <= 1:
        print "Usage: 0.3pre_upgrade.py app|mon"
        sys.exit(1)

    server_role = sys.argv[1]
    assert server_role in ("app", "mon")

    if server_role == "app":
        backup_app()
        if not app_db_migrated():
            migrate_app_db()
    else:
        backup_mon()

if __name__ == "__main__":
    main()
