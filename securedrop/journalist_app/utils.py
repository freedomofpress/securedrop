# -*- coding: utf-8 -*-

from flask import g


def logged_in():
    # When a user is logged in, we push their user ID (database primary key)
    # into the session. setup_g checks for this value, and if it finds it,
    # stores a reference to the user's Journalist object in g.
    #
    # This check is good for the edge case where a user is deleted but still
    # has an active session - we will not authenticate a user if they are not
    # in the database.
    return bool(g.get('user', None))
