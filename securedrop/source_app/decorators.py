from typing import Any

from db import db

from flask import redirect, url_for, request, session
from functools import wraps

from typing import Callable

from source_app.utils import clear_session_and_redirect_to_logged_out_page
from source_app.session_manager import SessionManager, UserNotLoggedIn, \
    UserSessionExpired, UserHasBeenDeleted


def login_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        try:
            logged_in_source = SessionManager.get_logged_in_user(db_session=db.session)

        except (UserSessionExpired, UserHasBeenDeleted):
            return clear_session_and_redirect_to_logged_out_page(flask_session=session)

        except UserNotLoggedIn:
            return redirect(url_for("main.login"))

        return f(*args, **kwargs, logged_in_source=logged_in_source)
    return decorated_function


def ignore_static(f: Callable) -> Callable:
    """Only executes the wrapped function if we're not loading
    a static resource."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if request.path.startswith("/static"):
            return  # don't execute the decorated function
        return f(*args, **kwargs)
    return decorated_function
