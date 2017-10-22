# -*- coding: utf-8 -*-

from flask import Flask, session, redirect, url_for, flash
from flask_babel import gettext
from flask_wtf.csrf import CSRFProtect, CSRFError
from os import path


def create_app(config):
    app = Flask(__name__,
                template_folder=config.JOURNALIST_TEMPLATES_DIR,
                static_folder=path.join(config.SECUREDROP_ROOT, 'static'))

    app.config.from_object(config.JournalistInterfaceFlaskConfig)

    CSRFProtect(app)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        # render the message first to ensure it's localized.
        msg = gettext('You have been logged out due to inactivity')
        session.clear()
        flash(msg, 'error')
        return redirect(url_for('login'))

    return app
