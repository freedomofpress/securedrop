# -*- coding: utf-8 -*-

from flask import Blueprint, render_template

from journalist_app.decorators import login_required
from journalist_app.utils import make_password


def make_blueprint(config):
    view = Blueprint('account', __name__)

    @view.route('/account', methods=('GET',))
    @login_required
    def edit():
        password = make_password()
        return render_template('edit_account.html',
                               password=password)

    return view
