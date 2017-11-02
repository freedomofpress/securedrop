# -*- coding: utf-8 -*-

from flask import Blueprint, redirect, url_for

from db import db_session
from journalist_app.decorators import login_required
from journalist_app.utils import make_star_true


def make_blueprint(config):
    view = Blueprint('col', __name__)

    @view.route('/add_star/<filesystem_id>', methods=('POST',))
    @login_required
    def add_star(filesystem_id):
        make_star_true(filesystem_id)
        db_session.commit()
        return redirect(url_for('main.index'))

    return view
