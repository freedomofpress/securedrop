# -*- coding: utf-8 -*-
from typing import Union

import werkzeug
from flask import (Blueprint, render_template, request, g, redirect, url_for,
                   flash, session)
from flask_babel import gettext

from db import db
from journalist_app.utils import (make_password, set_diceware_password, set_name, validate_user,
                                  validate_hotp_secret)
from sdconfig import SDConfig


def make_blueprint(config: SDConfig) -> Blueprint:
    view = Blueprint('account', __name__)

    @view.route('/account', methods=('GET',))
    def edit() -> str:
        password = make_password(config)
        return render_template('edit_account.html',
                               password=password)

    @view.route('/change-name', methods=('POST',))
    def change_name() -> werkzeug.Response:
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        set_name(g.user, first_name, last_name)
        return redirect(url_for('account.edit'))

    @view.route('/new-password', methods=('POST',))
    def new_password() -> werkzeug.Response:
        user = g.user
        current_password = request.form.get('current_password')
        token = request.form.get('token')
        error_message = gettext('Incorrect password or two-factor code.')
        # If the user is validated, change their password
        if validate_user(user.username, current_password, token,
                         error_message):
            password = request.form.get('password')
            set_diceware_password(user, password)
            session.pop('uid', None)
            session.pop('expires', None)
            return redirect(url_for('main.login'))
        return redirect(url_for('account.edit'))

    @view.route('/2fa', methods=('GET', 'POST'))
    def new_two_factor() -> Union[str, werkzeug.Response]:
        if request.method == 'POST':
            token = request.form['token']
            if g.user.verify_token(token):
                flash(gettext("Your two-factor credentials have been reset successfully."),
                      "notification")
                return redirect(url_for('account.edit'))
            else:
                flash(gettext(
                    "There was a problem verifying the two-factor code. Please try again."),
                      "error")

        return render_template('account_new_two_factor.html', user=g.user)

    @view.route('/reset-2fa-totp', methods=['POST'])
    def reset_two_factor_totp() -> werkzeug.Response:
        g.user.is_totp = True
        g.user.regenerate_totp_shared_secret()
        db.session.commit()
        return redirect(url_for('account.new_two_factor'))

    @view.route('/reset-2fa-hotp', methods=['POST'])
    def reset_two_factor_hotp() -> Union[str, werkzeug.Response]:
        otp_secret = request.form.get('otp_secret', None)
        if otp_secret:
            if not validate_hotp_secret(g.user, otp_secret):
                return render_template('account_edit_hotp_secret.html')
            g.user.set_hotp_secret(otp_secret)
            db.session.commit()
            return redirect(url_for('account.new_two_factor'))
        else:
            return render_template('account_edit_hotp_secret.html')

    return view
