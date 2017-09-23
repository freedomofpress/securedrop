# -*- coding: utf-8 -*-
from cStringIO import StringIO
from flask import render_template, send_file, make_response

import config
import json
import version
import crypto_util
from source_app import create_app

import logging
# This module's logger is explicitly labeled so the correct logger is used,
# even when this is run from the command line (e.g. during development)
log = logging.getLogger('source')

app = create_app()


@app.route('/tor2web-warning')
def tor2web_warning():
    return render_template("tor2web-warning.html")


@app.route('/use-tor')
def recommend_tor_browser():
    return render_template("use-tor-browser.html")


@app.route('/journalist-key')
def download_journalist_pubkey():
    journalist_pubkey = crypto_util.gpg.export_keys(config.JOURNALIST_KEY)
    return send_file(StringIO(journalist_pubkey),
                     mimetype="application/pgp-keys",
                     attachment_filename=config.JOURNALIST_KEY + ".asc",
                     as_attachment=True)


@app.route('/why-journalist-key')
def why_download_journalist_pubkey():
    return render_template("why-journalist-key.html")


@app.route('/metadata')
def metadata():
    meta = {'gpg_fpr': config.JOURNALIST_KEY,
            'sd_version': version.__version__,
            }
    resp = make_response(json.dumps(meta))
    resp.headers['Content-Type'] = 'application/json'
    return resp


if __name__ == "__main__":  # pragma: no cover
    debug = getattr(config, 'env', 'prod') != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8080)
