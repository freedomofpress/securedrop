# -*- coding: utf-8 -*-
from cStringIO import StringIO
from flask import (request, render_template, session, redirect, url_for,
                   flash, g, send_file, Markup, make_response)

import config
import json
import version
import crypto_util
from flask_babel import gettext
from rm import srm
import store
from db import db_session
from source_app import create_app
from source_app.decorators import login_required
from source_app.utils import logged_in, valid_codename

import logging
# This module's logger is explicitly labeled so the correct logger is used,
# even when this is run from the command line (e.g. during development)
log = logging.getLogger('source')

app = create_app()


@app.route('/delete-all', methods=('POST',))
@login_required
def batch_delete():
    replies = g.source.replies
    if len(replies) == 0:
        app.logger.error("Found no replies when at least one was expected")
        return redirect(url_for('main.lookup'))
    for reply in replies:
        srm(store.path(g.filesystem_id, reply.filename))
        db_session.delete(reply)
    db_session.commit()

    flash(gettext("All replies have been deleted"), "notification")
    return redirect(url_for('main.lookup'))


@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        codename = request.form['codename'].strip()
        if valid_codename(codename):
            session.update(codename=codename, logged_in=True)
            return redirect(url_for('main.lookup', from_login='1'))
        else:
            app.logger.info(
                    "Login failed for invalid codename".format(codename))
            flash(gettext("Sorry, that is not a recognized codename."),
                  "error")
    return render_template('login.html')


@app.route('/logout')
def logout():
    if logged_in():
        session.clear()
        msg = render_template('logout_flashed_message.html')
        flash(Markup(msg), "important hide-if-not-tor-browser")
    return redirect(url_for('main.index'))


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
