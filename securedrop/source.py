# -*- coding: utf-8 -*-
import os
from datetime import datetime
import uuid
from functools import wraps

from flask import (Flask, request, render_template, session, redirect, url_for,
                   flash, abort, g, send_file)
from flask_wtf.csrf import CsrfProtect

import config
import version
import crypto_util
import store
import background
import zipfile
from cStringIO import StringIO

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
    # ignore_static here because `crypto_util.shash` is bcrypt (very time consuming),
    # and we don't need to waste time running if we're just serving a static
    # resource that won't need to access these common values.
    if logged_in():
        g.flagged = session['flagged']
        g.codename = session['codename']
        g.sid = crypto_util.shash(g.codename)
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
    return render_template('generate.html', codename=session['codename'])


@app.route('/create', methods=['POST'])
def create():
    sid = crypto_util.shash(session['codename'])
    if os.path.exists(store.path(sid)):
        # if this happens, we're not using very secure crypto
        store.log("Got a duplicate ID '%s'" % sid)
    else:
        os.mkdir(store.path(sid))
    session['logged_in'] = True
    session['flagged'] = False
    return redirect(url_for('lookup'))


@app.route('/lookup', methods=('GET',))
@login_required
def lookup():
    msgs = []
    flagged = False
    for fn in os.listdir(g.loc):
        if fn == '_FLAG':
            flagged = True
            continue
        if fn.startswith('reply-'):
            msg_candidate = crypto_util.decrypt(
                g.sid, g.codename, file(store.path(g.sid, fn)).read())
            try:
                msgs.append(dict(
                        id=fn,
                        date=str(
                            datetime.fromtimestamp(
                                os.stat(store.path(g.sid, fn)).st_mtime)),
                        msg=msg_candidate.decode()))
            except UnicodeDecodeError:
                # todo: we should have logging here!
                pass
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

    return render_template(
        'lookup.html', codename=g.codename, msgs=msgs, flagged=flagged,
        haskey=crypto_util.getkey(g.sid))


@app.route('/submit', methods=('POST',))
@login_required
def submit():
    msg = request.form['msg']
    fh = request.files['fh']

    if msg:
        msg_loc = store.path(g.sid, '%s_msg.gpg' % uuid.uuid4())
        crypto_util.encrypt(config.JOURNALIST_KEY, msg, msg_loc)
        flash("Thanks! We received your message.", "notification")
    if fh:
        file_loc = store.path(g.sid, "%s_doc.zip.gpg" % uuid.uuid4())

        s = StringIO()
        zip_file = zipfile.ZipFile(s, 'w')
        zip_file.writestr(fh.filename, fh.read())
        zip_file.close()
        s.reset()

        crypto_util.encrypt(config.JOURNALIST_KEY, s, file_loc)
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
    crypto_util.secureunlink(store.path(g.sid, msgid))
    flash("Reply deleted.", "notification")

    return redirect(url_for('lookup'))


def valid_codename(codename):
    return os.path.exists(store.path(crypto_util.shash(codename)))


@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        codename = request.form['codename']
        if valid_codename(codename):
            session.update(codename=codename, logged_in=True)
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


@app.errorhandler(404)
def page_not_found(error):
    return render_template('notfound.html'), 404

if __name__ == "__main__":
    # TODO make sure debug is not on in production
    app.run(debug=True, port=8080)
