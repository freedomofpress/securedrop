from typing import Any

from flask import redirect, url_for, request
from functools import wraps

from typing import Callable

from source_app.utils import logged_in


def login_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not logged_in():
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function


def ignore_static(f: Callable) -> Callable:
    """Only executes the wrapped function if we're not loading
    a static resource."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if request.path.startswith("/static") or request.path == "/org-logo":
            return  # don't execute the decorated function
        return f(*args, **kwargs)
    return decorated_function
