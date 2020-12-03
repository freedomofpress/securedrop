import json
import subprocess

import werkzeug
from flask import flash
from flask import abort, redirect
from flask import render_template
from flask import current_app, session
from flask import url_for
from markupsafe import Markup

import typing

import re

from source_user import SourceUser
from models import Journalist

if typing.TYPE_CHECKING:
    from typing import Optional


def clear_session_and_redirect_to_logged_out_page(flask_session: typing.Dict) -> werkzeug.Response:
    msg = render_template('session_timeout.html')

    # Clear the session after we render the message so it's localized
    flask_session.clear()

    flash(Markup(msg), "important")
    return redirect(url_for('main.index'))


def active_securedrop_groups() -> typing.Dict:
    # This is hardcoded for demo purposes. There would need to be logic around
    # populating this (i.e. onboarding/offboarding).
    journalist = Journalist.query.filter_by(username="journalist").first()

    # We would only return those journalists for which they have completed
    # signal registration.
    if not journalist.is_signal_registered():
        return {"default": ""}

    if not journalist:
        abort(404)  # Temp for testing, should be 500

    journalist_uuid = journalist.uuid

    # In production, we'd need to provide a list of journalists. Then we'd use
    # Signal group messaging to construct the journalists to talk to.
    #
    # This is also the step where for multi-tenancy we can add multiple groups,
    # and allow sources to select the group/organization they wish to message.
    return {"default": journalist_uuid}


def was_in_generate_flow() -> bool:
    return 'codenames' in session


def normalize_timestamps(logged_in_source: SourceUser) -> None:
    """
    Update the timestamps on all of the source's submissions. This
    minimizes metadata that could be useful to investigators. See
    #301.
    """
    source_in_db = logged_in_source.get_db_record()
    sub_paths = [current_app.storage.path(logged_in_source.filesystem_id, submission.filename)
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
