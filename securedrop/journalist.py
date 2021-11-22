# -*- coding: utf-8 -*-
from encryption import EncryptionManager, GpgKeyNotFoundError
from sdconfig import config

from journalist_app import create_app
from models import Source
from execution import asynchronous

app = create_app(config)


@asynchronous
def prime_keycache() -> None:
    """Pre-load the source public keys into Redis."""
    with app.app_context():
        encryption_mgr = EncryptionManager.get_default()
        for source in Source.query.filter_by(pending=False, deleted_at=None).all():
            try:
                encryption_mgr.get_source_public_key(source.filesystem_id)
            except GpgKeyNotFoundError:
                pass


prime_keycache()


if __name__ == "__main__":  # pragma: no cover
    debug = getattr(config, 'env', 'prod') != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8081)  # nosec
