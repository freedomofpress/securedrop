from flask import session


def logged_in():
    return 'logged_in' in session
