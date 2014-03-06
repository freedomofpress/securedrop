# -*- coding: utf-8 -*-
import os
from datetime import datetime
import uuid
from functools import wraps
import zipfile
from cStringIO import StringIO

import logging
# This module's logger is explicitly labeled so the correct logger is used,
# even when this is run from the command line (e.g. during development)
log = logging.getLogger('source')

from flask import (Flask, request, render_template, session, redirect, url_for,
                   flash, abort, g, send_file)
from flask_wtf.csrf import CsrfProtect

import config
import version
import crypto_util
import store
import background
from db import db_session, Source

app = Flask(__name__, template_folder=config.SOURCE_TEMPLATES_DIR)
app.config.from_object(config.FlaskConfig)
CsrfProtect(app)

app.jinja_env.globals['version'] = version.__version__
if getattr(config, 'CUSTOM_HEADER_IMAGE', None):
    app.jinja_env.globals['header_image'] = config.CUSTOM_HEADER_IMAGE
    app.jinja_env.globals['use_custom_header_image'] = True
else:
    app.jinja_env.globals['header_image'] = 'securedrop.png'
    app.jinja_env.globals['use_custom_header_image'] = False


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Automatically remove database sessions at the end of the request, or
    when the application shuts down"""
    db_session.remove()


def logged_in():
    if 'logged_in' in session:
        return True


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not logged_in():
            return redirect(url_for('lookup'))
        return f(*args, **kwargs)
    return decorated_function


def ignore_static(f):
    """Only executes the wrapped function if we're not loading a static resource."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.path.startswith('/static'):
            return  # don't execute the decorated function
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
@ignore_static
def setup_g():
    """Store commonly used values in Flask's special g object"""
    # ignore_static here because `crypto_util.hash_codename` is scrypt (very
    # time consuming), and we don't need to waste time running if we're just
    # serving a static resource that won't need to access these common values.
    if logged_in():
        # We use session.get (which defaults to None if 'flagged' is not in the
        # session) to avoid a KeyError on the redirect from login/ to lookup/
        g.flagged = session.get('flagged')
        g.codename = session['codename']
        g.sid = crypto_util.hash_codename(g.codename)
        g.loc = store.path(g.sid)


@app.before_request
@ignore_static
def check_tor2web():
        # ignore_static here so we only flash a single message warning about Tor2Web,
        # corresponding to the intial page load.
    if 'X-tor2web' in request.headers:
        flash('<strong>WARNING:</strong> You appear to be using Tor2Web. '
              'This <strong>does not</strong> provide anonymity. '
              '<a href="/tor2web-warning">Why is this dangerous?</a>',
              "header-warning")


@app.after_request
def no_cache(response):
    """Minimize potential traces of site access by telling the browser not to
    cache anything"""
    no_cache_headers = {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '-1',
    }
    for header, header_value in no_cache_headers.iteritems():
        response.headers.add(header, header_value)
    return response


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=('GET', 'POST'))
def generate():
    number_words = 8
    if request.method == 'POST':
        number_words = int(request.form['number-words'])
        if number_words not in range(7, 11):
            abort(403)
    session['codename'] = crypto_util.genrandomid(number_words)
    # TODO: make sure this codename isn't a repeat
    return render_template('generate.html', codename=session['codename'])


@app.route('/create', methods=['POST'])
def create():
    sid = crypto_util.hash_codename(session['codename'])

    source = Source(sid, crypto_util.display_id())
    db_session.add(source)
    db_session.commit()

    if os.path.exists(store.path(sid)):
        # if this happens, we're not using very secure crypto
        log.warning("Got a duplicate ID '%s'" % sid)
    else:
        os.mkdir(store.path(sid))

    session['logged_in'] = True
    session['flagged'] = False
    return redirect(url_for('lookup'))


@app.route('/lookup', methods=('GET',))
@login_required
def lookup():
    replies = []
    flagged = False
    for fn in os.listdir(g.loc):
        # TODO: make 'flag' a db column, so we can replace this with a db
        # lookup in the future
        if fn == '_FLAG':
            flagged = True
        elif fn.startswith('reply-'):
            try:
                msg = crypto_util.decrypt(g.sid, g.codename,
                        file(store.path(g.sid, fn)).read()).decode("utf-8")
            except UnicodeDecodeError:
                app.logger.error("Could not decode reply %s" % fn)
            else:
                date = str(datetime.fromtimestamp(
                           os.stat(store.path(g.sid, fn)).st_mtime))
                replies.append(dict(id=fn, date=date, msg=msg))

    if flagged:
        session['flagged'] = True

    def async_genkey(sid, codename):
        with app.app_context():
            background.execute(lambda: crypto_util.genkeypair(sid, codename))

    # Generate a keypair to encrypt replies from the journalist
    # Only do this if the journalist has flagged the source as one
    # that they would like to reply to. (Issue #140.)
    if not crypto_util.getkey(g.sid) and flagged:
        async_genkey(g.sid, g.codename)

    return render_template('lookup.html', codename=g.codename, msgs=replies,
            flagged=flagged, haskey=crypto_util.getkey(g.sid))


@app.route('/submit', methods=('POST',))
@login_required
def submit():
    msg = request.form['msg']
    fh = request.files['fh']

    if msg:
        store.save_message_submission(g.sid, msg)
        flash("Thanks! We received your message.", "notification")
    if fh:
        store.save_file_submission(g.sid, fh.filename, fh.stream)
        flash("Thanks! We received your document '%s'."
              % fh.filename or '[unnamed]', "notification")

    return redirect(url_for('lookup'))


@app.route('/delete', methods=('POST',))
@login_required
def delete():
    msgid = request.form['msgid']
    assert '/' not in msgid
    potential_files = os.listdir(g.loc)
    if msgid not in potential_files:
        abort(404)  # TODO are the checks necessary?
    store.secure_unlink(store.path(g.sid, msgid))
    flash("Reply deleted.", "notification")

    return redirect(url_for('lookup'))


def valid_codename(codename):
    return os.path.exists(store.path(crypto_util.hash_codename(codename)))

def check_flagged(codename):
    # TODO: make 'flag' a db column, so we can replace this with a db lookup in
    # the future
    flagged = False
    sid = crypto_util.hash_codename(codename)
    try:
        loc = store.path(sid)
    except:
        return flagged
    for fn in os.listdir(loc):
        if fn=='_FLAG':
            flagged = True
            break
    return flagged

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        codename = request.form['codename']
        if valid_codename(codename):
            flagged = check_flagged(codename)
            session.update(codename=codename, flagged=flagged, logged_in=True)
            return redirect(url_for('lookup'))
        else:
            flash("Sorry, that is not a recognized codename.", "error")
    return render_template('login.html')


@app.route('/howto-disable-js')
def howto_disable_js():
    return render_template("howto-disable-js.html")


@app.route('/tor2web-warning')
def tor2web_warning():
    return render_template("tor2web-warning.html")


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


_REDIRECT_URL_WHITELIST = ["http://tor2web.org/",
        "https://www.torproject.org/download.html.en",
        "https://tails.boum.org/",
        "http://www.wired.com/threatlevel/2013/09/freedom-hosting-fbi/",
        "http://www.theguardian.com/world/interactive/2013/oct/04/egotistical-giraffe-nsa-tor-document",
        "https://addons.mozilla.org/en-US/firefox/addon/noscript/",
        "http://noscript.net"]


@app.route('/redirect/<path:redirect_url>')
def redirect_hack(redirect_url):
    # A hack to avoid referer leakage when a user clicks on an external link.
    # TODO: Most likely will want to share this between source.py and
    # journalist.py in the future.
    if redirect_url not in _REDIRECT_URL_WHITELIST:
        return 'Redirect not allowed'
    else:
        return render_template("redirect.html", redirect_url=redirect_url)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('notfound.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html'), 500

if __name__ == "__main__":
    # TODO make sure debug is not on in production
    app.run(debug=True, host='0.0.0.0', port=8080)
