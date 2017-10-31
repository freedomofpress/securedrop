# -*- coding: utf-8 -*-

from flask import Blueprint, render_template

from db import Journalist
from journalist_app.decorators import admin_required


def make_blueprint(config):
    view = Blueprint('admin', __name__)

    @view.route('/', methods=('GET', 'POST'))
    @admin_required
    def index():
        users = Journalist.query.all()
        return render_template("admin.html", users=users)

    return view
