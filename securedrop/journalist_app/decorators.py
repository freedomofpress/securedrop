# -*- coding: utf-8 -*-
from typing import Any

from flask import redirect, url_for, flash, g, session
from flask_babel import gettext
from functools import wraps
from typing import Any, Callable

from typing import Callable


def admin_required(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if session.logged_in() and session.get_user().is_admin:
            return func(*args, **kwargs)
        flash(gettext("Only admins can access this page."), "notification")
        return redirect(url_for("main.index"))

    return wrapper
