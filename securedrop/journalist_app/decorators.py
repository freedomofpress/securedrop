# -*- coding: utf-8 -*-

from flask import redirect, url_for, flash, g
from flask_babel import gettext
from functools import wraps

from journalist_app.utils import logged_in


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if logged_in() and g.user.is_admin:
            return func(*args, **kwargs)
        # TODO: sometimes this gets flashed 2x (Chrome only?)
        flash(gettext("Only administrators can access this page."),
              "notification")
        return redirect(url_for('main.index'))
    return wrapper
