# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from flask import Flask, session, redirect, url_for, flash, g, request
from flask_assets import Environment
from flask_babel import gettext
from flask_wtf.csrf import CSRFProtect, CSRFError
from os import path

import i18n
import template_filters
import version

from db import db
from journalist_app import account, admin, main, col
from journalist_app.utils import get_source, logged_in
from models import Journalist
from store import Storage

_insecure_views = ['main.login', 'static']


def create_app(config):
    app = Flask(__name__,
                template_folder=config.JOURNALIST_TEMPLATES_DIR,
                static_folder=path.join(config.SECUREDROP_ROOT, 'static'))

    app.config.from_object(config.JournalistInterfaceFlaskConfig)

    CSRFProtect(app)
    Environment(app)

    if config.DATABASE_ENGINE == "sqlite":
        db_uri = (config.DATABASE_ENGINE + ":///" +
                  config.DATABASE_FILE)
    else:
        db_uri = (
            config.DATABASE_ENGINE + '://' +
            config.DATABASE_USERNAME + ':' +
            config.DATABASE_PASSWORD + '@' +
            config.DATABASE_HOST + '/' +
            config.DATABASE_NAME
        )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    db.init_app(app)

    app.storage = Storage(config.STORE_DIR,
                          config.TEMP_DIR,
                          config.JOURNALIST_KEY)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        # render the message first to ensure it's localized.
        msg = gettext('You have been logged out due to inactivity')
        session.clear()
        flash(msg, 'error')
        return redirect(url_for('main.login'))

    i18n.setup_app(config, app)

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

    @app.template_filter('autoversion')
    def autoversion_filter(filename):
        """Use this template filter for cache busting"""
        absolute_filename = path.join(config.SECUREDROP_ROOT, filename[1:])
        if path.exists(absolute_filename):
            timestamp = str(path.getmtime(absolute_filename))
        else:
            return filename
        versioned_filename = "{0}?v={1}".format(filename, timestamp)
        return versioned_filename

    @app.before_request
    def setup_g():
        """Store commonly used values in Flask's special g object"""
        if 'expires' in session and datetime.utcnow() >= session['expires']:
            session.clear()
            flash(gettext('You have been logged out due to inactivity'),
                  'error')

        session['expires'] = datetime.utcnow() + \
            timedelta(minutes=getattr(config,
                                      'SESSION_EXPIRATION_MINUTES',
                                      120))

        uid = session.get('uid', None)
        if uid:
            g.user = Journalist.query.get(uid)

        g.locale = i18n.get_locale(config)
        g.text_direction = i18n.get_text_direction(g.locale)
        g.html_lang = i18n.locale_to_rfc_5646(g.locale)
        g.locales = i18n.get_locale2name()

        if request.endpoint not in _insecure_views and not logged_in():
            return redirect(url_for('main.login'))

        if request.method == 'POST':
            filesystem_id = request.form.get('filesystem_id')
            if filesystem_id:
                g.filesystem_id = filesystem_id
                g.source = get_source(filesystem_id)

    app.register_blueprint(main.make_blueprint(config))
    app.register_blueprint(account.make_blueprint(config),
                           url_prefix='/account')
    app.register_blueprint(admin.make_blueprint(config), url_prefix='/admin')
    app.register_blueprint(col.make_blueprint(config), url_prefix='/col')

    return app
