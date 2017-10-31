# -*- coding: utf-8 -*-

from flask import g, flash, current_app, abort
from flask_babel import gettext, ngettext

from db import (db_session, get_one_or_else, Source, Journalist,
                InvalidUsernameException, WrongPasswordException,
                LoginThrottledException, BadTokenException)


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
