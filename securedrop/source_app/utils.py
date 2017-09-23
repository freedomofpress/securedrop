from datetime import datetime
from flask import session, current_app, abort
from threading import Thread

import crypto_util

from db import Source, db_session


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


def generate_unique_codename():
    """Generate random codenames until we get an unused one"""
    while True:
        codename = crypto_util.genrandomid(Source.NUM_WORDS)

        # The maximum length of a word in the wordlist is 9 letters and the
        # codename length is 7 words, so it is currently impossible to
        # generate a codename that is longer than the maximum codename length
        # (currently 128 characters). This code is meant to be defense in depth
        # to guard against potential future changes, such as modifications to
        # the word list or the maximum codename length.
        if len(codename) > Source.MAX_CODENAME_LEN:
            current_app.logger.warning(
                    "Generated a source codename that was too long, "
                    "skipping it. This should not happen. "
                    "(Codename='{}')".format(codename))
            continue

        filesystem_id = crypto_util.hash_codename(codename)  # scrypt (slow)
        matching_sources = Source.query.filter(
            Source.filesystem_id == filesystem_id).all()
        if len(matching_sources) == 0:
            return codename


def async(f):
    def wrapper(*args, **kwargs):
        thread = Thread(target=f, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


@async
def async_genkey(filesystem_id, codename):
    crypto_util.genkeypair(filesystem_id, codename)

    # Register key generation as update to the source, so sources will
    # filter to the top of the list in the journalist interface if a
    # flagged source logs in and has a key generated for them. #789
    try:
        source = Source.query.filter(Source.filesystem_id == filesystem_id) \
                       .one()
        source.last_updated = datetime.utcnow()
        db_session.commit()
    except Exception as e:
        current_app.logger.error(
                "async_genkey for source (filesystem_id={}): {}"
                .format(filesystem_id, e))
