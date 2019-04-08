# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from flask import (Flask, session, redirect, url_for, flash, g, request,
                   render_template)
from flask_assets import Environment
from flask_babel import gettext
from flask_wtf.csrf import CSRFProtect, CSRFError
from os import path
from werkzeug.exceptions import default_exceptions  # type: ignore

import i18n
import template_filters
import version
import platform

from crypto_util import CryptoUtil
from db import db
from journalist_app import account, admin, api, main, col
from journalist_app.utils import (get_source, logged_in,
                                  JournalistInterfaceSessionInterface)
from models import Journalist
from store import Storage

import typing
# https://www.python.org/dev/peps/pep-0484/#runtime-or-type-checking
if typing.TYPE_CHECKING:
    # flake8 can not understand type annotation yet.
    # That is why all type annotation relative import
    # statements has to be marked as noqa.
    # http://flake8.pycqa.org/en/latest/user/error-codes.html?highlight=f401
    from sdconfig import SDConfig  # noqa: F401

_insecure_views = ['main.login', 'main.select_logo', 'static']


def create_app(config):
    # type: (SDConfig) -> Flask
    app = Flask(__name__,
                template_folder=config.JOURNALIST_TEMPLATES_DIR,
                static_folder=path.join(config.SECUREDROP_ROOT, 'static'))

    app.config.from_object(config.JournalistInterfaceFlaskConfig)  # type: ignore
    app.sdconfig = config
    app.session_interface = JournalistInterfaceSessionInterface()

    csrf = CSRFProtect(app)
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

    # Magic values for Xenial upgrade message
    app.config.update(
        XENIAL_WARNING_DATE=datetime.strptime('Mar 4 2019', '%b %d %Y'),
        XENIAL_VER='16.04'
    )

    app.storage = Storage(config.STORE_DIR,
                          config.TEMP_DIR,
                          config.JOURNALIST_KEY)

    app.crypto_util = CryptoUtil(
        scrypt_params=config.SCRYPT_PARAMS,
        scrypt_id_pepper=config.SCRYPT_ID_PEPPER,
        scrypt_gpg_pepper=config.SCRYPT_GPG_PEPPER,
        securedrop_root=config.SECUREDROP_ROOT,
        word_list=config.WORD_LIST,
        nouns_file=config.NOUNS,
        adjectives_file=config.ADJECTIVES,
        gpg_key_dir=config.GPG_KEY_DIR,
    )

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        # render the message first to ensure it's localized.
        msg = gettext('You have been logged out due to inactivity')
        session.clear()
        flash(msg, 'error')
        return redirect(url_for('main.login'))

    def _handle_http_exception(error):
        # Workaround for no blueprint-level 404/5 error handlers, see:
        # https://github.com/pallets/flask/issues/503#issuecomment-71383286
        handler = list(app.error_handler_spec['api'][error.code].values())[0]
        if request.path.startswith('/api/') and handler:
            return handler(error)

        return render_template('error.html', error=error), error.code

    for code in default_exceptions:
        app.errorhandler(code)(_handle_http_exception)

    i18n.setup_app(config, app)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.jinja_env.globals['version'] = version.__version__
    if hasattr(config, 'CUSTOM_HEADER_IMAGE'):
        app.jinja_env.globals['header_image'] = \
            config.CUSTOM_HEADER_IMAGE  # type: ignore
        app.jinja_env.globals['use_custom_header_image'] = True
    else:
        app.jinja_env.globals['header_image'] = 'logo.png'
        app.jinja_env.globals['use_custom_header_image'] = False

    app.jinja_env.filters['rel_datetime_format'] = \
        template_filters.rel_datetime_format
    app.jinja_env.filters['filesizeformat'] = template_filters.filesizeformat

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

        if (platform.linux_distribution()[1] != app.config['XENIAL_VER'] and
                datetime.now() >= app.config['XENIAL_WARNING_DATE']):
            g.show_xenial_warning = True

        if request.path.split('/')[1] == 'api':
            pass  # We use the @token_required decorator for the API endpoints
        else:  # We are not using the API
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
    api_blueprint = api.make_blueprint(config)
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    csrf.exempt(api_blueprint)

    return app
