from datetime import datetime
from flask import (abort, current_app, g, flash, Markup, send_file,
                   render_template)
from flask_babel import gettext

import crypto_util
import store
import worker

from db import (Journalist, Source, get_one_or_else, db_session, PasswordError,
                SourceStar)
from rm import srm


def get_source(filesystem_id):
    """Return a Source object, representing the database row, for the source
    with the `filesystem_id`"""
    source = None
    query = Source.query.filter(Source.filesystem_id == filesystem_id)
    source = get_one_or_else(query, current_app.logger, abort)

    return source


def logged_in():
    # When a user is logged in, we push their user ID (database primary key)
    # into the session. setup_g checks for this value, and if it finds it,
    # stores a reference to the user's Journalist object in g.
    #
    # This check is good for the edge case where a user is deleted but still
    # has an active session - we will not authenticate a user if they are not
    # in the database.
    return bool(g.get('user', None))


def commit_account_changes(user):
    if db_session.is_modified(user):
        try:
            db_session.add(user)
            db_session.commit()
        except Exception as e:
            flash(gettext(
                "An unexpected error occurred! Please check the application "
                  "logs or inform your adminstrator."), "error")
            current_app.logger.error("Account changes for '{}' failed: {}"
                                     .format(user, e))
            db_session.rollback()
        else:
            flash(gettext("Account updated."), "success")


def make_password():
    while True:
        password = crypto_util.genrandomid(7)
        try:
            Journalist.check_password_acceptable(password)
            return password
        except PasswordError:
            continue


def set_diceware_password(user, password):
    try:
        user.set_password(password)
    except PasswordError:
        flash(gettext(
            'You submitted a bad password! Password not changed.'), 'error')
        return

    try:
        db_session.commit()
    except Exception:
        flash(gettext(
            'There was an error, and the new password might not have been '
            'saved correctly. To prevent you from getting locked '
            'out of your account, you should reset your password again.'),
            'error')
        current_app.logger.error('Failed to update a valid password.')
        return

    # using Markup so the HTML isn't escaped
    flash(Markup("<p>" + gettext(
        "Password updated. Don't forget to "
        "save it in your KeePassX database. New password:") +
        ' <span><code>{}</code></span></p>'.format(password)),
        'success')


def make_star_true(filesystem_id):
    source = get_source(filesystem_id)
    if source.star:
        source.star.starred = True
    else:
        source_star = SourceStar(source)
        db_session.add(source_star)


def make_star_false(filesystem_id):
    source = get_source(filesystem_id)
    if not source.star:
        source_star = SourceStar(source)
        db_session.add(source_star)
        db_session.commit()
    source.star.starred = False


def download(zip_basename, submissions):
    """Send client contents of ZIP-file *zip_basename*-<timestamp>.zip
    containing *submissions*. The ZIP-file, being a
    :class:`tempfile.NamedTemporaryFile`, is stored on disk only
    temporarily.

    :param str zip_basename: The basename of the ZIP-file download.

    :param list submissions: A list of :class:`db.Submission`s to
                             include in the ZIP-file.
    """
    zf = store.get_bulk_archive(submissions,
                                zip_directory=zip_basename)
    attachment_filename = "{}--{}.zip".format(
        zip_basename, datetime.utcnow().strftime("%Y-%m-%d--%H-%M-%S"))

    # Mark the submissions that have been downloaded as such
    for submission in submissions:
        submission.downloaded = True
    db_session.commit()

    return send_file(zf.name, mimetype="application/zip",
                     attachment_filename=attachment_filename,
                     as_attachment=True)


def delete_collection(filesystem_id):
    # Delete the source's collection of submissions
    job = worker.enqueue(srm, store.path(filesystem_id))

    # Delete the source's reply keypair
    crypto_util.delete_reply_keypair(filesystem_id)

    # Delete their entry in the db
    source = get_source(filesystem_id)
    db_session.delete(source)
    db_session.commit()
    return job


def confirm_bulk_delete(filesystem_id, items_selected):
    return render_template('delete.html',
                           filesystem_id=filesystem_id,
                           source=g.source,
                           items_selected=items_selected)
