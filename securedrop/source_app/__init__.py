from flask import Flask
from flask_assets import Environment
from flask_wtf.csrf import CSRFProtect
from os import path

import config as global_config
from request_that_secures_file_uploads import RequestThatSecuresFileUploads


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

    return app
