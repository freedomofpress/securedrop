from typing import Union

import werkzeug
from db import db
from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for
from flask_babel import gettext
from journalist_app.sessions import session
from journalist_app.utils import (
    set_diceware_password,
    set_name,
    validate_hotp_secret,
    validate_user,
)
from passphrases import PassphraseGenerator
from two_factor import OtpTokenInvalid, random_base32


_NEW_OTP_IS_TOTP = "new_otp_is_totp"
_NEW_OTP_SECRET = "new_otp_secret"


def make_blueprint() -> Blueprint:
    view = Blueprint("account", __name__)

    @view.route("/account", methods=("GET",))
    def edit() -> str:
        password = PassphraseGenerator.get_default().generate_passphrase(
            preferred_language=g.localeinfo.language
        )
        return render_template("edit_account.html", password=password)

    @view.route("/change-name", methods=("POST",))
    def change_name() -> werkzeug.Response:
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        set_name(session.get_user(), first_name, last_name)
        return redirect(url_for("account.edit"))

    @view.route("/new-password", methods=("POST",))
    def new_password() -> werkzeug.Response:
        user = session.get_user()
        current_password = request.form.get("current_password")
        token = request.form.get("token")
        error_message = gettext("Incorrect password or two-factor code.")
        # If the user is validated, change their password
        if validate_user(user.username, current_password, token, error_message):
            password = request.form.get("password")
            if set_diceware_password(user, password):
                current_app.session_interface.logout_user(user.id)  # type: ignore
                return redirect(url_for("main.login"))
        return redirect(url_for("account.edit"))

    @view.route("/2fa", methods=("GET", "POST"))
    def new_two_factor() -> Union[str, werkzeug.Response]:
        user = session.get_user()

        # Update the user with the new OTP secret, if set. If the user enters a valid token,
        # the new secret is committed. Otherwise, the secret is rolled back after the request
        # completes.
        if _NEW_OTP_IS_TOTP in session and _NEW_OTP_SECRET in session:
            if session[_NEW_OTP_IS_TOTP]:
                user.set_totp_secret(session[_NEW_OTP_SECRET])
            else:
                user.set_hotp_secret(session[_NEW_OTP_SECRET])

        if request.method == "POST":
            token = request.form["token"]

            try:
                session.get_user().verify_2fa_token(token)

                db.session.commit()
                flash(
                    gettext("Your two-factor credentials have been reset successfully."),
                    "notification",
                )
                return redirect(url_for("account.edit"))

            except OtpTokenInvalid:
                db.session.rollback()
                flash(
                    gettext("There was a problem verifying the two-factor code. Please try again."),
                    "error",
                )

        page = render_template("account_new_two_factor.html", user=session.get_user())
        db.session.rollback()
        return page

    @view.route("/reset-2fa-totp", methods=["POST"])
    def reset_two_factor_totp() -> werkzeug.Response:
        session[_NEW_OTP_IS_TOTP] = True
        session[_NEW_OTP_SECRET] = random_base32()
        return redirect(url_for("account.new_two_factor"))

    @view.route("/reset-2fa-hotp", methods=["POST"])
    def reset_two_factor_hotp() -> Union[str, werkzeug.Response]:
        otp_secret = request.form.get("otp_secret", None)
        if otp_secret:
            if not validate_hotp_secret(session.get_user(), otp_secret):
                return render_template("account_edit_hotp_secret.html")
            session[_NEW_OTP_IS_TOTP] = False
            session[_NEW_OTP_SECRET] = otp_secret
            return redirect(url_for("account.new_two_factor"))
        else:
            return render_template("account_edit_hotp_secret.html")

    return view
