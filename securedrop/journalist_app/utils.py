# -*- coding: utf-8 -*-

from flask import g, flash, current_app, abort
from flask_babel import gettext

from db import db_session, get_one_or_else, Source


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
