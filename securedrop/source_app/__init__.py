from flask import (Flask, render_template, flash, Markup, request, g, session,
                   abort, url_for, redirect)
from flask_babel import gettext
from flask_assets import Environment
from flask_wtf.csrf import CSRFProtect
from jinja2 import evalcontextfilter
from os import path
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import config as global_config
import crypto_util
import i18n
import store
import template_filters
import version

from db import Source, db_session
from request_that_secures_file_uploads import RequestThatSecuresFileUploads
from source_app import main, info
from source_app.decorators import ignore_static
from source_app.utils import logged_in


def create_app(config=None):
    if config is None:
        config = global_config

    app = Flask(__name__,
                template_folder=config.SOURCE_TEMPLATES_DIR,
                static_folder=path.join(config.SECUREDROP_ROOT, 'static'))
    app.request_class = RequestThatSecuresFileUploads
    app.config.from_object(config.SourceInterfaceFlaskConfig)

    # The default CSRF token expiration is 1 hour. Since large uploads can
    # take longer than an hour over Tor, we increase the valid window to 24h.
    app.config['WTF_CSRF_TIME_LIMIT'] = 60 * 60 * 24
    CSRFProtect(app)

    assets = Environment(app)
    app.config['assets'] = assets

    # this set needs to happen *before* we set the jinja filters otherwise
    # we get name collisions
    i18n.setup_app(app)

    app.jinja_env.globals['version'] = version.__version__
    if getattr(config, 'CUSTOM_HEADER_IMAGE', None):
        app.jinja_env.globals['header_image'] = config.CUSTOM_HEADER_IMAGE
        app.jinja_env.globals['use_custom_header_image'] = True
    else:
        app.jinja_env.globals['header_image'] = 'logo.png'
        app.jinja_env.globals['use_custom_header_image'] = False

    app.jinja_env.filters['datetimeformat'] = template_filters.datetimeformat
    app.jinja_env.filters['nl2br'] = evalcontextfilter(template_filters.nl2br)
    app.jinja_env.filters['filesizeformat'] = template_filters.filesizeformat

    for blueprint in [main.make_blueprint(), info.make_blueprint()]:
        app.register_blueprint(blueprint)

    @app.before_request
    @ignore_static
    def check_tor2web():
        # ignore_static here so we only flash a single message warning
        # about Tor2Web, corresponding to the initial page load.
        if 'X-tor2web' in request.headers:
            flash(Markup(gettext(
                '<strong>WARNING:</strong> You appear to be using Tor2Web. '
                'This <strong>does not</strong> provide anonymity. '
                '<a href="{url}">Why is this dangerous?</a>')
                .format(url=url_for('info.tor2web_warning'))),
                  "banner-warning")

    @app.before_request
    @ignore_static
    def setup_g():
        """Store commonly used values in Flask's special g object"""
        g.locale = i18n.get_locale()
        g.text_direction = i18n.get_text_direction(g.locale)
        g.html_lang = i18n.locale_to_rfc_5646(g.locale)
        g.locales = i18n.get_locale2name()

        # ignore_static here because `crypto_util.hash_codename` is scrypt
        # (very time consuming), and we don't need to waste time running if
        # we're just serving a static resource that won't need to access
        # these common values.
        if logged_in():
            g.codename = session['codename']
            g.filesystem_id = crypto_util.hash_codename(g.codename)
            try:
                g.source = Source.query \
                            .filter(Source.filesystem_id == g.filesystem_id) \
                            .one()
            except MultipleResultsFound as e:
                app.logger.error(
                    "Found multiple Sources when one was expected: %s" %
                    (e,))
                abort(500)
            except NoResultFound as e:
                app.logger.error(
                    "Found no Sources when one was expected: %s" %
                    (e,))
                del session['logged_in']
                del session['codename']
                return redirect(url_for('main.index'))
            g.loc = store.path(g.filesystem_id)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Automatically remove database sessions at the end of the request, or
        when the application shuts down"""
        db_session.remove()

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('notfound.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html'), 500

    return app
