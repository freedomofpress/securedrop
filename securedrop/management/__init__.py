from contextlib import contextmanager
from typing import Generator

import journalist_app
from sdconfig import config


@contextmanager
def app_context() -> Generator:
    with journalist_app.create_app(config).app_context():
        yield
