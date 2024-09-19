import datetime
import re
from pathlib import Path

import argon2
import flask
import models
from db import db
from encryption import EncryptionManager
from flask.testing import FlaskClient
from models import ARGON2_PARAMS
from source_user import SourceUser
from tests.utils import asynchronous, db_helper  # noqa: F401
from two_factor import TOTP

import redwood

JOURNALIST_SECRET_KEY_PATH = Path(__file__).parent.parent / "files" / "test_journalist_key.sec"
JOURNALIST_SECRET_KEY = JOURNALIST_SECRET_KEY_PATH.read_text()


def flaky_filter_xfail(err, *args):
    """
    Tell the pytest flaky plugin to not retry XFailed errors.

    If the test is expected to fail, let's not run it again.
    """
    return (
        f"{err[0].__class__.__module__}.{err[0].__class__.__qualname__}"
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


def extract_password(html: bytes) -> str:
    search = re.search(r'<input name="password" type="hidden" value="(.*?)">', html.decode())
    if search:
        return search.group(1)
    else:
        raise ValueError("Could not find password in HTML")


def prepare_password_change(app_test_client: FlaskClient, id: int, new_password: str) -> None:
    """A reimplementation of utils.set_pending_password() for tests"""
    with app_test_client.session_transaction() as session:
        session[f"pending_password_{id}"] = argon2.PasswordHasher(**ARGON2_PARAMS).hash(
            new_password
        )


def decrypt_as_journalist(ciphertext: bytes) -> bytes:
    return redwood.decrypt(
        ciphertext=ciphertext,
        secret_key=JOURNALIST_SECRET_KEY,
        passphrase="correcthorsebatterystaple",
    )


def create_legacy_gpg_key(
    manager: EncryptionManager, source_user: SourceUser, source: models.Source
) -> str:
    """Create a GPG key for the source, so we can test pre-Sequoia behavior"""
    # All reply keypairs will be "created" on the same day SecureDrop (then
    # Strongbox) was publicly released for the first time.
    # https://www.newyorker.com/news/news-desk/strongbox-and-aaron-swartz
    default_key_creation_date = datetime.date(2013, 5, 14)
    gen_key_input = manager.gpg().gen_key_input(
        passphrase=source_user.gpg_secret,
        name_email=source_user.filesystem_id,
        key_type="RSA",
        key_length=4096,
        name_real="Source Key",
        creation_date=default_key_creation_date.isoformat(),
        # '0' is the magic value that tells GPG's batch key generation not
        # to set an expiration date.
        expire_date="0",
    )
    result = manager.gpg().gen_key(gen_key_input)

    # Delete the Sequoia-generated keys
    source.pgp_public_key = None
    source.pgp_fingerprint = None
    source.pgp_secret_key = None
    db.session.add(source)
    db.session.commit()
    return result.fingerprint


# Helper function to extract a the session cookie from the cookiejar when testing as client
# Returns the session cookie value
def _session_from_cookiejar(cookie_jar, flask_app):
    return next(
        (cookie for cookie in cookie_jar if cookie.name == flask_app.config["SESSION_COOKIE_NAME"]),
        None,
    )
