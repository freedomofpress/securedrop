from flask import (Blueprint, render_template, flash, redirect, url_for,
                   session)
from flask_babel import gettext

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

    return view
