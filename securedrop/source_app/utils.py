import io
import logging
import subprocess

from datetime import datetime
from flask import session, current_app, abort, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from threading import Thread

import i18n

from crypto_util import CryptoException
from models import Source


def logged_in():
    return 'logged_in' in session


def valid_codename(codename):
    try:
        filesystem_id = current_app.crypto_util.hash_codename(codename)
    except CryptoException as e:
        current_app.logger.info(
                "Could not compute filesystem ID for codename '{}': {}".format(
                    codename, e))
        abort(500)

    source = Source.query.filter_by(filesystem_id=filesystem_id).first()
    return source is not None


def generate_unique_codename(config):
    """Generate random codenames until we get an unused one"""
    while True:
        codename = current_app.crypto_util.genrandomid(
            Source.NUM_WORDS,
            i18n.get_language(config))

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

        # scrypt (slow)
        filesystem_id = current_app.crypto_util.hash_codename(codename)

        matching_sources = Source.query.filter(
            Source.filesystem_id == filesystem_id).all()
        if len(matching_sources) == 0:
            return codename


def get_entropy_estimate():
    with io.open('/proc/sys/kernel/random/entropy_avail') as f:
        return int(f.read())


def asynchronous(f):
    def wrapper(*args, **kwargs):
        thread = Thread(target=f, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


@asynchronous
def async_genkey(crypto_util_, db_uri, filesystem_id, codename):
    # We pass in the `crypto_util_` so we don't have to reference `current_app`
    # here. The app might not have a pushed context during testing which would
    # cause this asynchronous function to break.
    crypto_util_.genkeypair(filesystem_id, codename)

    # Register key generation as update to the source, so sources will
    # filter to the top of the list in the journalist interface if a
    # flagged source logs in and has a key generated for them. #789
    session = sessionmaker(bind=create_engine(db_uri))()
    try:
        source = session.query(Source).filter(
            Source.filesystem_id == filesystem_id).one()
        source.last_updated = datetime.utcnow()
        session.commit()
    except Exception as e:
        logging.getLogger(__name__).error(
                "async_genkey for source (filesystem_id={}): {}"
                .format(filesystem_id, e))
    session.close()


def normalize_timestamps(filesystem_id):
    """
    Update the timestamps on all of the source's submissions to match that of
    the latest submission. This minimizes metadata that could be useful to
    investigators. See #301.
    """
    sub_paths = [current_app.storage.path(filesystem_id, submission.filename)
                 for submission in g.source.submissions]
    if len(sub_paths) > 1:
        args = ["touch"]
        args.extend(sub_paths[:-1])
        rc = subprocess.call(args)
        if rc != 0:
            current_app.logger.warning(
                "Couldn't normalize submission "
                "timestamps (touch exited with %d)" %
                rc)
