from flask import Flask
from flask_assets import Environment
from flask_wtf.csrf import CSRFProtect
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
    app.jinja_env.filters['filesizeformat'] = template_filters.filesizeformat

    return app
