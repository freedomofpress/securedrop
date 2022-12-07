from pyotp import TOTP

from . import asynchronous
from . import db_helper


def flaky_filter_xfail(err, *args):
    """
    Tell the pytest flaky plugin to not retry XFailed errors.

    If the test is expected to fail, let's not run it again.
    """
    return "_pytest.outcomes.XFailed" == "{}.{}".format(
        err[0].__class__.__module__, err[0].__class__.__qualname__
    )


def login_user(app, test_user):
    resp = app.post(
        "/login",
        data={
            "username": test_user["username"],
            "password": test_user["password"],
            "token": TOTP(test_user["otp_secret"]).now(),
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert test_user["username"] in resp.data.decode("utf-8")
