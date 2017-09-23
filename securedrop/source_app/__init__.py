from flask import Flask, render_template
from flask_assets import Environment
from flask_wtf.csrf import CSRFProtect
from jinja2 import evalcontextfilter
from os import path

import config as global_config
import i18n
import template_filters
import version

from request_that_secures_file_uploads import RequestThatSecuresFileUploads
from source_app import views


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

    views.add_blueprints(app)

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('notfound.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html'), 500

    return app
