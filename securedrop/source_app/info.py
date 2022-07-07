# -*- coding: utf-8 -*-
from io import BytesIO  # noqa

import flask
import werkzeug
from encryption import EncryptionManager
from flask import Blueprint, redirect, render_template, send_file, url_for
from flask_babel import gettext
from sdconfig import SDConfig
from source_app.utils import flash_msg, get_sourcev3_url


def make_blueprint(config: SDConfig) -> Blueprint:
    view = Blueprint("info", __name__)

    @view.route("/tor2web-warning")
    def tor2web_warning() -> flask.Response:
        flash_msg("error", None, gettext("Your connection is not anonymous right now!"))
        return flask.Response(
            render_template("tor2web-warning.html", source_url=get_sourcev3_url()), 403
        )

    @view.route("/use-tor")
    def recommend_tor_browser() -> str:
        return render_template("use-tor-browser.html")

    @view.route("/public-key")
    def download_public_key() -> flask.Response:
        journalist_pubkey = EncryptionManager.get_default().get_journalist_public_key()
        data = BytesIO(journalist_pubkey.encode("utf-8"))
        return send_file(
            data,
            mimetype="application/pgp-keys",
            attachment_filename=config.JOURNALIST_KEY + ".asc",
            as_attachment=True,
        )

    @view.route("/journalist-key")
    def download_journalist_key() -> werkzeug.wrappers.Response:
        return redirect(url_for(".download_public_key"), code=301)

    @view.route("/why-public-key")
    def why_download_public_key() -> str:
        return render_template("why-public-key.html")

    return view
