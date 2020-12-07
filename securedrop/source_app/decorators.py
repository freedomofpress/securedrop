from typing import Any

from flask import redirect, url_for, request, session
from functools import wraps

from typing import Callable

from source_app.utils import redirect_to_index_and_show_logout_message
from source_app.session_manager import SessionManager, UserNotLoggedIn, \
    UserSessionExpired, UserHasBeenDeleted


def login_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        try:
            logged_in_source = SessionManager.get_logged_in_user()

        except UserHasBeenDeleted:
            SessionManager.log_user_out()
            return redirect(url_for("main.index"))

        except UserSessionExpired:
            SessionManager.log_user_out()
            return redirect_to_index_and_show_logout_message(session)

        except UserNotLoggedIn:
            return redirect(url_for("main.login"))

        return f(*args, **kwargs, logged_in_source=logged_in_source)
    return decorated_function


def ignore_static(f: Callable) -> Callable:
    """Only executes the wrapped function if we're not loading
    a static resource."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if request.path.startswith('/static'):
            return  # don't execute the decorated function
        return f(*args, **kwargs)
    return decorated_function
