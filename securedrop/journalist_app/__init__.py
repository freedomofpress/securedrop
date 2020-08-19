# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from flask import (Flask, session, redirect, url_for, flash, g, request,
                   render_template)
from flask_assets import Environment
from flask_babel import gettext
from flask_wtf.csrf import CSRFProtect, CSRFError
from os import path
import sys
from werkzeug.exceptions import default_exceptions

import i18n
import template_filters
import version

from crypto_util import CryptoUtil
from db import db
from journalist_app import account, admin, api, main, col
from journalist_app.utils import (get_source, logged_in,
                                  JournalistInterfaceSessionInterface,
                                  cleanup_expired_revoked_tokens)
from models import InstanceConfig, Journalist
from store import Storage

import typing
# https://www.python.org/dev/peps/pep-0484/#runtime-or-type-checking
if typing.TYPE_CHECKING:
    # flake8 can not understand type annotation yet.
    # That is why all type annotation relative import
    # statements has to be marked as noqa.
    # http://flake8.pycqa.org/en/latest/user/error-codes.html?highlight=f401
    from sdconfig import SDConfig  # noqa: F401
    from typing import Optional, Union, Tuple, Any  # noqa: F401
    from werkzeug import Response  # noqa: F401
    from werkzeug.exceptions import HTTPException  # noqa: F401

_insecure_views = ['main.login', 'main.select_logo', 'static']


def create_app(config: 'SDConfig') -> Flask:
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

    v2_enabled = path.exists(path.join(config.SECUREDROP_DATA_ROOT, 'source_v2_url'))
    v3_enabled = path.exists(path.join(config.SECUREDROP_DATA_ROOT, 'source_v3_url'))
    app.config.update(V2_ONION_ENABLED=v2_enabled, V3_ONION_ENABLED=v3_enabled)

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
    def handle_csrf_error(e: CSRFError) -> 'Response':
        # render the message first to ensure it's localized.
        msg = gettext('You have been logged out due to inactivity.')
        session.clear()
        flash(msg, 'error')
        return redirect(url_for('main.login'))

    def _handle_http_exception(
        error: 'HTTPException'
    ) -> 'Tuple[Union[Response, str], Optional[int]]':
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
    app.jinja_env.filters['rel_datetime_format'] = \
        template_filters.rel_datetime_format
    app.jinja_env.filters['filesizeformat'] = template_filters.filesizeformat

    @app.before_first_request
    def expire_blacklisted_tokens() -> None:
        cleanup_expired_revoked_tokens()

    @app.before_request
    def load_instance_config() -> None:
        app.instance_config = InstanceConfig.get_current()

    @app.before_request
    def setup_g() -> 'Optional[Response]':
        """Store commonly used values in Flask's special g object"""
        if 'expires' in session and datetime.utcnow() >= session['expires']:
            session.clear()
            flash(gettext('You have been logged out due to inactivity.'),
                  'error')

        uid = session.get('uid', None)
        if uid:
            user = Journalist.query.get(uid)
            if user and 'nonce' in session and \
               session['nonce'] != user.session_nonce:
                session.clear()
                flash(gettext('You have been logged out due to password change'),
                      'error')

        session['expires'] = datetime.utcnow() + \
            timedelta(minutes=getattr(config,
                                      'SESSION_EXPIRATION_MINUTES',
                                      120))

        # Work around https://github.com/lepture/flask-wtf/issues/275
        # -- after upgrading from Python 2 to Python 3, any existing
        # session's csrf_token value will be retrieved as bytes,
        # causing a TypeError. This simple fix, deleting the existing
        # token, was suggested in the issue comments. This code will
        # be safe to remove after Python 2 reaches EOL in 2020, and no
        # supported SecureDrop installations can still have this
        # problem.
        if sys.version_info.major > 2 and type(session.get('csrf_token')) is bytes:
            del session['csrf_token']

        uid = session.get('uid', None)
        if uid:
            g.user = Journalist.query.get(uid)

        g.locale = i18n.get_locale(config)
        g.text_direction = i18n.get_text_direction(g.locale)
        g.html_lang = i18n.locale_to_rfc_5646(g.locale)
        g.locales = i18n.get_locale2name()

        if not app.config['V3_ONION_ENABLED'] or app.config['V2_ONION_ENABLED']:
            g.show_v2_onion_eol_warning = True

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

        return None

    app.register_blueprint(main.make_blueprint(config))
    app.register_blueprint(account.make_blueprint(config),
                           url_prefix='/account')
    app.register_blueprint(admin.make_blueprint(config), url_prefix='/admin')
    app.register_blueprint(col.make_blueprint(config), url_prefix='/col')
    api_blueprint = api.make_blueprint(config)
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    csrf.exempt(api_blueprint)

    return app
