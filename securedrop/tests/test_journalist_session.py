import json
from datetime import datetime, timedelta, timezone

import pytest
from flask import Response, url_for
from flask.sessions import session_json_serializer
from itsdangerous import URLSafeTimedSerializer
from redis import Redis
from tests.utils import _session_from_cookiejar, login_journalist, prepare_password_change
from tests.utils.api_helper import get_api_headers
from two_factor import TOTP

NEW_PASSWORD = "another correct horse battery staple generic passphrase"


@pytest.fixture
def redis(config):
    return Redis(**config.REDIS_KWARGS)


# Helper function to check if session cookie are properly signed
# Returns just the session id without signature
def _check_sig(session_cookie, journalist_app, api=False):
    if api:
        salt = "api_" + journalist_app.config["SESSION_SIGNER_SALT"]
    else:
        salt = journalist_app.config["SESSION_SIGNER_SALT"]

    signer = URLSafeTimedSerializer(journalist_app.secret_key, salt)
    return signer.loads(session_cookie)


# Helper function to get a session payload from redis
# Returns the unserialized session payload
def _get_session(sid, journalist_app, redis, api=False):
    if api:
        key = "api_" + journalist_app.config["SESSION_KEY_PREFIX"] + sid
    else:
        key = journalist_app.config["SESSION_KEY_PREFIX"] + sid

    return session_json_serializer.loads(redis.get(key))


# Test a standard login sequence
def test_session_login(journalist_app, test_journo, redis):
    # Given a test client and a valid journalist user
    with journalist_app.test_client() as app:
        # When sending a correct login request
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )

        # When checking the local session cookie jar
        session_cookie = _session_from_cookiejar(app._cookies, journalist_app)
        # Then there is a session cookie in it
        assert session_cookie is not None
        # Verify correct `SameSite` value was set on the cookie
        assert session_cookie.same_site == "Strict"

        # Then such cookie is properly signed
        sid = _check_sig(session_cookie.value, journalist_app)
        # Then such session cookie has a corresponding payload in redis
        redis_session = _get_session(sid, journalist_app, redis)
        ttl = redis.ttl(journalist_app.config["SESSION_KEY_PREFIX"] + sid)

        # Then the TTL of such key in redis conforms to the lifetime configuration
        assert (
            (journalist_app.config["SESSION_LIFETIME"] - 10)
            < ttl
            <= journalist_app.config["SESSION_LIFETIME"]
        )

        # Then the user id of the user who logged in is the same as the user id in session
        assert redis_session["uid"] == test_journo["id"]

        # Finally load the main page
        resp = app.get(url_for("main.index"))
        # And expect a successful status code
        assert resp.status_code == 200


# Test a standard session renewal sequence
def test_session_renew(journalist_app, test_journo, redis):
    # Given a test client and a valid journalist user
    with journalist_app.test_client() as app:
        # When sending a correct login request
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        # Then check session existence, signature, and redis payload
        session_cookie = _session_from_cookiejar(app._cookies, journalist_app)
        assert session_cookie is not None

        sid = _check_sig(session_cookie.value, journalist_app)
        redis_session = _get_session(sid, journalist_app, redis)
        # The `renew_count` must exists in the session payload and must be equal to the app config
        assert redis_session["renew_count"] == journalist_app.config["SESSION_RENEW_COUNT"]

        # When forcing the session TTL in redis to be below the threshold
        # Threshold for auto renew is less than 60*30
        redis.setex(
            name=journalist_app.config["SESSION_KEY_PREFIX"] + sid,
            value=session_json_serializer.dumps(redis_session),
            time=15 * 60,
        )
        # When doing a generic request to trigger the auto-renew
        resp = app.get(url_for("main.index"))
        # Then the session must still be valid
        assert resp.status_code == 200

        # Then the corresponding renew_count in redis must have been decreased
        redis_session = _get_session(sid, journalist_app, redis)
        assert redis_session["renew_count"] == (journalist_app.config["SESSION_RENEW_COUNT"] - 1)

        # Then the ttl must have been updated and the new lifetime must be > of app confing lifetime
        # (Bigger because there is also a variable amount of time in the threshold that is kept)
        ttl = redis.ttl(journalist_app.config["SESSION_KEY_PREFIX"] + sid)
        assert ttl > journalist_app.config["SESSION_LIFETIME"]


# Test a standard login then logout sequence
def test_session_logout(journalist_app, test_journo, redis):
    # Given a test client and a valid journalist user
    with journalist_app.test_client() as app:
        # When sending a correct login request
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        # Then check session as in the previous tests
        session_cookie = _session_from_cookiejar(app._cookies, journalist_app)
        assert session_cookie is not None

        sid = _check_sig(session_cookie.value, journalist_app)
        assert (redis.get(journalist_app.config["SESSION_KEY_PREFIX"] + sid)) is not None

        # When sending a logout request from a logged in journalist
        resp = app.post(url_for("main.logout"), follow_redirects=False)
        # Then it redirects to login
        assert resp.status_code == 302
        # Then the session no longer exists in redis
        assert (redis.get(journalist_app.config["SESSION_KEY_PREFIX"] + sid)) is None

        # Then a request to the index redirects back to login
        resp = app.get(url_for("main.index"), follow_redirects=False)
        assert resp.status_code == 302


# Test the user forced logout when an admin changes the user password
def test_session_admin_change_password_logout(journalist_app, test_journo, test_admin, redis):
    # Given a test client and a valid journalist user
    with journalist_app.test_client() as app:
        # When sending a correct login request
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        session_cookie = _session_from_cookiejar(app._cookies, journalist_app)
        assert session_cookie is not None
        # Then save the cookie for later
        cookie_val = session_cookie.value
        # Then also save the session id for later
        sid = _check_sig(session_cookie.value, journalist_app)
        assert (redis.get(journalist_app.config["SESSION_KEY_PREFIX"] + sid)) is not None

    # Given a another test client and a valid admin user
    with journalist_app.test_client() as admin_app:
        # When sending a valid login request as the admin user
        login_journalist(
            admin_app,
            test_admin["username"],
            test_admin["password"],
            test_admin["otp_secret"],
        )
        # When changing password of the journalist (non-admin) user
        prepare_password_change(admin_app, test_journo["id"], NEW_PASSWORD)
        resp = admin_app.post(
            url_for("admin.new_password", user_id=test_journo["id"]),
            data=dict(password=NEW_PASSWORD),
            follow_redirects=False,
        )
        # Then the password change has been successful
        assert resp.status_code == 302
        # Then the journalist (non-admin) user session does no longer exist in redis
        assert (redis.get(journalist_app.config["SESSION_KEY_PREFIX"] + sid)) is None

    with journalist_app.test_client() as app:
        # Add our original cookie back into the session, and try to re-use it
        app.set_cookie(
            key="js",
            value=cookie_val,
            httponly=True,
            path="/",
        )
        resp = app.get(url_for("main.index"), follow_redirects=False)
        # Then trying to reuse the same journalist user cookie fails and redirects
        assert resp.status_code == 302


# Test the forced logout when the user changes its password
def test_session_change_password_logout(journalist_app, test_journo, redis):
    # Given a test client and a valid journalist user
    with journalist_app.test_client() as app:
        # When sending a correct login request
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        # Then check session as the previous tests
        session_cookie = _session_from_cookiejar(app._cookies, journalist_app)
        assert session_cookie is not None

        sid = _check_sig(session_cookie.value, journalist_app)
        assert (redis.get(journalist_app.config["SESSION_KEY_PREFIX"] + sid)) is not None

        # When sending a self change password request
        prepare_password_change(app, test_journo["id"], NEW_PASSWORD)
        resp = app.post(
            url_for("account.new_password"),
            data=dict(
                current_password=test_journo["password"],
                token=TOTP(test_journo["otp_secret"]).now(),
                password=NEW_PASSWORD,
            ),
        )
        # Then the session is no longer valid
        assert resp.status_code == 302
        # Then the session no longer exists in redis
        assert (redis.get(journalist_app.config["SESSION_KEY_PREFIX"] + sid)) is None

        # Then a request for the index redirects back to login
        resp = app.get(url_for("main.index"), follow_redirects=False)
        assert resp.status_code == 302


# Test that the session id is regenerated after a valid login
def test_session_login_regenerate_sid(journalist_app, test_journo):
    # Given a test client and a valid journalist user
    with journalist_app.test_client() as app:
        # When sending an anonymous get request
        resp = app.get(url_for("main.login"))
        # Then check the response code is correct
        assert resp.status_code == 200

        # Given a valid unauthenticated session id from the previous request
        session_cookie_pre_login = _session_from_cookiejar(app._cookies, journalist_app)
        assert session_cookie_pre_login is not None

        # When sending a valid login request using the same client (same cookiejar)
        login_journalist(
            app, test_journo["username"], test_journo["password"], test_journo["otp_secret"]
        )
        session_cookie_post_login = _session_from_cookiejar(app._cookies, journalist_app)
        # Then the two session ids are different as the session id gets regenerated post login
        assert session_cookie_post_login != session_cookie_pre_login


# Test a standard `get_token` API login
def test_session_api_login(journalist_app, test_journo, redis):
    # Given a test client and a valid journalist user
    with journalist_app.test_client() as app:
        # When sending a `get_token` request to the API with valid creds
        resp = app.post(
            url_for("api.get_token"),
            data=json.dumps(
                {
                    "username": test_journo["username"],
                    "passphrase": test_journo["password"],
                    "one_time_code": TOTP(test_journo["otp_secret"]).now(),
                }
            ),
            headers=get_api_headers(),
        )

        # Then the API token is issued and returned with the correct journalist id
        assert resp.json["journalist_uuid"] == test_journo["uuid"]
        assert resp.status_code == 200

        # Then such token is properly signed
        sid = _check_sig(resp.json["token"], journalist_app, api=True)
        redis_session = _get_session(sid, journalist_app, redis, api=True)
        # Then the session id in redis match that of the credentials
        assert redis_session["uid"] == test_journo["id"]

        # Then the ttl of the session in redis is lower than the lifetime configured in the app
        ttl = redis.ttl("api_" + journalist_app.config["SESSION_KEY_PREFIX"] + sid)
        assert (
            (journalist_app.config["SESSION_LIFETIME"] - 10)
            < ttl
            <= journalist_app.config["SESSION_LIFETIME"]
        )

        # Then the expiration date returned in `get_token` response also conforms to the same rules
        assert (
            datetime.now(timezone.utc)
            < datetime.strptime(resp.json["expiration"], "%Y-%m-%dT%H:%M:%S.%f%z")
            < (
                datetime.now(timezone.utc)
                + timedelta(seconds=journalist_app.config["SESSION_LIFETIME"])
            )
        )

        # When querying the endpoint that return the corrent user with the token
        response = app.get(
            url_for("api.get_current_user"), headers=get_api_headers(resp.json["token"])
        )
        # Then the request is successful and the correct journalist id is returned
        assert response.status_code == 200
        assert response.json["uuid"] == test_journo["uuid"]


# test a standard login then logout from API
def test_session_api_logout(journalist_app, test_journo, redis):
    # Given a test client and a valid journalist user
    with journalist_app.test_client() as app:
        # When sending a valid login request and asking an API token
        resp = app.post(
            url_for("api.get_token"),
            data=json.dumps(
                {
                    "username": test_journo["username"],
                    "passphrase": test_journo["password"],
                    "one_time_code": TOTP(test_journo["otp_secret"]).now(),
                }
            ),
            headers=get_api_headers(),
        )

        # Then the token is issued successfully with the correct attributed
        assert resp.json["journalist_uuid"] == test_journo["uuid"]
        assert resp.status_code == 200
        token = resp.json["token"]
        sid = _check_sig(token, journalist_app, api=True)

        # When querying the endpoint for the current user information
        resp = app.get(url_for("api.get_current_user"), headers=get_api_headers(token))
        # Then the request is successful and the returned id matches the creds journalist id
        assert resp.status_code == 200
        assert resp.json["uuid"] == test_journo["uuid"]

        # When sending a logout request using the API token
        resp = app.post(url_for("api.logout"), headers=get_api_headers(token))
        # Then it is successful
        assert resp.status_code == 200
        # Then the token and the corresponding payload no longer exist in redis
        assert (redis.get("api_" + journalist_app.config["SESSION_KEY_PREFIX"] + sid)) is None

        # When sending an authenticated request with the deleted token
        resp = app.get(url_for("api.get_current_user"), headers=get_api_headers(token))
        # Then the request is unsuccessful
        assert resp.status_code == 403


# Test a few cases of valid session token with bad signatures
def test_session_bad_signature(journalist_app, test_journo):
    # Given a test client and a valid journalist user
    with journalist_app.test_client() as app:
        # When sending a valid login request and asking an API token
        resp = app.post(
            url_for("api.get_token"),
            data=json.dumps(
                {
                    "username": test_journo["username"],
                    "passphrase": test_journo["password"],
                    "one_time_code": TOTP(test_journo["otp_secret"]).now(),
                }
            ),
            headers=get_api_headers(),
        )

        # Then the request is successful and the uid matched the creds one
        assert resp.json["journalist_uuid"] == test_journo["uuid"]
        assert resp.status_code == 200

        # Given the valid token in the response
        token = resp.json["token"]
        # When checking the signature and sreipping it
        sid = _check_sig(token, journalist_app, api=True)

        # When requesting an authenticated endpoint with a valid unsigned token
        resp = app.get(url_for("api.get_current_user"), headers=get_api_headers(sid))
        # Then the request is refused
        assert resp.status_code == 403

        # When requesting an authenticated endpoint with a valid unsigned token with a trailing dot
        resp = app.get(url_for("api.get_current_user"), headers=get_api_headers(sid + "."))
        # Then the request is refused
        assert resp.status_code == 403

        # Given the correct app secret key and a wrong salt
        signer = URLSafeTimedSerializer(journalist_app.secret_key, "wrong_salt")
        # Given a valid token signed with the correct secret key and the wrong salt
        token_wrong_salt = signer.dumps(sid)

        # When requesting an authenticated endpoint with a valid token signed with the wrong salt
        resp = app.get(url_for("api.get_current_user"), headers=get_api_headers(token_wrong_salt))
        # Then the request is refused
        assert resp.status_code == 403

        # Given the correct app secret and the Journalist Interface salt
        signer = URLSafeTimedSerializer(
            journalist_app.secret_key, journalist_app.config["SESSION_SIGNER_SALT"]
        )
        # Given a valid token signed with the corrects secret key and the Journalist Interface salt
        token_not_api_salt = signer.dumps(sid)

        # When requesting an authenticated endpoint with such token
        resp = app.get(url_for("api.get_current_user"), headers=get_api_headers(token_not_api_salt))
        # Then the request is refused since the JI salt is not valid for the API
        assert resp.status_code == 403

        # When sending again an authenticated request with the original, valid, signed token
        resp = app.get(url_for("api.get_current_user"), headers=get_api_headers(token))
        # Then the request is successful
        assert resp.status_code == 200
        assert resp.json["uuid"] == test_journo["uuid"]


# Context: there are many cases in which as users may logout or be forcibly logged out.
# For the latter case, a user session is destroyed by an admin when a password change is
# enforced or when the user is deleted. When that happens, the session gets deleted from redis.
# What could happen is that if a user session is deleted between open_session() and save_session(),
# then the session might be restored and the admin deletion might fail.
# To avoid this, save_session() uses a setxx call, which writes in redis only if the key exists.
# This does not apply when the session is new or is being regenerated.
# Test that a deleted session cannot be rewritten by a race condition
def test_session_race_condition(mocker, journalist_app, test_journo, redis):
    # Given a test client and a valid journalist user
    with journalist_app.test_request_context() as app:
        # When manually creating a session in the context
        session = journalist_app.session_interface.open_session(journalist_app, app.request)
        assert session.sid is not None
        # When manually setting the journalist uid in session
        session["uid"] = test_journo["id"]

        # When manually building a Flask response object
        app.response = Response()
        # When manually calling save_session() to write the session in redis
        journalist_app.session_interface.save_session(journalist_app, session, app.response)
        # Then the session gets written in redis
        assert redis.get(journalist_app.config["SESSION_KEY_PREFIX"] + session.sid) is not None

        # When manually adding the created session token in the request cookies
        app.request.cookies = {journalist_app.config["SESSION_COOKIE_NAME"]: session.token}
        # When getting the session object by supplying a request context to open_session()
        session2 = journalist_app.session_interface.open_session(journalist_app, app.request)
        # Then the properties of the two sessions are the same
        # (They are indeed the same session)
        assert session2.sid == session.sid
        assert session2["uid"] == test_journo["id"]
        # When setting the modified properties to issue a write in redis
        # (To force entering the redis set xx case)
        session.modified = True
        session.new = False
        session.to_regenerate = False
        # When deleting the original session token and object from redis
        redis.delete(journalist_app.config["SESSION_KEY_PREFIX"] + session.sid)
        # Then the session_save() fails since the original object no longer exists
        journalist_app.session_interface.save_session(journalist_app, session, app.response)
        assert redis.get(journalist_app.config["SESSION_KEY_PREFIX"] + session.sid) is None
