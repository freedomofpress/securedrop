# -*- coding: utf-8 -*-

from flask import Flask, session, redirect, url_for, flash
from flask_assets import Environment
from flask_babel import gettext
from flask_wtf.csrf import CSRFProtect, CSRFError
from os import path

import i18n
import template_filters
import version


def create_app(config):
    app = Flask(__name__,
                template_folder=config.JOURNALIST_TEMPLATES_DIR,
                static_folder=path.join(config.SECUREDROP_ROOT, 'static'))

    app.config.from_object(config.JournalistInterfaceFlaskConfig)

    CSRFProtect(app)
    Environment(app)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        # render the message first to ensure it's localized.
        msg = gettext('You have been logged out due to inactivity')
        session.clear()
        flash(msg, 'error')
        return redirect(url_for('login'))

    i18n.setup_app(app)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.jinja_env.globals['version'] = version.__version__
    if hasattr(config, 'CUSTOM_HEADER_IMAGE'):
        app.jinja_env.globals['header_image'] = config.CUSTOM_HEADER_IMAGE
        app.jinja_env.globals['use_custom_header_image'] = True
    else:
        app.jinja_env.globals['header_image'] = 'logo.png'
        app.jinja_env.globals['use_custom_header_image'] = False

    app.jinja_env.filters['rel_datetime_format'] = \
        template_filters.rel_datetime_format
    app.jinja_env.filters['filesizeformat'] = template_filters.filesizeformat

    return app
