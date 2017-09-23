import os

from flask import (Blueprint, render_template, flash, redirect, url_for,
                   session, current_app)
from flask_babel import gettext
from sqlalchemy.exc import IntegrityError

import crypto_util
import store

from db import Source, db_session
from source_app.utils import logged_in, generate_unique_codename


def add_blueprints(app):
    app.register_blueprint(_main_blueprint())


def _main_blueprint():
    view = Blueprint('main', 'main')

    @view.route('/')
    def index():
        return render_template('index.html')

    @view.route('/generate', methods=('GET', 'POST'))
    def generate():
        if logged_in():
            flash(gettext(
                "You were redirected because you are already logged in. "
                "If you want to create a new account, you should log out "
                "first."),
                  "notification")
            return redirect(url_for('lookup'))

        codename = generate_unique_codename()
        session['codename'] = codename
        return render_template('generate.html', codename=codename)

    @view.route('/create', methods=['POST'])
    def create():
        filesystem_id = crypto_util.hash_codename(session['codename'])

        source = Source(filesystem_id, crypto_util.display_id())
        db_session.add(source)
        try:
            db_session.commit()
        except IntegrityError as e:
            current_app.logger.error(
                "Attempt to create a source with duplicate codename: %s" %
                (e,))
        else:
            os.mkdir(store.path(filesystem_id))

        session['logged_in'] = True
        return redirect(url_for('lookup'))

    return view
