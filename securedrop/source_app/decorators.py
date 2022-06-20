from typing import Any

from db import db

from flask import redirect, url_for, request, session
import werkzeug
from functools import wraps

from typing import Callable, Union, Optional

from source_app.utils import clear_session_and_redirect_to_logged_out_page
from source_app.session_manager import SessionManager, UserNotLoggedIn, \
    UserSessionExpired, UserHasBeenDeleted
from source_user import SourceUser


def _source_user() -> Optional[Union[SourceUser, werkzeug.Response]]:
    try:
        return SessionManager.get_logged_in_user(db_session=db.session)

    except (UserSessionExpired, UserHasBeenDeleted):
        return clear_session_and_redirect_to_logged_out_page(flask_session=session)

    except UserNotLoggedIn:
        return None


def login_possible(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Union[str, werkzeug.Response]:
        result = _source_user()
        if isinstance(result, werkzeug.Response):
            return result

        return f(*args, **kwargs, logged_in_source=result)
    return decorated_function


def login_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Union[str, werkzeug.Response]:
        result = _source_user()
        if result is None:
            return redirect(url_for("main.login"))
        elif isinstance(result, werkzeug.Response):
            return result

        return f(*args, **kwargs, logged_in_source=result)
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
