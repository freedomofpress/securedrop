# -*- coding: utf-8 -*-

from sdconfig import config

from journalist_app import create_app
from models import Source
from source_app.utils import asynchronous

app = create_app(config)


@asynchronous
def prime_keycache():
    """
    Preloads CryptoUtil.keycache.
    """
    with app.app_context():
        for source in Source.query.filter_by(pending=False).all():
            app.crypto_util.get_pubkey(source.filesystem_id)


prime_keycache()


if __name__ == "__main__":  # pragma: no cover
    debug = getattr(config, 'env', 'prod') != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8081)  # nosec
