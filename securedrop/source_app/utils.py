from flask import session, current_app, abort

import crypto_util

from db import Source


def logged_in():
    return 'logged_in' in session


def valid_codename(codename):
    # Ignore codenames that are too long to avoid DoS
    if len(codename) > Source.MAX_CODENAME_LEN:
        current_app.logger.info(
                "Ignored attempted login because the codename was too long.")
        return False

    try:
        filesystem_id = crypto_util.hash_codename(codename)
    except crypto_util.CryptoException as e:
        current_app.logger.info(
                "Could not compute filesystem ID for codename '{}': {}".format(
                    codename, e))
        abort(500)

    source = Source.query.filter_by(filesystem_id=filesystem_id).first()
    return source is not None
