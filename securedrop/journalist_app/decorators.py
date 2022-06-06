# -*- coding: utf-8 -*-
from functools import wraps
from typing import Any, Callable

from flask import flash, redirect, url_for
from flask_babel import gettext
from journalist_app.sessions import session


def admin_required(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if session.logged_in() and session.get_user().is_admin:
            return func(*args, **kwargs)
        flash(gettext("Only admins can access this page."), "notification")
        return redirect(url_for("main.index"))

    return wrapper
