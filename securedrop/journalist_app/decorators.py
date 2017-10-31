# -*- coding: utf-8 -*-

from flask import redirect, url_for
from functools import wraps

from journalist_app.utils import logged_in


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not logged_in():
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper
