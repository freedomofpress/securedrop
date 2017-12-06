from cStringIO import StringIO
from flask import Blueprint, render_template, send_file

import crypto_util


def make_blueprint(config):
    view = Blueprint('info', __name__)

    @view.route('/tor2web-warning')
    def tor2web_warning():
        return render_template("tor2web-warning.html")

    @view.route('/use-tor')
    def recommend_tor_browser():
        return render_template("use-tor-browser.html")

    @view.route('/journalist-key')
    def download_journalist_pubkey():
        journalist_pubkey = crypto_util.gpg.export_keys(config.JOURNALIST_KEY)
        return send_file(StringIO(journalist_pubkey),
                         mimetype="application/pgp-keys",
                         attachment_filename=config.JOURNALIST_KEY + ".asc",
                         as_attachment=True)

    @view.route('/why-journalist-key')
    def why_download_journalist_pubkey():
        return render_template("why-journalist-key.html")

    return view
