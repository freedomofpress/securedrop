# -*- coding: utf-8 -*-
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
from sdconfig import SDConfig


def make_blueprint(config: SDConfig) -> Blueprint:
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
        if request.method == "POST":
            token = request.form["token"]
            if session.get_user().verify_token(token):
                flash(
                    gettext("Your two-factor credentials have been reset successfully."),
                    "notification",
                )
                return redirect(url_for("account.edit"))
            else:
                flash(
                    gettext("There was a problem verifying the two-factor code. Please try again."),
                    "error",
                )

        return render_template("account_new_two_factor.html", user=session.get_user())

    @view.route("/reset-2fa-totp", methods=["POST"])
    def reset_two_factor_totp() -> werkzeug.Response:
        session.get_user().is_totp = True
        session.get_user().regenerate_totp_shared_secret()
        db.session.commit()
        return redirect(url_for("account.new_two_factor"))

    @view.route("/reset-2fa-hotp", methods=["POST"])
    def reset_two_factor_hotp() -> Union[str, werkzeug.Response]:
        otp_secret = request.form.get("otp_secret", None)
        if otp_secret:
            if not validate_hotp_secret(session.get_user(), otp_secret):
                return render_template("account_edit_hotp_secret.html")
            session.get_user().set_hotp_secret(otp_secret)
            db.session.commit()
            return redirect(url_for("account.new_two_factor"))
        else:
            return render_template("account_edit_hotp_secret.html")

    return view
