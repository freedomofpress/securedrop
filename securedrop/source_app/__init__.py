from flask import Flask
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

    return app
