# -*- coding: utf-8 -*-
from functools import wraps
from typing import Any, Callable

from flask import flash, g, redirect, url_for
from flask_babel import gettext
from journalist_app.utils import logged_in


def admin_required(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if logged_in() and g.user.is_admin:
            return func(*args, **kwargs)
        flash(gettext("Only admins can access this page."), "notification")
        return redirect(url_for("main.index"))

    return wrapper
