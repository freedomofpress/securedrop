from flask import redirect, url_for, request
from functools import wraps

from source_app.utils import logged_in


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not logged_in():
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function


def ignore_static(f):
    """Only executes the wrapped function if we're not loading
    a static resource."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.path.startswith('/static'):
            return  # don't execute the decorated function
        return f(*args, **kwargs)
    return decorated_function
