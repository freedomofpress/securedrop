# -*- coding: utf-8 -*-

from io import StringIO
from flask import Blueprint, render_template, send_file, current_app


def make_blueprint(config):
    view = Blueprint('info', __name__)

    @view.route('/disable-noscript-xss')
    def disable_noscript_xss():
        return render_template("disable-noscript-xss.html")

    @view.route('/tor2web-warning')
    def tor2web_warning():
        return render_template("tor2web-warning.html")

    @view.route('/use-tor')
    def recommend_tor_browser():
        return render_template("use-tor-browser.html")

    @view.route('/journalist-key')
    def download_journalist_pubkey():
        journalist_pubkey = current_app.crypto_util.gpg.export_keys(
            config.JOURNALIST_KEY)
        return send_file(StringIO(journalist_pubkey),
                         mimetype="application/pgp-keys",
                         attachment_filename=config.JOURNALIST_KEY + ".asc",
                         as_attachment=True)

    @view.route('/why-journalist-key')
    def why_download_journalist_pubkey():
        return render_template("why-journalist-key.html")

    return view
