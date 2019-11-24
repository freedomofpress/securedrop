from __future__ import print_function

import datetime
import os
import sys
import time

from db import db
from rm import secure_delete
from models import Reply, Source, Submission
from management import app_context


def find_disconnected_db_submissions(path):
    """
    Finds Submission records whose file does not exist.
    """
    submissions = db.session.query(Submission).order_by(Submission.id, Submission.filename).all()

    files_in_fs = {}
    for directory, subdirs, files in os.walk(path):
        for f in files:
            files_in_fs[f] = os.path.abspath(os.path.join(directory, f))

    disconnected_submissions = [s for s in submissions if s.filename not in files_in_fs]

    return disconnected_submissions


def check_for_disconnected_db_submissions(args):
    """
    Check for Submission records whose files are missing.
    """
    with app_context():
        disconnected = find_disconnected_db_submissions(args.store_dir)
        if disconnected:
            print(
                "There are submissions in the database with no corresponding files. "
                'Run "manage.py list-disconnected-db-submissions" for details.'
            )
        else:
            print("No problems were found. All submissions' files are present.")


def list_disconnected_db_submissions(args):
    """
    List the IDs of Submission records whose files are missing.
    """
    with app_context():
        disconnected_submissions = find_disconnected_db_submissions(args.store_dir)
        if disconnected_submissions:
            print(
                'Run "manage.py delete-disconnected-db-submissions" to delete these records.',
                file=sys.stderr,
            )
        for s in disconnected_submissions:
            print(s.id)


def delete_disconnected_db_submissions(args):
    """
    Delete Submission records whose files are missing.
    """
    with app_context():
        disconnected_submissions = find_disconnected_db_submissions(args.store_dir)
        ids = [s.id for s in disconnected_submissions]

        remove = args.force
        if not args.force:
            remove = input("Enter 'y' to delete all submissions missing files: ") == "y"
        if remove:
            print("Removing submission IDs {}...".format(ids))
            db.session.query(Submission).filter(Submission.id.in_(ids)).delete(
                synchronize_session="fetch"
            )
            db.session.commit()
        else:
            print("Not removing disconnected submissions in database.")


def find_disconnected_fs_submissions(path):
    """
    Finds files in the store that lack a Submission or Reply record.
    """
    submissions = Submission.query.order_by(Submission.id, Submission.filename).all()
    files_in_db = {s.filename: True for s in submissions}

    replies = Reply.query.order_by(Reply.id, Reply.filename).all()
    files_in_db.update({r.filename: True for r in replies})

    files_in_fs = {}
    for directory, subdirs, files in os.walk(path):
        for f in files:
            files_in_fs[f] = os.path.abspath(os.path.join(directory, f))

    disconnected_files = []
    for f, p in files_in_fs.items():
        if f not in files_in_db:
            filesize = os.stat(p).st_size
            disconnected_files.append((p, filesize))

    disconnected_files = [t[0] for t in sorted(disconnected_files, key=lambda t: t[1])]

    return disconnected_files


def check_for_disconnected_fs_submissions(args):
    """
    Check for files without a corresponding Submission or Reply record in the database.
    """
    with app_context():
        disconnected = find_disconnected_fs_submissions(args.store_dir)
        if disconnected:
            print(
                "There are files in the submission area with no corresponding records in the "
                'database. Run "manage.py list-disconnected-fs-submissions" for details.'
            )
        else:
            print("No unexpected files were found in the store.")


def list_disconnected_fs_submissions(args):
    """
    List files without a corresponding Submission or Reply record in the database.
    """
    with app_context():
        disconnected_files = find_disconnected_fs_submissions(args.store_dir)
        if disconnected_files:
            print(
                'Run "manage.py delete-disconnected-fs-submissions" to delete these files.',
                file=sys.stderr,
            )
        for f in disconnected_files:
            print(f)


def delete_disconnected_fs_submissions(args):
    """
    Delete files without a corresponding Submission record in the database.
    """
    with app_context():
        disconnected_files = find_disconnected_fs_submissions(args.store_dir)
        bytes_deleted = 0
        time_elapsed = 0.0
        rate = 1.0
        filecount = len(disconnected_files)
        eta_msg = ""
        for i, f in enumerate(disconnected_files, 1):
            remove = args.force
            if not args.force:
                remove = input("Enter 'y' to delete {}: ".format(f)) == "y"
            if remove:
                filesize = os.stat(f).st_size
                if i > 1:
                    eta = filesize / rate
                    eta_msg = " (ETA to remove {:d} bytes: {:.0f}s )".format(filesize, eta)
                print("Securely removing file {}/{} {}{}...".format(i, filecount, f, eta_msg))
                start = time.time()
                secure_delete(f)
                file_elapsed = time.time() - start
                bytes_deleted += filesize
                time_elapsed += file_elapsed
                rate = bytes_deleted / time_elapsed
                print(
                    "elapsed: {:.2f}s rate: {:.1f} MB/s overall rate: {:.1f} MB/s".format(
                        file_elapsed, filesize / 1048576 / file_elapsed, rate / 1048576
                    )
                )
            else:
                print("Not removing {}.".format(f))


def were_there_submissions_today(args, context=None):
    with context or app_context():
        something = (
            db.session.query(Source)
            .filter(Source.last_updated > datetime.datetime.utcnow() - datetime.timedelta(hours=24))
            .count()
            > 0
        )
        count_file = os.path.join(args.data_root, "submissions_today.txt")
        open(count_file, "w").write(something and "1" or "0")


def add_check_db_disconnect_parser(subps):
    check_db_disconnect_subp = subps.add_parser(
        "check-disconnected-db-submissions",
        help="Check for submissions that exist in the database but not the filesystem.",
    )
    check_db_disconnect_subp.set_defaults(func=check_for_disconnected_db_submissions)


def add_check_fs_disconnect_parser(subps):
    check_fs_disconnect_subp = subps.add_parser(
        "check-disconnected-fs-submissions",
        help="Check for submissions that exist in the filesystem but not in the database.",
    )
    check_fs_disconnect_subp.set_defaults(func=check_for_disconnected_fs_submissions)


def add_delete_db_disconnect_parser(subps):
    delete_db_disconnect_subp = subps.add_parser(
        "delete-disconnected-db-submissions",
        help="Delete submissions that exist in the database but not the filesystem.",
    )
    delete_db_disconnect_subp.set_defaults(func=delete_disconnected_db_submissions)
    delete_db_disconnect_subp.add_argument(
        "--force", action="store_true", help="Do not ask for confirmation."
    )


def add_delete_fs_disconnect_parser(subps):
    delete_fs_disconnect_subp = subps.add_parser(
        "delete-disconnected-fs-submissions",
        help="Delete submissions that exist in the filesystem but not the database.",
    )
    delete_fs_disconnect_subp.set_defaults(func=delete_disconnected_fs_submissions)
    delete_fs_disconnect_subp.add_argument(
        "--force", action="store_true", help="Do not ask for confirmation."
    )


def add_list_db_disconnect_parser(subps):
    list_db_disconnect_subp = subps.add_parser(
        "list-disconnected-db-submissions",
        help="List submissions that exist in the database but not the filesystem.",
    )
    list_db_disconnect_subp.set_defaults(func=list_disconnected_db_submissions)


def add_list_fs_disconnect_parser(subps):
    list_fs_disconnect_subp = subps.add_parser(
        "list-disconnected-fs-submissions",
        help="List submissions that exist in the filesystem but not the database.",
    )
    list_fs_disconnect_subp.set_defaults(func=list_disconnected_fs_submissions)


def add_were_there_submissions_today(subps):
    parser = subps.add_parser(
        "were-there-submissions-today",
        help=("Update the file indicating " "whether submissions were received in the past 24h."),
    )
    parser.set_defaults(func=were_there_submissions_today)
