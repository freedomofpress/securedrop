# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, g, redirect, url_for
from flask_babel import gettext

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

    return view
