import subprocess

from flask import session, current_app, abort, g

import typing

import re

from crypto_util import CryptoException
from models import Source
from passphrases import PassphraseGenerator, DicewarePassphrase
from models import Journalist, Source
from sdconfig import SDConfig

if typing.TYPE_CHECKING:
    from typing import Optional  # noqa: F401


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
