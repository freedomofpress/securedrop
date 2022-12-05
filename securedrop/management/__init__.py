from contextlib import contextmanager
from typing import Generator

import journalist_app
from sdconfig import SecureDropConfig


@contextmanager
def app_context() -> Generator:
    config = SecureDropConfig.get_current()
    with journalist_app.create_app(config).app_context():
        yield
