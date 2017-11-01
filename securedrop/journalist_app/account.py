# -*- coding: utf-8 -*-

from flask import (Blueprint, render_template, request, g, redirect, url_for,
                   flash)
from flask_babel import gettext

from db import db_session
from journalist_app.decorators import login_required
from journalist_app.utils import (make_password, set_diceware_password,
                                  validate_user)


def make_blueprint(config):
    view = Blueprint('account', __name__)

    @view.route('/account', methods=('GET',))
    @login_required
    def edit():
        password = make_password()
        return render_template('edit_account.html',
                               password=password)

    @view.route('/new-password', methods=('POST',))
    @login_required
    def new_password():
        user = g.user
        current_password = request.form.get('current_password')
        token = request.form.get('token')
        error_message = gettext('Incorrect password or two-factor code.')
        # If the user is validated, change their password
        if validate_user(user.username, current_password, token,
                         error_message):
            password = request.form.get('password')
            set_diceware_password(user, password)
        return redirect(url_for('account.edit'))

    @view.route('/2fa', methods=('GET', 'POST'))
    @login_required
    def new_two_factor():
        if request.method == 'POST':
            token = request.form['token']
            if g.user.verify_token(token):
                flash(gettext("Token in two-factor authentication verified."),
                      "notification")
                return redirect(url_for('account.edit'))
            else:
                flash(gettext(
                    "Could not verify token in two-factor authentication."),
                      "error")

        return render_template('account_new_two_factor.html', user=g.user)

    @view.route('/reset-2fa-totp', methods=['POST'])
    @login_required
    def reset_two_factor_totp():
        g.user.is_totp = True
        g.user.regenerate_totp_shared_secret()
        db_session.commit()
        return redirect(url_for('account.new_two_factor'))

    return view
