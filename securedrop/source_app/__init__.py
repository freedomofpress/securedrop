from datetime import datetime, timedelta
from flask import (Flask, render_template, flash, Markup, request, g, session,
                   url_for, redirect)
from flask_babel import gettext
from flask_assets import Environment
from flask_wtf.csrf import CSRFProtect, CSRFError
from jinja2 import evalcontextfilter
from os import path
from sqlalchemy.orm.exc import NoResultFound

import i18n
import template_filters
import version

from crypto_util import CryptoUtil
from db import db
from models import Source
from request_that_secures_file_uploads import RequestThatSecuresFileUploads
from source_app import main, info, api
from source_app.decorators import ignore_static
from source_app.utils import logged_in
from store import Storage

import typing
# https://www.python.org/dev/peps/pep-0484/#runtime-or-type-checking
if typing.TYPE_CHECKING:
    # flake8 can not understand type annotation yet.
    # That is why all type annotation relative import
    # statements has to be marked as noqa.
    # http://flake8.pycqa.org/en/latest/user/error-codes.html?highlight=f401
    from sdconfig import SDConfig  # noqa: F401


def create_app(config):
    # type: (SDConfig) -> Flask
    app = Flask(__name__,
                template_folder=config.SOURCE_TEMPLATES_DIR,
                static_folder=path.join(config.SECUREDROP_ROOT, 'static'))
    app.request_class = RequestThatSecuresFileUploads
    app.config.from_object(config.SourceInterfaceFlaskConfig)  # type: ignore
    app.sdconfig = config

    # The default CSRF token expiration is 1 hour. Since large uploads can
    # take longer than an hour over Tor, we increase the valid window to 24h.
    app.config['WTF_CSRF_TIME_LIMIT'] = 60 * 60 * 24
    CSRFProtect(app)

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
        msg = render_template('session_timeout.html')
        session.clear()
        flash(Markup(msg), "important")
        return redirect(url_for('main.index'))

    assets = Environment(app)
    app.config['assets'] = assets

    i18n.setup_app(config, app)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.jinja_env.globals['version'] = version.__version__
    if getattr(config, 'CUSTOM_HEADER_IMAGE', None):
        app.jinja_env.globals['header_image'] = \
            config.CUSTOM_HEADER_IMAGE  # type: ignore
        app.jinja_env.globals['use_custom_header_image'] = True
    else:
        app.jinja_env.globals['header_image'] = 'logo.png'
        app.jinja_env.globals['use_custom_header_image'] = False

    app.jinja_env.filters['rel_datetime_format'] = \
        template_filters.rel_datetime_format
    app.jinja_env.filters['nl2br'] = evalcontextfilter(template_filters.nl2br)
    app.jinja_env.filters['filesizeformat'] = template_filters.filesizeformat

    for module in [main, info, api]:
        app.register_blueprint(module.make_blueprint(config))  # type: ignore

    @app.before_request
    @ignore_static
    def check_tor2web():
        # ignore_static here so we only flash a single message warning
        # about Tor2Web, corresponding to the initial page load.
        if 'X-tor2web' in request.headers:
            flash(Markup(gettext(
                '<strong>WARNING:&nbsp;</strong> '
                'You appear to be using Tor2Web. '
                'This <strong>&nbsp;does not&nbsp;</strong> '
                'provide anonymity. '
                '<a href="{url}">Why is this dangerous?</a>')
                .format(url=url_for('info.tor2web_warning'))),
                  "banner-warning")

    @app.before_request
    @ignore_static
    def setup_g():
        """Store commonly used values in Flask's special g object"""
        g.locale = i18n.get_locale(config)
        g.text_direction = i18n.get_text_direction(g.locale)
        g.html_lang = i18n.locale_to_rfc_5646(g.locale)
        g.locales = i18n.get_locale2name()

        if 'expires' in session and datetime.utcnow() >= session['expires']:
            msg = render_template('session_timeout.html')

            # clear the session after we render the message so it's localized
            session.clear()

            flash(Markup(msg), "important")

        session['expires'] = datetime.utcnow() + \
            timedelta(minutes=getattr(config,
                                      'SESSION_EXPIRATION_MINUTES',
                                      120))

        # ignore_static here because `crypto_util.hash_codename` is scrypt
        # (very time consuming), and we don't need to waste time running if
        # we're just serving a static resource that won't need to access
        # these common values.
        if logged_in():
            g.codename = session['codename']
            g.filesystem_id = app.crypto_util.hash_codename(g.codename)
            try:
                g.source = Source.query \
                            .filter(Source.filesystem_id == g.filesystem_id) \
                            .one()
            except NoResultFound as e:
                app.logger.error(
                    "Found no Sources when one was expected: %s" %
                    (e,))
                del session['logged_in']
                del session['codename']
                return redirect(url_for('main.index'))
            g.loc = app.storage.path(g.filesystem_id)

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('notfound.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html'), 500

    return app
