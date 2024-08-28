from base64 import b32encode
from binascii import unhexlify

import pytest
from db import db
from flask import url_for
from journalist_app.sessions import session
from models import Journalist
from tests.utils import db_helper, login_journalist
from tests.utils.instrument import InstrumentedApp
from two_factor import HOTP, TOTP, OtpTokenInvalid


class TestTwoFactorInJournalistApp:
    def test_rejects_already_used_totp_token(self, journalist_app, test_journo):
        # Given a journalist that previously logged in using a specific 2fa token
        token = TOTP(test_journo["otp_secret"]).now()
        with journalist_app.test_client() as app:
            resp1 = app.post(
                url_for("main.login"),
                data=dict(
                    username=test_journo["username"],
                    password=test_journo["password"],
                    token=token,
                ),
                follow_redirects=True,
            )
            assert resp1.status_code == 200

            resp2 = app.post(url_for("main.logout"), follow_redirects=True)
            assert resp2.status_code == 200

        with journalist_app.app_context():
            journo = Journalist.query.get(test_journo["id"])
            assert journo.last_token == token

        # When they try to login again using the same 2fa token
        with journalist_app.test_client() as app:
            resp = app.post(
                url_for("main.login"),
                data=dict(
                    username=test_journo["username"],
                    password=test_journo["password"],
                    token=token,
                ),
            )

            # Then a login error is displayed
            assert resp.status_code == 200
            text = resp.data.decode("utf-8")
            assert "Login failed" in text

    def test_rejects_already_used_totp_token_with_padding(self, journalist_app, test_journo):
        # Given a journalist that previously logged in using a specific 2fa token
        token = TOTP(test_journo["otp_secret"]).now()
        with journalist_app.app_context():
            Journalist.login(test_journo["username"], test_journo["password"], token)

            # When they try to login again using the same token but with spaces added to the token
            token_for_second_login = token + "   "

            # Then it fails
            with pytest.raises(OtpTokenInvalid, match="already used"):
                Journalist.login(
                    test_journo["username"], test_journo["password"], token_for_second_login
                )

    def test_rejects_already_used_totp_token_after_failed_login(self, journalist_app, test_journo):
        # Given a journalist that previously logged in using a specific 2fa token
        token = TOTP(test_journo["otp_secret"]).now()
        with journalist_app.app_context():
            Journalist.login(test_journo["username"], test_journo["password"], token)

            # And they later tried to login using an invalid 2fa token
            invalid_token = "000000"
            with pytest.raises(OtpTokenInvalid):
                Journalist.login(test_journo["username"], test_journo["password"], invalid_token)

            # When they try to login again by reusing the initial/valid 2fa token
            # Then it fails with the right exception: the last_used_token in the DB was not
            #  overwritten by the token from the invalid login attempt
            with pytest.raises(OtpTokenInvalid, match="already used"):
                Journalist.login(test_journo["username"], test_journo["password"], token)

    @pytest.mark.parametrize("otp_secret", ["", "GARBAGE", "notbase32:&&&&aaa" "JHCOGO7VCER3EJ4"])
    def test_rejects_user_with_invalid_otp_secret(self, journalist_app, otp_secret):
        # Given a journalist that has an invalid OTP secret
        with journalist_app.app_context():
            new_username = "badotp" + otp_secret
            user, password = db_helper.init_journalist(is_admin=False)
            user.otp_secret = otp_secret
            user.username = new_username
            db.session.add(user)
            db.session.commit()

        # When they try to login
        with journalist_app.test_client() as app, InstrumentedApp(app) as ins:
            resp = app.post(
                url_for("main.login"),
                data={
                    "username": new_username,
                    "password": password,
                    "token": "705334",
                },
                follow_redirects=True,
            )

            # It fails and they didn't get a session
            assert resp.status_code == 200
            assert session.get_user() is None

            # And the corresponding error messages was displayed
            assert len(ins.flashed_messages) == 1
            assert "2FA details are invalid" in ins.flashed_messages[0][0]

    def test_can_login_after_regenerating_hotp(self, journalist_app, test_journo):
        # Given a journalist logged into the journalist app
        with journalist_app.test_client() as app:
            resp = app.post(
                "/login",
                data=dict(
                    username=test_journo["username"],
                    password=test_journo["password"],
                    token=TOTP(test_journo["otp_secret"]).now(),
                ),
            )
            assert resp.status_code == 302

            # Who goes to the page to reset their 2fa as HOTP
            otp_secret = "0123456789abcdef0123456789abcdef01234567"
            b32_otp_secret = b32encode(unhexlify(otp_secret)).decode("ascii")
            resp = app.post("/account/reset-2fa-hotp", data=dict(otp_secret=otp_secret))
            assert resp.status_code == 200
            assert (
                '<form id="check-token" method="post" action="/account/verify-2fa-hotp">'
                in resp.data.decode()
            )

            with InstrumentedApp(journalist_app) as ins:
                # And they successfully confirm the reset
                app.post(
                    "/account/verify-2fa-hotp", data=dict(token=HOTP(b32_otp_secret).generate(0))
                )
                ins.assert_message_flashed(
                    "Your two-factor credentials have been reset successfully.", "notification"
                )

            # And they then log out
            resp = app.post("/logout")
            assert resp.status_code == 302

        # When they later try to login using a 2fa token based on their new HOTP secret
        with journalist_app.test_client() as app, InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                "/login",
                data=dict(
                    username=test_journo["username"],
                    password=test_journo["password"],
                    token=HOTP(b32_otp_secret).generate(1),
                ),
            )

            # Then it succeeds
            ins.assert_redirects(resp, "/")


class TestTwoFactorInAdminApp:
    def test_rejects_invalid_token_in_new_user_2fa_page(self, journalist_app, test_admin):
        """Regression test for https://github.com/freedomofpress/securedrop/pull/1692"""
        # Given an admin logged into the admin app
        with journalist_app.test_client() as app:
            login_journalist(
                app,
                test_admin["username"],
                test_admin["password"],
                test_admin["otp_secret"],
            )

            # When they try to submit an invalid token for setting up 2fa for a new user
            invalid_token = "000000"
            with InstrumentedApp(journalist_app) as ins:
                resp = app.post(
                    url_for("admin.new_user_two_factor_totp"),
                    data=dict(
                        token=invalid_token,
                        otp_secret=test_admin["otp_secret"],
                        userid=test_admin["id"],
                    ),
                )

                # Then the corresponding error message is displayed
                assert resp.status_code == 200
                ins.assert_message_flashed(
                    "There was a problem verifying the two-factor code. Please try again.",
                    "error",
                )

    def test_rejects_invalid_token_in_account_2fa_page(self, journalist_app, test_journo):
        """Regression test for https://github.com/freedomofpress/securedrop/pull/1692"""
        # Given an admin logged into the admin app
        with journalist_app.test_client() as app:
            login_journalist(
                app,
                test_journo["username"],
                test_journo["password"],
                test_journo["otp_secret"],
            )

            # When they try to submit an invalid token for setting up 2fa for themselves
            invalid_token = "000000"
            with InstrumentedApp(journalist_app) as ins:
                resp = app.post(
                    url_for("account.new_two_factor_totp"),
                    data=dict(token=invalid_token, otp_secret=test_journo["otp_secret"]),
                )

                # Then the corresponding error message is displayed
                assert resp.status_code == 200
                ins.assert_message_flashed(
                    "There was a problem verifying the two-factor code. Please try again.",
                    "error",
                )
