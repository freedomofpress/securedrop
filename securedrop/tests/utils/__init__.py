import flask
import models
from db import db
from flask.testing import FlaskClient
from tests.utils import asynchronous, db_helper  # noqa: F401
from two_factor import TOTP


def flaky_filter_xfail(err, *args):
    """
    Tell the pytest flaky plugin to not retry XFailed errors.

    If the test is expected to fail, let's not run it again.
    """
    return (
        "{}.{}".format(err[0].__class__.__module__, err[0].__class__.__qualname__)
        == "_pytest.outcomes.XFailed"
    )


def _reset_journalist_last_token(username: str) -> None:
    # This function only works if there's an existing app context
    assert flask.current_app

    user = db.session.query(models.Journalist).filter_by(username=username).one()
    user.last_token = None
    db.session.commit()


def login_journalist(
    app_test_client: FlaskClient,
    username: str,
    password: str,
    otp_secret: str,
) -> None:
    """Log the journalist in, bypass login hardening measures in order to facilitate testing."""
    # Remove the last_token entry for this user so that the login here can succeed
    # instead of being blocked due to 2fa token reuse
    _reset_journalist_last_token(username)

    # Perform the login
    resp = app_test_client.post(
        "/login",
        data={
            "username": username,
            "password": password,
            "token": TOTP(otp_secret).now(),
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    # Ensure the user got a session
    from journalist_app.sessions import session

    assert session.get_user() is not None

    _reset_journalist_last_token(username)
