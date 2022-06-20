import subprocess
import re
from hmac import compare_digest

from typing import Optional

import werkzeug
from flask import flash, redirect, render_template, current_app, url_for
from flask.sessions import SessionMixin
from markupsafe import Markup, escape
from flask_babel import gettext
from store import Storage

from source_user import SourceUser


def passphrase_detected(message: str, passphrase: str) -> bool:
    """
    Check for passphrases in incoming messages. including case where user copy/pasted
    from the passphrase widget on the same page
    """
    message = message.strip()

    return compare_digest(message.strip(), passphrase)


def flash_msg(
    category: str,
    declarative: 'Optional[str]',
    *msg_contents: 'str',
) -> None:
    """
    Render flash message with a (currently) optional declarative heading.
    """
    contents = Markup("<br>".join([escape(part) for part in msg_contents]))

    msg = render_template(
        'flash_message.html',
        declarative=declarative,
        msg_contents=contents,
    )
    flash(Markup(msg), category)


def clear_session_and_redirect_to_logged_out_page(flask_session: SessionMixin) -> werkzeug.Response:
    msg = render_template(
        'flash_message.html',
        declarative=gettext("Important"),
        msg_contents=Markup(gettext(
            'You were logged out due to inactivity. Click the <img src={icon} alt="" width="16" '
            'height="16">&nbsp;<b>New Identity</b> button in your Tor Browser\'s toolbar before '
            'moving on. This will clear your Tor Browser activity data on this device.')
             .format(icon=url_for("static", filename="i/torbroom.png")))
    )

    # Clear the session after we render the message so it's localized
    flask_session.clear()

    flash(Markup(msg), "error")
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
