import io
import logging
import subprocess

from datetime import datetime
from flask import session, current_app, abort, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from threading import Thread

import typing

import re

from crypto_util import CryptoUtil, CryptoException
from models import Source
from passphrases import PassphraseGenerator, DicewarePassphrase
from sdconfig import SDConfig

if typing.TYPE_CHECKING:
    from typing import Optional  # noqa: F401


def was_in_generate_flow() -> bool:
    return 'codenames' in session


def logged_in() -> bool:
    return 'logged_in' in session


def valid_codename(codename: str) -> bool:
    try:
        filesystem_id = current_app.crypto_util.hash_codename(codename)
    except CryptoException as e:
        current_app.logger.info(
                "Could not compute filesystem ID for codename '{}': {}".format(
                    codename, e))
        abort(500)

    source = Source.query.filter_by(filesystem_id=filesystem_id).first()
    return source is not None


def generate_unique_codename(config: SDConfig) -> DicewarePassphrase:
    """Generate random codenames until we get an unused one"""
    while True:
        passphrase = PassphraseGenerator.get_default().generate_passphrase(
            preferred_language=g.localeinfo.language
        )
        # scrypt (slow)
        filesystem_id = current_app.crypto_util.hash_codename(passphrase)

        matching_sources = Source.query.filter(
            Source.filesystem_id == filesystem_id).all()
        if len(matching_sources) == 0:
            return passphrase


def get_entropy_estimate() -> int:
    with io.open('/proc/sys/kernel/random/entropy_avail') as f:
        return int(f.read())


def asynchronous(f):               # type: ignore
    def wrapper(*args, **kwargs):  # type: ignore
        thread = Thread(target=f, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


@asynchronous
def async_genkey(crypto_util_: CryptoUtil,
                 db_uri: str,
                 filesystem_id: str,
                 codename: DicewarePassphrase) -> None:
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


def normalize_timestamps(filesystem_id: str) -> None:
    """
    Update the timestamps on all of the source's submissions. This
    minimizes metadata that could be useful to investigators. See
    #301.
    """
    sub_paths = [current_app.storage.path(filesystem_id, submission.filename)
                 for submission in g.source.submissions]
    if len(sub_paths) > 1:
        args = ["touch", "--no-create"]
        args.extend(sub_paths)
        rc = subprocess.call(args)
        if rc != 0:
            current_app.logger.warning(
                "Couldn't normalize submission "
                "timestamps (touch exited with %d)" %
                rc)


def check_url_file(path: str, regexp: str) -> 'Optional[str]':
    """
    Check that a file exists at the path given and contains a single line
    matching the regexp. Used for checking the source interface address
    files at /var/lib/securedrop/source_{v2,v3}_url.
    """
    try:
        f = open(path, "r")
        contents = f.readline().strip()
        f.close()
        if re.match(regexp, contents):
            return contents
        else:
            return None
    except IOError:
        return None


def get_sourcev2_url() -> 'Optional[str]':
    return check_url_file("/var/lib/securedrop/source_v2_url",
                          r"^[a-z0-9]{16}\.onion$")


def get_sourcev3_url() -> 'Optional[str]':
    return check_url_file("/var/lib/securedrop/source_v3_url",
                          r"^[a-z0-9]{56}\.onion$")
