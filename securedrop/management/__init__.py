from contextlib import contextmanager

import journalist_app
from sdconfig import config


@contextmanager
def app_context():
    with journalist_app.create_app(config).app_context():
        yield
