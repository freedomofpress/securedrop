# -*- coding: utf-8 -*-

from flask import Blueprint, redirect, url_for, render_template

import crypto_util

from db import db_session
from journalist_app.decorators import login_required
from journalist_app.forms import ReplyForm
from journalist_app.utils import make_star_true, make_star_false, get_source


def make_blueprint(config):
    view = Blueprint('col', __name__)

    @view.route('/add_star/<filesystem_id>', methods=('POST',))
    @login_required
    def add_star(filesystem_id):
        make_star_true(filesystem_id)
        db_session.commit()
        return redirect(url_for('main.index'))

    @view.route("/remove_star/<filesystem_id>", methods=('POST',))
    @login_required
    def remove_star(filesystem_id):
        make_star_false(filesystem_id)
        db_session.commit()
        return redirect(url_for('main.index'))

    @view.route('/<filesystem_id>')
    @login_required
    def col(filesystem_id):
        form = ReplyForm()
        source = get_source(filesystem_id)
        source.has_key = crypto_util.getkey(filesystem_id)
        return render_template("col.html", filesystem_id=filesystem_id,
                               source=source, form=form)

    return view
