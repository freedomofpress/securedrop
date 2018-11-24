# -*- coding: utf-8 -*-

from datetime import datetime
from flask import (g, flash, current_app, abort, send_file, redirect, url_for,
                   render_template, Markup, sessions, request)
from flask_babel import gettext, ngettext
import hashlib
from sqlalchemy.sql.expression import false

import i18n
import worker

from db import db
from models import (get_one_or_else, Source, Journalist,
                    InvalidUsernameException, WrongPasswordException,
                    LoginThrottledException, BadTokenException, SourceStar,
                    PasswordError, Submission)
from rm import srm

import typing
# https://www.python.org/dev/peps/pep-0484/#runtime-or-type-checking
if typing.TYPE_CHECKING:
    # flake8 can not understand type annotation yet.
    # That is why all type annotation relative import
    # statements has to be marked as noqa.
    # http://flake8.pycqa.org/en/latest/user/error-codes.html?highlight=f401
    from sdconfig import SDConfig  # noqa: F401


def logged_in():
    # type: () -> bool
    # When a user is logged in, we push their user ID (database primary key)
    # into the session. setup_g checks for this value, and if it finds it,
    # stores a reference to the user's Journalist object in g.
    #
    # This check is good for the edge case where a user is deleted but still
    # has an active session - we will not authenticate a user if they are not
    # in the database.
    return bool(g.get('user', None))


def commit_account_changes(user):
    if db.session.is_modified(user):
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            flash(gettext(
                "An unexpected error occurred! Please "
                  "inform your admin."), "error")
            current_app.logger.error("Account changes for '{}' failed: {}"
                                     .format(user, e))
            db.session.rollback()
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
                        "Please wait for a new code from your two-factor token"
                        " or application before trying again.")
            except Exception:
                pass

        flash(login_flashed_msg, "error")
        return None


def validate_hotp_secret(user, otp_secret):
    """
    Validates and sets the HOTP provided by a user
    :param user: the change is for this instance of the User object
    :param otp_secret: the new HOTP secret
    :return: True if it validates, False if it does not
    """
    try:
        user.set_hotp_secret(otp_secret)
    except TypeError as e:
        if "Non-hexadecimal digit found" in str(e):
            flash(gettext(
                "Invalid secret format: "
                "please only submit letters A-F and numbers 0-9."),
                  "error")
            return False
        elif "Odd-length string" in str(e):
            flash(gettext(
                "Invalid secret format: "
                "odd-length secret. Did you mistype the secret?"),
                  "error")
            return False
        else:
            flash(gettext(
                "An unexpected error occurred! "
                "Please inform your admin."), "error")
            current_app.logger.error(
                "set_hotp_secret '{}' (id {}) failed: {}".format(
                    otp_secret, user.id, e))
            return False
    return True


def download(zip_basename, submissions):
    """Send client contents of ZIP-file *zip_basename*-<timestamp>.zip
    containing *submissions*. The ZIP-file, being a
    :class:`tempfile.NamedTemporaryFile`, is stored on disk only
    temporarily.

    :param str zip_basename: The basename of the ZIP-file download.

    :param list submissions: A list of :class:`models.Submission`s to
                             include in the ZIP-file.
    """
    zf = current_app.storage.get_bulk_archive(submissions,
                                              zip_directory=zip_basename)
    attachment_filename = "{}--{}.zip".format(
        zip_basename, datetime.utcnow().strftime("%Y-%m-%d--%H-%M-%S"))

    # Mark the submissions that have been downloaded as such
    for submission in submissions:
        submission.downloaded = True
    db.session.commit()

    return send_file(zf.name, mimetype="application/zip",
                     attachment_filename=attachment_filename,
                     as_attachment=True)


def delete_file(filesystem_id, filename, file_object):
    file_path = current_app.storage.path(filesystem_id, filename)
    worker.enqueue(srm, file_path)
    db.session.delete(file_object)
    db.session.commit()


def bulk_delete(filesystem_id, items_selected):
    for item in items_selected:
        delete_file(filesystem_id, item.filename, item)

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
        db.session.add(source_star)


def make_star_false(filesystem_id):
    source = get_source(filesystem_id)
    if not source.star:
        source_star = SourceStar(source)
        db.session.add(source_star)
        db.session.commit()
    source.star.starred = False


def col_star(cols_selected):
    for filesystem_id in cols_selected:
        make_star_true(filesystem_id)

    db.session.commit()
    return redirect(url_for('main.index'))


def col_un_star(cols_selected):
    for filesystem_id in cols_selected:
        make_star_false(filesystem_id)

    db.session.commit()
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
    # type: (SDConfig) -> str
    while True:
        password = current_app.crypto_util.genrandomid(
            7,
            i18n.get_language(config))
        try:
            Journalist.check_password_acceptable(password)
            return password
        except PasswordError:
            continue


def delete_collection(filesystem_id):
    # Delete the source's collection of submissions
    job = worker.enqueue(srm, current_app.storage.path(filesystem_id))

    # Delete the source's reply keypair
    current_app.crypto_util.delete_reply_keypair(filesystem_id)

    # Delete their entry in the db
    source = get_source(filesystem_id)
    db.session.delete(source)
    db.session.commit()
    return job


def set_diceware_password(user, password):
    try:
        user.set_password(password)
    except PasswordError:
        flash(gettext(
            'You submitted a bad password! Password not changed.'), 'error')
        return

    try:
        db.session.commit()
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


def serve_file_with_etag(source, filename):
    response = send_file(current_app.storage.path(source.filesystem_id,
                                                  filename),
                         mimetype="application/pgp-encrypted",
                         as_attachment=True,
                         add_etags=False)  # Disable Flask default ETag

    response.direct_passthrough = False
    response.headers['Etag'] = '"sha256:{}"'.format(
        hashlib.sha256(response.get_data()).hexdigest())
    return response


class JournalistInterfaceSessionInterface(
        sessions.SecureCookieSessionInterface):
    """A custom session interface that skips storing sessions for api requests but
    otherwise just uses the default behaviour."""
    def save_session(self, app, session, response):
        # If this is an api request do not save the session
        if request.path.split("/")[1] == "api":
            return
        else:
            super(JournalistInterfaceSessionInterface, self).save_session(
                app, session, response)
