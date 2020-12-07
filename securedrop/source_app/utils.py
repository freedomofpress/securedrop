import io
import logging
import subprocess

from datetime import datetime

import werkzeug
from flask import flash
from flask import redirect
from flask import render_template
from flask import current_app
from flask import url_for
from markupsafe import Markup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from threading import Thread

import typing

import re

from crypto_util import CryptoUtil
from models import Source
from passphrases import DicewarePassphrase
from source_user import SourceUser

if typing.TYPE_CHECKING:
    from typing import Optional


def redirect_to_index_and_show_logout_message(session: typing.Dict) -> werkzeug.Response:
    msg = render_template('session_timeout.html')

    # Clear the session after we render the message so it's localized
    session.clear()

    flash(Markup(msg), "important")
    return redirect(url_for('main.index'))


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
                 source_user: SourceUser
                 ) -> None:
    # We pass in the `crypto_util_` so we don't have to reference `current_app`
    # here. The app might not have a pushed context during testing which would
    # cause this asynchronous function to break.
    crypto_util_.genkeypair(source_user)

    # Register key generation as update to the source, so sources will
    # filter to the top of the list in the journalist interface if a
    # flagged source logs in and has a key generated for them. #789
    db_session = sessionmaker(bind=create_engine(db_uri))()
    try:
        source = source_user.get_db_record()
        source.last_updated = datetime.utcnow()
        db_session.commit()
    except Exception as e:
        logging.getLogger(__name__).error(
                "async_genkey for source (filesystem_id={}): {}"
                .format(source_user.filesystem_id, e))
    finally:
        db_session.close()


def normalize_timestamps(logged_in_source: SourceUser) -> None:
    """
    Update the timestamps on all of the source's submissions to match that of
    the latest submission. This minimizes metadata that could be useful to
    investigators. See #301.
    """
    source_in_db = logged_in_source.get_db_record()
    sub_paths = [current_app.storage.path(logged_in_source.filesystem_id, submission.filename)
                 for submission in source_in_db.submissions]
    if len(sub_paths) > 1:
        args = ["touch"]
        args.extend(sub_paths[:-1])
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
