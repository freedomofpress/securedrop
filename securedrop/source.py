# -*- coding: utf-8 -*-
import os
from datetime import datetime
from cStringIO import StringIO
import operator
from flask import (request, render_template, session, redirect, url_for,
                   flash, abort, g, send_file, Markup, make_response)

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
from db import db_session, Source, Submission, Reply, get_one_or_else
from source_app import create_app
from source_app.decorators import login_required, ignore_static
from source_app.utils import (logged_in, valid_codename, async_genkey,
                              generate_unique_codename, normalize_timestamps)

import logging
# This module's logger is explicitly labeled so the correct logger is used,
# even when this is run from the command line (e.g. during development)
log = logging.getLogger('source')

app = create_app()


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Automatically remove database sessions at the end of the request, or
    when the application shuts down"""
    db_session.remove()


@app.before_request
@ignore_static
def setup_g():
    """Store commonly used values in Flask's special g object"""
    g.locale = i18n.get_locale()
    g.text_direction = i18n.get_text_direction(g.locale)
    g.html_lang = i18n.locale_to_rfc_5646(g.locale)
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
            return redirect(url_for('main.index'))
        g.loc = store.path(g.filesystem_id)


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
            html_contents = gettext('Thanks! We received your message.')
        elif not msg and fh:
            html_contents = gettext('Thanks! We received your document.')
        else:
            html_contents = gettext('Thanks! We received your message and '
                                    'document.')

        msg = render_template('next_submission_flashed_message.html',
                              html_contents=html_contents)
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
