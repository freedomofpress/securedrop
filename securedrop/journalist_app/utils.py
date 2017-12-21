# -*- coding: utf-8 -*-

from datetime import datetime
from flask import (g, flash, current_app, abort, send_file, redirect, url_for,
                   render_template, Markup)
from flask_babel import gettext, ngettext
from sqlalchemy.sql.expression import false

import crypto_util
import i18n
import store
import worker

from db import (db_session, get_one_or_else, Source, Journalist,
                InvalidUsernameException, WrongPasswordException,
                LoginThrottledException, BadTokenException, SourceStar,
                PasswordError, Submission)
from rm import srm


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
                "An unexpected error occurred! Please "
                  "inform your administrator."), "error")
            current_app.logger.error("Account changes for '{}' failed: {}"
                                     .format(user, e))
            db_session.rollback()
        else:
            flash(gettext("Account updated."), "success")


def get_source(filesystem_id):
    """Return a Source object, representing the database row, for the source
    with the `filesystem_id`"""
    source = None
    query = Source.query.filter(Source.filesystem_id == filesystem_id)
    source = get_one_or_else(query, current_app.logger, abort)

    return source


def validate_user(username, password, token, error_message=None):
    """
    Validates the user by calling the login and handling exceptions
    :param username: Username
    :param password: Password
    :param token: Two-factor authentication token
    :param error_message: Localized error message string to use on failure
    :return: Journalist user object if successful, None otherwise.
    """
    try:
        return Journalist.login(username, password, token)
    except (InvalidUsernameException,
            BadTokenException,
            WrongPasswordException,
            LoginThrottledException) as e:
        current_app.logger.error("Login for '{}' failed: {}".format(
            username, e))
        if not error_message:
            error_message = gettext('Login failed.')
        login_flashed_msg = error_message

        if isinstance(e, LoginThrottledException):
            login_flashed_msg += " "
            period = Journalist._LOGIN_ATTEMPT_PERIOD
            # ngettext is needed although we always have period > 1
            # see https://github.com/freedomofpress/securedrop/issues/2422
            login_flashed_msg += ngettext(
                "Please wait at least {seconds} second "
                "before logging in again.",
                "Please wait at least {seconds} seconds "
                "before logging in again.", period).format(seconds=period)
        else:
            try:
                user = Journalist.query.filter_by(
                    username=username).one()
                if user.is_totp:
                    login_flashed_msg += " "
                    login_flashed_msg += gettext(
                        "Please wait for a new two-factor token"
                        " before trying again.")
            except:
                pass

        flash(login_flashed_msg, "error")
        return None


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


def bulk_delete(filesystem_id, items_selected):
    for item in items_selected:
        item_path = store.path(filesystem_id, item.filename)
        worker.enqueue(srm, item_path)
        db_session.delete(item)
    db_session.commit()

    flash(ngettext("Submission deleted.",
                   "{num} submissions deleted.".format(
                       num=len(items_selected)),
                   len(items_selected)), "notification")
    return redirect(url_for('col.col', filesystem_id=filesystem_id))


def confirm_bulk_delete(filesystem_id, items_selected):
    return render_template('delete.html',
                           filesystem_id=filesystem_id,
                           source=g.source,
                           items_selected=items_selected)


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


def col_star(cols_selected):
    for filesystem_id in cols_selected:
        make_star_true(filesystem_id)

    db_session.commit()
    return redirect(url_for('main.index'))


def col_un_star(cols_selected):
    for filesystem_id in cols_selected:
        make_star_false(filesystem_id)

    db_session.commit()
    return redirect(url_for('main.index'))


def col_delete(cols_selected):
    """deleting multiple collections from the index"""
    if len(cols_selected) < 1:
        flash(gettext("No collections selected for deletion."), "error")
    else:
        for filesystem_id in cols_selected:
            delete_collection(filesystem_id)
        num = len(cols_selected)
        flash(ngettext('{num} collection deleted', '{num} collections deleted',
                       num).format(num=num),
              "notification")

    return redirect(url_for('main.index'))


def make_password(config):
    while True:
        password = crypto_util.genrandomid(7, i18n.get_language(config))
        try:
            Journalist.check_password_acceptable(password)
            return password
        except PasswordError:
            continue


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


def col_download_unread(cols_selected):
    """Download all unread submissions from all selected sources."""
    submissions = []
    for filesystem_id in cols_selected:
        id = Source.query.filter(Source.filesystem_id == filesystem_id) \
                   .one().id
        submissions += Submission.query.filter(
            Submission.downloaded == false(),
            Submission.source_id == id).all()
    if submissions == []:
        flash(gettext("No unread submissions in selected collections."),
              "error")
        return redirect(url_for('main.index'))
    return download("unread", submissions)


def col_download_all(cols_selected):
    """Download all submissions from all selected sources."""
    submissions = []
    for filesystem_id in cols_selected:
        id = Source.query.filter(Source.filesystem_id == filesystem_id) \
                   .one().id
        submissions += Submission.query.filter(
            Submission.source_id == id).all()
    return download("all", submissions)
