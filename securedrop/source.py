# -*- coding: utf-8 -*-
import os
from datetime import datetime
import uuid
from functools import wraps
import zipfile
from cStringIO import StringIO
import subprocess
from threading import Thread

import logging
# This module's logger is explicitly labeled so the correct logger is used,
# even when this is run from the command line (e.g. during development)
log = logging.getLogger('source')

from flask import (Flask, request, render_template, session, redirect, url_for,
                   flash, abort, g, send_file)
from flask_wtf.csrf import CsrfProtect
from flask.ext.babel import Babel, _

from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.exc import IntegrityError

import config
import version
import crypto_util
import store
import template_filters
from db import db_session, Source, Submission
from jinja2 import evalcontextfilter

app = Flask(__name__, template_folder=config.SOURCE_TEMPLATES_DIR)
app.config.from_object(config.SourceInterfaceFlaskConfig)
CsrfProtect(app)

babel = Babel(app)

app.jinja_env.globals['version'] = version.__version__
if getattr(config, 'CUSTOM_HEADER_IMAGE', None):
    app.jinja_env.globals['header_image'] = config.CUSTOM_HEADER_IMAGE
    app.jinja_env.globals['use_custom_header_image'] = True
else:
    app.jinja_env.globals['header_image'] = 'logo.png'
    app.jinja_env.globals['use_custom_header_image'] = False

app.jinja_env.filters['datetimeformat'] = template_filters.datetimeformat
app.jinja_env.filters['nl2br'] = evalcontextfilter(template_filters.nl2br)


@babel.localeselector
def get_locale():
    locale = session.get("locale")
    try:
        if locale and locale in config.LOCALES.keys():
            return locale
        return request.accept_languages.best_match(config.LOCALES.keys())
    except AttributeError:
        app.logger.warning("LOCALES is not defined in config")
        return None


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Automatically remove database sessions at the end of the request, or
    when the application shuts down"""
    db_session.remove()


def logged_in():
    return 'logged_in' in session


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not logged_in():
            return redirect(url_for('login'))
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
        g.codename = session['codename']
        g.sid = crypto_util.hash_codename(g.codename)
        try:
            g.source = Source.query.filter(Source.filesystem_id == g.sid).one()
        except MultipleResultsFound as e:
            app.logger.error("Found multiple Sources when one was expected: %s" % (e,))
            abort(500)
        except NoResultFound as e:
            app.logger.error("Found no Sources when one was expected: %s" % (e,))
            del session['logged_in']
            del session['codename']
            return redirect(url_for('index'))
        g.loc = store.path(g.sid)


@app.before_request
@ignore_static
def check_tor2web():
        # ignore_static here so we only flash a single message warning about Tor2Web,
        # corresponding to the intial page load.
    if 'X-tor2web' in request.headers:
        flash(_('<strong>WARNING:</strong> You appear to be using Tor2Web. '
              'This <strong>does not</strong> provide anonymity. '
              '%(tor2web_warning)s',
              tor2web_warning='<a href="/tor2web-warning">{}</a>'.format(_('Why is this dangerous?'))),
              "banner-warning")


@app.before_request
@ignore_static
def apply_locale():
    try:
        if 'l' in request.args:
            locale = request.args['l']
            if locale in config.LOCALES.keys():
                session['locale'] = locale
            elif len(locale) == 0 and 'locale' in session:
                del session['locale']
    except AttributeError:
        pass
    # Save the resolved locale in g for templates
    g.resolved_locale = get_locale()
    g.locales = getattr(config, 'LOCALES', None)


@app.route('/')
def index():
    return render_template('index.html')


def generate_unique_codename(num_words):
    """Generate random codenames until we get an unused one"""
    while True:
        codename = crypto_util.genrandomid(num_words)
        sid = crypto_util.hash_codename(codename) # scrypt (slow)
        matching_sources = Source.query.filter(Source.filesystem_id == sid).all()
        if len(matching_sources) == 0:
            return codename


@app.route('/generate', methods=('GET', 'POST'))
def generate():
    # Popping this key prevents errors when a logged in user returns to /generate.
    # TODO: is this the best experience? A logged in user will be automatically
    # logged out if they navigate to /generate by accident, which could be
    # confusing. It might be better to instead redirect them to the lookup
    # page, or inform them that they're logged in.
    session.pop('logged_in', None)

    num_words = 7
    if request.method == 'POST':
        num_words = int(request.form['number-words'])
        if num_words not in range(7, 11):
            abort(403)

    codename = generate_unique_codename(num_words)
    session['codename'] = codename
    return render_template('generate.html', codename=codename, num_words=num_words)


@app.route('/create', methods=['POST'])
def create():
    sid = crypto_util.hash_codename(session['codename'])

    source = Source(sid, crypto_util.display_id())
    db_session.add(source)
    try:
        db_session.commit()
    except IntegrityError as e:
        app.logger.error("Attempt to create a source with duplicate codename: %s" % (e,))
    else:
        os.mkdir(store.path(sid))

    session['logged_in'] = True
    return redirect(url_for('lookup'))


def async(f):
    def wrapper(*args, **kwargs):
        thread = Thread(target=f, args=args, kwargs=kwargs)
        thread.start()
    return wrapper

@async
def async_genkey(sid, codename):
    crypto_util.genkeypair(sid, codename)

    # Register key generation as update to the source, so sources will
    # filter to the top of the list in the document interface if a
    # flagged source logs in and has a key generated for them. #789
    try:
        source = Source.query.filter(Source.filesystem_id == sid).one()
        source.last_updated = datetime.utcnow()
        db_session.commit()
    except Exception as e:
        app.logger.error("async_genkey for source (sid={}): {}".format(sid, e))


@app.route('/lookup', methods=('GET',))
@login_required
def lookup():
    replies = []
    for fn in os.listdir(g.loc):
        if fn.endswith('-reply.gpg'):
            try:
                msg = crypto_util.decrypt(g.codename,
                        file(store.path(g.sid, fn)).read()).decode("utf-8")
            except UnicodeDecodeError:
                app.logger.error("Could not decode reply %s" % fn)
            else:
                date = datetime.utcfromtimestamp(os.stat(store.path(g.sid, fn)).st_mtime)
                replies.append(dict(id=fn, date=date, msg=msg))

    # Sort the replies by date
    replies.sort(key=lambda reply: reply['date'], reverse=True)

    # Generate a keypair to encrypt replies from the journalist
    # Only do this if the journalist has flagged the source as one
    # that they would like to reply to. (Issue #140.)
    if not crypto_util.getkey(g.sid) and g.source.flagged:
        async_genkey(g.sid, g.codename)

    return render_template('lookup.html', codename=g.codename, replies=replies,
            flagged=g.source.flagged, haskey=crypto_util.getkey(g.sid))


def normalize_timestamps(sid):
    """
    Update the timestamps on all of the source's submissions to match that of
    the latest submission. This minimizes metadata that could be useful to
    investigators. See #301.
    """
    sub_paths = [ store.path(sid, submission.filename)
                  for submission in g.source.submissions ]
    if len(sub_paths) > 1:
        args = ["touch"]
        args.extend(sub_paths[:-1])
        rc = subprocess.call(args)
        if rc != 0:
            app.logger.warning("Couldn't normalize submission timestamps (touch exited with %d)" % rc)


@app.route('/submit', methods=('POST',))
@login_required
def submit():
    msg = request.form['msg']
    fh = request.files['fh']

    fnames = []
    journalist_filename = g.source.journalist_filename()
    first_submission = g.source.interaction_count == 0

    if msg:
        g.source.interaction_count += 1
        fnames.append(store.save_message_submission(g.sid, g.source.interaction_count,
            journalist_filename, msg))
        flash(_("Thanks! We received your message."), "notification")
    if fh:
        g.source.interaction_count += 1
        fnames.append(store.save_file_submission(g.sid, g.source.interaction_count,
            journalist_filename, fh.filename, fh.stream))
        flash(_("Thanks! We received your document \"%(filename)s\".",
                filename=fh.filename or '[unnamed]'), "notification")

    if first_submission:
        flash(_("Thanks for submitting something to SecureDrop! Please check back later for replies."),
              "notification")

    for fname in fnames:
        submission = Submission(g.source, fname)
        db_session.add(submission)

    if g.source.pending:
        g.source.pending = False

        # Generate a keypair now, if there's enough entropy (issue #303)
        entropy_avail = int(open('/proc/sys/kernel/random/entropy_avail').read())
        if entropy_avail >= 2400:
            async_genkey(g.sid, g.codename)

    g.source.last_updated = datetime.utcnow()
    db_session.commit()
    normalize_timestamps(g.sid)

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
    flash(_("Reply deleted"), "notification")

    return redirect(url_for('lookup'))


def valid_codename(codename):
    return os.path.exists(store.path(crypto_util.hash_codename(codename)))

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        codename = request.form['codename']
        try:
            valid = valid_codename(codename)
        except crypto_util.CryptoException:
            pass
        else:
            if valid:
                session.update(codename=codename, logged_in=True)
                return redirect(url_for('lookup', from_login='1'))
        flash(_("Sorry, that is not a recognized codename."), "error")
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

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html'), 500

def write_pidfile():
    pid = str(os.getpid())
    with open(config.SOURCE_PIDFILE, 'w') as fp:
        fp.write(pid)

if __name__ == "__main__":
    write_pidfile()
    # TODO make sure debug is not on in production
    app.run(debug=True, host='0.0.0.0', port=8080)
