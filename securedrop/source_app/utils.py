import json
import subprocess

import werkzeug
from flask import flash
from flask import redirect
from flask import render_template
from flask import current_app
from flask import url_for
from flask.sessions import SessionMixin
from markupsafe import Markup
from store import Storage

import typing

import re

from source_user import SourceUser

if typing.TYPE_CHECKING:
    from typing import Optional


def clear_session_and_redirect_to_logged_out_page(flask_session: SessionMixin) -> werkzeug.Response:
    msg = render_template('session_timeout.html')

    # Clear the session after we render the message so it's localized
    flask_session.clear()

    flash(Markup(msg), "important")
    return redirect(url_for('main.index'))


def normalize_timestamps(logged_in_source: SourceUser) -> None:
    """
    Update the timestamps on all of the source's submissions. This
    minimizes metadata that could be useful to investigators. See
    #301.
    """
    source_in_db = logged_in_source.get_db_record()
    sub_paths = [Storage.get_default().path(logged_in_source.filesystem_id, submission.filename)
                 for submission in source_in_db.submissions]
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
    files in /var/lib/securedrop (as the Apache user can't read Tor config)
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


def get_sourcev3_url() -> 'Optional[str]':
    return check_url_file("/var/lib/securedrop/source_v3_url",
                          r"^[a-z0-9]{56}\.onion$")


def fit_codenames_into_cookie(codenames: dict) -> dict:
    """
    If `codenames` will approach `werkzeug.Response.max_cookie_size` once
    serialized, incrementally pop off the oldest codename until the remaining
    (newer) ones will fit.
    """

    serialized = json.dumps(codenames).encode()
    if len(codenames) > 1 and len(serialized) > 4000:  # werkzeug.Response.max_cookie_size = 4093
        if current_app:
            current_app.logger.warn(f"Popping oldest of {len(codenames)} "
                                    f"codenames ({len(serialized)} bytes) to "
                                    f"fit within maximum cookie size")
        del codenames[list(codenames)[0]]  # FIFO

        return fit_codenames_into_cookie(codenames)

    return codenames
