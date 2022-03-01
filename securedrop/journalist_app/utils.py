# -*- coding: utf-8 -*-
import binascii
from datetime import datetime, timezone
import os
from typing import Optional, List, Union, Any

import flask
import werkzeug
from flask import (g, flash, current_app, abort, send_file, redirect, url_for,
                   Markup, sessions, request, escape)
from flask_babel import gettext, ngettext
from sqlalchemy.exc import IntegrityError

from db import db
from encryption import EncryptionManager
from models import (
    BadTokenException,
    FirstOrLastNameError,
    InvalidPasswordLength,
    InvalidOTPSecretException,
    InvalidUsernameException,
    Journalist,
    LoginThrottledException,
    PasswordError,
    Reply,
    RevokedToken,
    SeenFile,
    SeenMessage,
    SeenReply,
    Source,
    SourceStar,
    Submission,
    WrongPasswordException,
    get_one_or_else,
    HOTP_SECRET_LENGTH,
)
from store import Storage, add_checksum_for_file


def logged_in() -> bool:
    # When a user is logged in, we push their user ID (database primary key)
    # into the session. setup_g checks for this value, and if it finds it,
    # stores a reference to the user's Journalist object in g.
    #
    # This check is good for the edge case where a user is deleted but still
    # has an active session - we will not authenticate a user if they are not
    # in the database.
    return bool(g.get('user', None))


def commit_account_changes(user: Journalist) -> None:
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


def get_source(filesystem_id: str, include_deleted: bool = False) -> Source:
    """
    Return the Source object with `filesystem_id`

    If `include_deleted` is False, only sources with a null `deleted_at` will
    be returned.
    """
    query = Source.query.filter(Source.filesystem_id == filesystem_id)
    if not include_deleted:
        query = query.filter_by(deleted_at=None)
    source = get_one_or_else(query, current_app.logger, abort)

    return source


def validate_user(
    username: str,
    password: Optional[str],
    token: Optional[str],
    error_message: Optional[str] = None
) -> Optional[Journalist]:
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
            InvalidOTPSecretException,
            BadTokenException,
            WrongPasswordException,
            LoginThrottledException,
            InvalidPasswordLength) as e:
        current_app.logger.error("Login for '{}' failed: {}".format(
            username, e))
        login_flashed_msg = error_message if error_message else gettext('Login failed.')

        if isinstance(e, LoginThrottledException):
            login_flashed_msg += " "
            period = Journalist._LOGIN_ATTEMPT_PERIOD
            # ngettext is needed although we always have period > 1
            # see https://github.com/freedomofpress/securedrop/issues/2422
            login_flashed_msg += ngettext(
                "Please wait at least {num} second before logging in again.",
                "Please wait at least {num} seconds before logging in again.",
                period
            ).format(num=period)
        elif isinstance(e, InvalidOTPSecretException):
            login_flashed_msg += ' '
            login_flashed_msg += gettext(
                "Your 2FA details are invalid"
                " - please contact an administrator to reset them.")
        else:
            try:
                user = Journalist.query.filter_by(
                    username=username).one()
                if user.is_totp:
                    login_flashed_msg += " "
                    login_flashed_msg += gettext(
                        "Please wait for a new code from your two-factor mobile"
                        " app or security key before trying again.")
            except Exception:
                pass

        flash(login_flashed_msg, "error")
        return None


def validate_hotp_secret(user: Journalist, otp_secret: str) -> bool:
    """
    Validates and sets the HOTP provided by a user
    :param user: the change is for this instance of the User object
    :param otp_secret: the new HOTP secret
    :return: True if it validates, False if it does not
    """
    strip_whitespace = otp_secret.replace(' ', '')
    secret_length = len(strip_whitespace)

    if secret_length != HOTP_SECRET_LENGTH:
        flash(ngettext(
                'HOTP secrets are 40 characters long - you have entered {num}.',
                'HOTP secrets are 40 characters long - you have entered {num}.',
                secret_length
            ).format(num=secret_length), "error")
        return False

    try:
        user.set_hotp_secret(otp_secret)
    except (binascii.Error, TypeError) as e:
        if "Non-hexadecimal digit found" in str(e):
            flash(gettext(
                "Invalid HOTP secret format: "
                "please only submit letters A-F and numbers 0-9."),
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


def mark_seen(targets: List[Union[Submission, Reply]], user: Journalist) -> None:
    """
    Marks a list of submissions or replies seen by the given journalist.
    """
    for t in targets:
        try:
            if isinstance(t, Submission):
                t.downloaded = True
                if t.is_file:
                    sf = SeenFile(file_id=t.id, journalist_id=user.id)
                    db.session.add(sf)
                elif t.is_message:
                    sm = SeenMessage(message_id=t.id, journalist_id=user.id)
                    db.session.add(sm)
                db.session.commit()
            elif isinstance(t, Reply):
                sr = SeenReply(reply_id=t.id, journalist_id=user.id)
                db.session.add(sr)
                db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            if 'UNIQUE constraint failed' in str(e):
                continue
            raise


def download(
    zip_basename: str,
    submissions: List[Union[Submission, Reply]],
    on_error_redirect: Optional[str] = None
) -> werkzeug.Response:
    """Send client contents of ZIP-file *zip_basename*-<timestamp>.zip
    containing *submissions*. The ZIP-file, being a
    :class:`tempfile.NamedTemporaryFile`, is stored on disk only
    temporarily.

    :param str zip_basename: The basename of the ZIP-file download.

    :param list submissions: A list of :class:`models.Submission`s to
                             include in the ZIP-file.
    """
    try:
        zf = Storage.get_default().get_bulk_archive(submissions, zip_directory=zip_basename)
    except FileNotFoundError:
        flash(
            ngettext(
                "Your download failed because the file could not be found. An admin can find "
                + "more information in the system and monitoring logs.",
                "Your download failed because a file could not be found. An admin can find "
                + "more information in the system and monitoring logs.",
                len(submissions)
            ),
            "error"
        )
        if on_error_redirect is None:
            on_error_redirect = url_for('main.index')
        return redirect(on_error_redirect)

    attachment_filename = "{}--{}.zip".format(
        zip_basename, datetime.now(timezone.utc).strftime("%Y-%m-%d--%H-%M-%S")
    )

    mark_seen(submissions, g.user)

    return send_file(
        zf.name,
        mimetype="application/zip",
        attachment_filename=attachment_filename,
        as_attachment=True,
    )


def delete_file_object(file_object: Union[Submission, Reply]) -> None:
    path = Storage.get_default().path(file_object.source.filesystem_id, file_object.filename)
    try:
        Storage.get_default().move_to_shredder(path)
    except ValueError as e:
        current_app.logger.error("could not queue file for deletion: %s", e)
        raise
    finally:
        db.session.delete(file_object)
        db.session.commit()


def bulk_delete(
    filesystem_id: str,
    items_selected: List[Union[Submission, Reply]]
) -> werkzeug.Response:
    deletion_errors = 0
    for item in items_selected:
        try:
            delete_file_object(item)
        except ValueError:
            deletion_errors += 1

    num_selected = len(items_selected)
    success_message = ngettext(
        "The item has been deleted.", "{num} items have been deleted.",
        num_selected).format(num=num_selected)

    flash(
        Markup(
           "<b>{}</b> {}".format(
               # Translators: Precedes a message confirming the success of an operation.
               escape(gettext("Success!")), escape(success_message))), 'success')

    if deletion_errors > 0:
        current_app.logger.error("Disconnected submission entries (%d) were detected",
                                 deletion_errors)
    return redirect(url_for('col.col', filesystem_id=filesystem_id))


def make_star_true(filesystem_id: str) -> None:
    source = get_source(filesystem_id)
    if source.star:
        source.star.starred = True
    else:
        source_star = SourceStar(source)
        db.session.add(source_star)


def make_star_false(filesystem_id: str) -> None:
    source = get_source(filesystem_id)
    if not source.star:
        source_star = SourceStar(source)
        db.session.add(source_star)
        db.session.commit()
    source.star.starred = False


def col_star(cols_selected: List[str]) -> werkzeug.Response:
    for filesystem_id in cols_selected:
        make_star_true(filesystem_id)

    db.session.commit()
    return redirect(url_for('main.index'))


def col_un_star(cols_selected: List[str]) -> werkzeug.Response:
    for filesystem_id in cols_selected:
        make_star_false(filesystem_id)

    db.session.commit()
    return redirect(url_for('main.index'))


def col_delete(cols_selected: List[str]) -> werkzeug.Response:
    """deleting multiple collections from the index"""
    if len(cols_selected) < 1:
        flash(gettext("No collections selected for deletion."), "error")
    else:
        now = datetime.now(timezone.utc)
        sources = Source.query.filter(Source.filesystem_id.in_(cols_selected))
        sources.update({Source.deleted_at: now}, synchronize_session="fetch")
        db.session.commit()

        num = len(cols_selected)

        success_message = ngettext(
            "The account and all data for the source have been deleted.",
            "The accounts and all data for {n} sources have been deleted.",
            num).format(n=num)

        flash(
            Markup(
               "<b>{}</b> {}".format(
                   # Translators: Precedes a message confirming the success of an operation.
                   escape(gettext("Success!")), escape(success_message))), 'success')

    return redirect(url_for('main.index'))


def delete_source_files(filesystem_id: str) -> None:
    """deletes submissions and replies for specified source"""
    source = get_source(filesystem_id, include_deleted=True)
    if source is not None:
        # queue all files for deletion and remove them from the database
        for f in source.collection:
            try:
                delete_file_object(f)
            except Exception:
                pass


def col_delete_data(cols_selected: List[str]) -> werkzeug.Response:
    """deletes store data for selected sources"""
    if len(cols_selected) < 1:
        flash(
            Markup(
                "<b>{}</b> {}".format(
                    # Translators: Error shown when a user has not selected items to act on.
                    escape(gettext("Nothing Selected")),
                    escape(gettext("You must select one or more items for deletion.")))
                ), 'error')
    else:

        for filesystem_id in cols_selected:
            delete_source_files(filesystem_id)

        flash(
            Markup(
                "<b>{}</b> {}".format(
                    # Translators: Precedes a message confirming the success of an operation.
                    escape(gettext("Success!")),
                    escape(gettext("The files and messages have been deleted.")))
                ), 'success')

    return redirect(url_for('main.index'))


def delete_collection(filesystem_id: str) -> None:
    """deletes source account including files and reply key"""
    # Delete the source's collection of submissions
    path = Storage.get_default().path(filesystem_id)
    if os.path.exists(path):
        Storage.get_default().move_to_shredder(path)

    # Delete the source's reply keypair
    EncryptionManager.get_default().delete_source_key_pair(filesystem_id)

    # Delete their entry in the db
    source = get_source(filesystem_id, include_deleted=True)
    db.session.delete(source)
    db.session.commit()


def purge_deleted_sources() -> None:
    """
    Deletes all Sources with a non-null `deleted_at` attribute.
    """
    sources = Source.query.filter(Source.deleted_at.isnot(None)).order_by(Source.deleted_at).all()
    if sources:
        current_app.logger.info("Purging deleted sources (%s)", len(sources))
    for source in sources:
        try:
            delete_collection(source.filesystem_id)
        except Exception as e:
            current_app.logger.error("Error deleting source %s: %s", source.uuid, e)


def set_name(user: Journalist, first_name: Optional[str], last_name: Optional[str]) -> None:
    try:
        user.set_name(first_name, last_name)
        db.session.commit()
        flash(gettext('Name updated.'), "success")
    except FirstOrLastNameError as e:
        flash(gettext('Name not updated: {message}').format(message=e), "error")


def set_diceware_password(user: Journalist, password: Optional[str]) -> bool:
    try:
        user.set_password(password)
    except PasswordError:
        flash(gettext(
            'The password you submitted is invalid. Password not changed.'), 'error')
        return False

    try:
        db.session.commit()
    except Exception:
        flash(gettext(
            'There was an error, and the new password might not have been '
            'saved correctly. To prevent you from getting locked '
            'out of your account, you should reset your password again.'),
            'error')
        current_app.logger.error('Failed to update a valid password.')
        return False

    # using Markup so the HTML isn't escaped
    flash(
        Markup(
            "<p>{message} <span><code>{password}</code></span></p>".format(
                message=Markup.escape(
                    gettext(
                        "Password updated. Don't forget to save it in your KeePassX database. "
                        "New password:"
                    )
                ),
                password=Markup.escape("" if password is None else password)
            )
        ),
        'success'
    )
    return True


def col_download_unread(cols_selected: List[str]) -> werkzeug.Response:
    """
    Download all unseen submissions from all selected sources.
    """
    unseen_submissions = (
        Submission.query.join(Source)
        .filter(
            Source.deleted_at.is_(None),
            Source.filesystem_id.in_(cols_selected)
        )
        .filter(~Submission.seen_files.any(), ~Submission.seen_messages.any())
        .all()
    )

    if len(unseen_submissions) == 0:
        flash(gettext("No unread submissions in selected collections."), "error")
        return redirect(url_for("main.index"))

    return download("unread", unseen_submissions)


def col_download_all(cols_selected: List[str]) -> werkzeug.Response:
    """Download all submissions from all selected sources."""
    submissions = []  # type: List[Union[Source, Submission]]
    for filesystem_id in cols_selected:
        id = Source.query.filter(Source.filesystem_id == filesystem_id) \
                         .filter_by(deleted_at=None).one().id
        submissions += Submission.query.filter(
            Submission.source_id == id).all()
    return download("all", submissions)


def serve_file_with_etag(db_obj: Union[Reply, Submission]) -> flask.Response:
    file_path = Storage.get_default().path(db_obj.source.filesystem_id, db_obj.filename)
    response = send_file(file_path,
                         mimetype="application/pgp-encrypted",
                         as_attachment=True,
                         add_etags=False)  # Disable Flask default ETag

    if not db_obj.checksum:
        add_checksum_for_file(db.session, db_obj, file_path)

    response.direct_passthrough = False
    response.headers['Etag'] = db_obj.checksum
    return response


class JournalistInterfaceSessionInterface(
        sessions.SecureCookieSessionInterface):
    """A custom session interface that skips storing sessions for api requests but
    otherwise just uses the default behaviour."""
    def save_session(self, app: flask.Flask, session: Any, response: flask.Response) -> None:
        # If this is an api request do not save the session
        if request.path.split("/")[1] == "api":
            return
        else:
            super(JournalistInterfaceSessionInterface, self).save_session(
                app, session, response)


def cleanup_expired_revoked_tokens() -> None:
    """Remove tokens that have now expired from the revoked token table."""

    revoked_tokens = db.session.query(RevokedToken).all()

    for revoked_token in revoked_tokens:
        if Journalist.validate_token_is_not_expired_or_invalid(revoked_token.token):
            pass  # The token has not expired, we must keep in the revoked token table.
        else:
            # The token is no longer valid, remove from the revoked token table.
            db.session.delete(revoked_token)

    db.session.commit()


def revoke_token(user: Journalist, auth_token: str) -> None:
    try:
        revoked_token = RevokedToken(token=auth_token, journalist_id=user.id)
        db.session.add(revoked_token)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        if "UNIQUE constraint failed: revoked_tokens.token" not in str(e):
            raise e
