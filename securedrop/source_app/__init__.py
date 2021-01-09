from datetime import datetime, timedelta
from typing import Optional

import werkzeug
from flask import (Flask, render_template, flash, Markup, request, g, session,
                   url_for)
from flask_babel import gettext
from flask_assets import Environment
from flask_wtf.csrf import CSRFProtect, CSRFError
from jinja2 import evalcontextfilter
from os import path
from typing import Tuple

import i18n
import template_filters
import version

from crypto_util import CryptoUtil
from db import db
from models import InstanceConfig
from request_that_secures_file_uploads import RequestThatSecuresFileUploads
from sdconfig import SDConfig
from source_app import main, info, api
from source_app.decorators import ignore_static
from source_app.utils import redirect_to_index_and_show_logout_message
from store import Storage


def create_app(config: SDConfig) -> Flask:
    app = Flask(__name__,
                template_folder=config.SOURCE_TEMPLATES_DIR,
                static_folder=path.join(config.SECUREDROP_ROOT, 'static'))
    app.request_class = RequestThatSecuresFileUploads
    app.config.from_object(config.SOURCE_APP_FLASK_CONFIG_CLS)

    # The default CSRF token expiration is 1 hour. Since large uploads can
    # take longer than an hour over Tor, we increase the valid window to 24h.
    app.config['WTF_CSRF_TIME_LIMIT'] = 60 * 60 * 24
    CSRFProtect(app)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URI
    db.init_app(app)

    # TODO: Attaching a Storage dynamically like this disables all type checking (and
    # breaks code analysis tools) for code that uses current_app.storage; it should be refactored
    app.storage = Storage(config.STORE_DIR,
                          config.TEMP_DIR,
                          config.JOURNALIST_KEY)

    # TODO: Attaching a CryptoUtil dynamically like this disables all type checking (and
    # breaks code analysis tools) for code that uses current_app.storage; it should be refactored
    app.crypto_util = CryptoUtil(
        securedrop_root=config.SECUREDROP_ROOT,
        nouns_file=config.NOUNS,
        adjectives_file=config.ADJECTIVES,
        gpg_key_dir=config.GPG_KEY_DIR,
    )

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e: CSRFError) -> werkzeug.Response:
        return redirect_to_index_and_show_logout_message(session)

    assets = Environment(app)
    app.config['assets'] = assets

    i18n.setup_app(config, app)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.jinja_env.globals['version'] = version.__version__
    # Exported to source templates for being included in instructions
    app.jinja_env.globals['submission_key_fpr'] = config.JOURNALIST_KEY
    app.jinja_env.filters['rel_datetime_format'] = \
        template_filters.rel_datetime_format
    app.jinja_env.filters['nl2br'] = evalcontextfilter(template_filters.nl2br)
    app.jinja_env.filters['filesizeformat'] = template_filters.filesizeformat

    for module in [main, info, api]:
        app.register_blueprint(module.make_blueprint(config))  # type: ignore

    @app.before_request
    @ignore_static
    def setup_i18n() -> None:
        """Store i18n-related values in Flask's special g object"""
        g.locale = i18n.get_locale(config)
        g.text_direction = i18n.get_text_direction(g.locale)
        g.html_lang = i18n.locale_to_rfc_5646(g.locale)
        g.locales = i18n.get_locale2name()

    @app.before_request
    @ignore_static
    def check_tor2web() -> None:
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
    def load_instance_config() -> None:
        app.instance_config = InstanceConfig.get_current()

    @app.before_request
    @ignore_static
    def setup_g() -> Optional[werkzeug.Response]:
        if 'expires' in session and datetime.utcnow() >= session['expires']:
            # If the session as has expired, redirect to index with flashed message
            # if the user was in the middle of the generate flow
            if 'codenames' in session:
                return redirect_to_index_and_show_logout_message(session)

        session['expires'] = datetime.utcnow() + \
            timedelta(minutes=getattr(config,
                                      'SESSION_EXPIRATION_MINUTES',
                                      120))

        if app.instance_config.organization_name:
            g.organization_name = app.instance_config.organization_name
        else:
            g.organization_name = gettext('SecureDrop')

        return None

    @app.errorhandler(404)
    def page_not_found(error: werkzeug.exceptions.HTTPException) -> Tuple[str, int]:
        return render_template('notfound.html'), 404

    @app.errorhandler(500)
    def internal_error(error: werkzeug.exceptions.HTTPException) -> Tuple[str, int]:
        return render_template('error.html'), 500

    return app
