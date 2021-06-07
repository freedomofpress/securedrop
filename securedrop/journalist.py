# -*- coding: utf-8 -*-

from sdconfig import config

from journalist_app import create_app
from models import Source
from execution import asynchronous

app = create_app(config)


@asynchronous
def prime_keycache() -> None:
    """
    Preloads CryptoUtil.keycache.
    """
    with app.app_context():
        for source in Source.query.filter_by(pending=False, deleted_at=None).all():
            app.crypto_util.get_pubkey(source.filesystem_id)


prime_keycache()


if __name__ == "__main__":  # pragma: no cover
    debug = getattr(config, 'env', 'prod') != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8081)  # nosec
