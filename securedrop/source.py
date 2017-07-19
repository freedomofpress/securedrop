# -*- coding: utf-8 -*-
import os
from datetime import datetime
from functools import wraps
from cStringIO import StringIO
import subprocess
from threading import Thread
import operator
from flask import (Flask, request, render_template, session, redirect, url_for,
                   flash, abort, g, send_file, Markup, make_response)
from flask_wtf.csrf import CSRFProtect
from flask_assets import Environment

from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.exc import IntegrityError

import config
import json
import version
import crypto_util
from flask_babel import gettext
from rm import srm
import i18n
import store
import template_filters
from db import db_session, Source, Submission, Reply, get_one_or_else
from request_that_secures_file_uploads import RequestThatSecuresFileUploads
from jinja2 import evalcontextfilter

import logging
# This module's logger is explicitly labeled so the correct logger is used,
# even when this is run from the command line (e.g. during development)
log = logging.getLogger('source')

app = Flask(__name__, template_folder=config.SOURCE_TEMPLATES_DIR)
app.request_class = RequestThatSecuresFileUploads
app.config.from_object(config.SourceInterfaceFlaskConfig)

i18n.setup_app(app)

assets = Environment(app)

# The default CSRF token expiration is 1 hour. Since large uploads can
# take longer than an hour over Tor, we increase the valid window to 24h.
app.config['WTF_CSRF_TIME_LIMIT'] = 60 * 60 * 24
CSRFProtect(app)

app.jinja_env.globals['version'] = version.__version__
if getattr(config, 'CUSTOM_HEADER_IMAGE', None):
    app.jinja_env.globals['header_image'] = config.CUSTOM_HEADER_IMAGE
    app.jinja_env.globals['use_custom_header_image'] = True
else:
    app.jinja_env.globals['header_image'] = 'logo.png'
    app.jinja_env.globals['use_custom_header_image'] = False

app.jinja_env.filters['datetimeformat'] = template_filters.datetimeformat
app.jinja_env.filters['nl2br'] = evalcontextfilter(template_filters.nl2br)


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
    """Only executes the wrapped function if we're not loading
    a static resource."""
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
    g.locale = i18n.get_locale()
    g.locales = i18n.get_locale2name()
    # ignore_static here because `crypto_util.hash_codename` is scrypt (very
    # time consuming), and we don't need to waste time running if we're just
    # serving a static resource that won't need to access these common values.
    if logged_in():
        g.codename = session['codename']
        g.filesystem_id = crypto_util.hash_codename(g.codename)
        try:
            g.source = Source.query \
                             .filter(Source.filesystem_id == g.filesystem_id) \
                             .one()
        except MultipleResultsFound as e:
            app.logger.error(
                "Found multiple Sources when one was expected: %s" %
                (e,))
            abort(500)
        except NoResultFound as e:
            app.logger.error(
                "Found no Sources when one was expected: %s" %
                (e,))
            del session['logged_in']
            del session['codename']
            return redirect(url_for('index'))
        g.loc = store.path(g.filesystem_id)


@app.before_request
@ignore_static
def check_tor2web():
    # ignore_static here so we only flash a single message warning
    # about Tor2Web, corresponding to the initial page load.
    if 'X-tor2web' in request.headers:
        flash(Markup(gettext(
            '<strong>WARNING:</strong> You appear to be using Tor2Web. '
            'This <strong>does not</strong> provide anonymity. '
            '<a href="/tor2web-warning">Why is this dangerous?</a>')),
              "banner-warning")


@app.route('/')
def index():
    return render_template('index.html')


def generate_unique_codename():
    """Generate random codenames until we get an unused one"""
    while True:
        codename = crypto_util.genrandomid(Source.NUM_WORDS)

        # The maximum length of a word in the wordlist is 9 letters and the
        # codename length is 7 words, so it is currently impossible to
        # generate a codename that is longer than the maximum codename length
        # (currently 128 characters). This code is meant to be defense in depth
        # to guard against potential future changes, such as modifications to
        # the word list or the maximum codename length.
        if len(codename) > Source.MAX_CODENAME_LEN:
            app.logger.warning(
                    "Generated a source codename that was too long, "
                    "skipping it. This should not happen. "
                    "(Codename='{}')".format(codename))
            continue

        filesystem_id = crypto_util.hash_codename(codename)  # scrypt (slow)
        matching_sources = Source.query.filter(
            Source.filesystem_id == filesystem_id).all()
        if len(matching_sources) == 0:
            return codename


@app.route('/generate', methods=('GET', 'POST'))
def generate():
    if logged_in():
        flash(gettext(
            "You were redirected because you are already logged in. "
            "If you want to create a new account, you should log out first."),
              "notification")
        return redirect(url_for('lookup'))

    codename = generate_unique_codename()
    session['codename'] = codename
    return render_template('generate.html', codename=codename)


@app.route('/create', methods=['POST'])
def create():
    filesystem_id = crypto_util.hash_codename(session['codename'])

    source = Source(filesystem_id, crypto_util.display_id())
    db_session.add(source)
    try:
        db_session.commit()
    except IntegrityError as e:
        app.logger.error(
            "Attempt to create a source with duplicate codename: %s" %
            (e,))
    else:
        os.mkdir(store.path(filesystem_id))

    session['logged_in'] = True
    return redirect(url_for('lookup'))


def async(f):
    def wrapper(*args, **kwargs):
        thread = Thread(target=f, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


@async
def async_genkey(filesystem_id, codename):
    crypto_util.genkeypair(filesystem_id, codename)

    # Register key generation as update to the source, so sources will
    # filter to the top of the list in the journalist interface if a
    # flagged source logs in and has a key generated for them. #789
    try:
        source = Source.query.filter(Source.filesystem_id == filesystem_id) \
                       .one()
        source.last_updated = datetime.utcnow()
        db_session.commit()
    except Exception as e:
        app.logger.error("async_genkey for source "
                         "(filesystem_id={}): {}".format(filesystem_id, e))


@app.route('/lookup', methods=('GET',))
@login_required
def lookup():
    replies = []
    for reply in g.source.replies:
        reply_path = store.path(g.filesystem_id, reply.filename)
        try:
            reply.decrypted = crypto_util.decrypt(
                g.codename,
                open(reply_path).read()).decode('utf-8')
        except UnicodeDecodeError:
            app.logger.error("Could not decode reply %s" % reply.filename)
        else:
            reply.date = datetime.utcfromtimestamp(
                os.stat(reply_path).st_mtime)
            replies.append(reply)

    # Sort the replies by date
    replies.sort(key=operator.attrgetter('date'), reverse=True)

    # Generate a keypair to encrypt replies from the journalist
    # Only do this if the journalist has flagged the source as one
    # that they would like to reply to. (Issue #140.)
    if not crypto_util.getkey(g.filesystem_id) and g.source.flagged:
        async_genkey(g.filesystem_id, g.codename)

    return render_template(
        'lookup.html',
        codename=g.codename,
        replies=replies,
        flagged=g.source.flagged,
        haskey=crypto_util.getkey(
            g.filesystem_id))


def normalize_timestamps(filesystem_id):
    """
    Update the timestamps on all of the source's submissions to match that of
    the latest submission. This minimizes metadata that could be useful to
    investigators. See #301.
    """
    sub_paths = [store.path(filesystem_id, submission.filename)
                 for submission in g.source.submissions]
    if len(sub_paths) > 1:
        args = ["touch"]
        args.extend(sub_paths[:-1])
        rc = subprocess.call(args)
        if rc != 0:
            app.logger.warning(
                "Couldn't normalize submission "
                "timestamps (touch exited with %d)" %
                rc)


@app.route('/submit', methods=('POST',))
@login_required
def submit():
    msg = request.form['msg']
    fh = request.files['fh']

    # Don't bother submitting anything if it was an "empty" submission. #878.
    if not (msg or fh):
        flash(gettext(
            "You must enter a message or choose a file to submit."),
              "error")
        return redirect(url_for('lookup'))

    fnames = []
    journalist_filename = g.source.journalist_filename
    first_submission = g.source.interaction_count == 0

    if msg:
        g.source.interaction_count += 1
        fnames.append(
            store.save_message_submission(
                g.filesystem_id,
                g.source.interaction_count,
                journalist_filename,
                msg))
    if fh:
        g.source.interaction_count += 1
        fnames.append(
            store.save_file_submission(
                g.filesystem_id,
                g.source.interaction_count,
                journalist_filename,
                fh.filename,
                fh.stream))

    if first_submission:
        msg = render_template('first_submission_flashed_message.html')
        flash(Markup(msg), "success")

    else:
        if msg and not fh:
            things = 'message'
        elif not msg and fh:
            things = 'document'
        else:
            things = 'message and document'

        msg = render_template('next_submission_flashed_message.html',
                              things=things)
        flash(Markup(msg), "success")

    for fname in fnames:
        submission = Submission(g.source, fname)
        db_session.add(submission)

    if g.source.pending:
        g.source.pending = False

        # Generate a keypair now, if there's enough entropy (issue #303)
        entropy_avail = int(
            open('/proc/sys/kernel/random/entropy_avail').read())
        if entropy_avail >= 2400:
            async_genkey(g.filesystem_id, g.codename)

    g.source.last_updated = datetime.utcnow()
    db_session.commit()
    normalize_timestamps(g.filesystem_id)

    return redirect(url_for('lookup'))


@app.route('/delete', methods=('POST',))
@login_required
def delete():
    query = Reply.query.filter(
        Reply.filename == request.form['reply_filename'])
    reply = get_one_or_else(query, app.logger, abort)
    srm(store.path(g.filesystem_id, reply.filename))
    db_session.delete(reply)
    db_session.commit()

    flash(gettext("Reply deleted"), "notification")
    return redirect(url_for('lookup'))


@app.route('/delete-all', methods=('POST',))
@login_required
def batch_delete():
    replies = g.source.replies
    if len(replies) == 0:
        app.logger.error("Found no replies when at least one was expected")
        return redirect(url_for('lookup'))
    for reply in replies:
        srm(store.path(g.filesystem_id, reply.filename))
        db_session.delete(reply)
    db_session.commit()

    flash(gettext("All replies have been deleted"), "notification")
    return redirect(url_for('lookup'))


def valid_codename(codename):
    # Ignore codenames that are too long to avoid DoS
    if len(codename) > Source.MAX_CODENAME_LEN:
        app.logger.info(
                "Ignored attempted login because the codename was too long.")
        return False

    try:
        filesystem_id = crypto_util.hash_codename(codename)
    except crypto_util.CryptoException as e:
        app.logger.info(
                "Could not compute filesystem ID for codename '{}': {}".format(
                    codename, e))
        abort(500)

    source = Source.query.filter_by(filesystem_id=filesystem_id).first()
    return source is not None


@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        codename = request.form['codename'].strip()
        if valid_codename(codename):
            session.update(codename=codename, logged_in=True)
            return redirect(url_for('lookup', from_login='1'))
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
    return redirect(url_for('index'))


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


@app.errorhandler(404)
def page_not_found(error):
    return render_template('notfound.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html'), 500


if __name__ == "__main__":  # pragma: no cover
    debug = getattr(config, 'env', 'prod') != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8080)
