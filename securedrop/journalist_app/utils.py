# -*- coding: utf-8 -*-

from flask import g, flash, current_app
from flask_babel import gettext

from db import db_session


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
