import operator
import os

from datetime import datetime
from flask import (Blueprint, render_template, flash, redirect, url_for, g,
                   session, current_app, request, Markup, abort)
from flask_babel import gettext
from sqlalchemy.exc import IntegrityError

import crypto_util
import store

from db import Source, db_session, Submission, Reply, get_one_or_else
from rm import srm
from source_app.decorators import login_required
from source_app.utils import (logged_in, generate_unique_codename,
                              async_genkey, normalize_timestamps,
                              valid_codename)


def add_blueprints(app):
    app.register_blueprint(_main_blueprint())


def _main_blueprint():
    view = Blueprint('main', 'main')

    @view.route('/')
    def index():
        return render_template('index.html')

    @view.route('/generate', methods=('GET', 'POST'))
    def generate():
        if logged_in():
            flash(gettext(
                "You were redirected because you are already logged in. "
                "If you want to create a new account, you should log out "
                "first."),
                  "notification")
            return redirect(url_for('.lookup'))

        codename = generate_unique_codename()
        session['codename'] = codename
        return render_template('generate.html', codename=codename)

    @view.route('/create', methods=['POST'])
    def create():
        filesystem_id = crypto_util.hash_codename(session['codename'])

        source = Source(filesystem_id, crypto_util.display_id())
        db_session.add(source)
        try:
            db_session.commit()
        except IntegrityError as e:
            current_app.logger.error(
                "Attempt to create a source with duplicate codename: %s" %
                (e,))
        else:
            os.mkdir(store.path(filesystem_id))

        session['logged_in'] = True
        return redirect(url_for('.lookup'))

    @view.route('/lookup', methods=('GET',))
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
                current_app.logger.error("Could not decode reply %s" %
                                         reply.filename)
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

    @view.route('/submit', methods=('POST',))
    @login_required
    def submit():
        msg = request.form['msg']
        fh = request.files['fh']

        # Don't submit anything if it was an "empty" submission. #878
        if not (msg or fh):
            flash(gettext(
                "You must enter a message or choose a file to submit."),
                  "error")
            return redirect(url_for('main.lookup'))

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

        return redirect(url_for('main.lookup'))

    @view.route('/delete', methods=('POST',))
    @login_required
    def delete():
        query = Reply.query.filter(
            Reply.filename == request.form['reply_filename'])
        reply = get_one_or_else(query, current_app.logger, abort)
        srm(store.path(g.filesystem_id, reply.filename))
        db_session.delete(reply)
        db_session.commit()

        flash(gettext("Reply deleted"), "notification")
        return redirect(url_for('.lookup'))

    @view.route('/delete-all', methods=('POST',))
    @login_required
    def batch_delete():
        replies = g.source.replies
        if len(replies) == 0:
            current_app.logger.error("Found no replies when at least one was "
                                     "expected")
            return redirect(url_for('.lookup'))

        for reply in replies:
            srm(store.path(g.filesystem_id, reply.filename))
            db_session.delete(reply)
        db_session.commit()

        flash(gettext("All replies have been deleted"), "notification")
        return redirect(url_for('.lookup'))

    @view.route('/login', methods=('GET', 'POST'))
    def login():
        if request.method == 'POST':
            codename = request.form['codename'].strip()
            if valid_codename(codename):
                session.update(codename=codename, logged_in=True)
                return redirect(url_for('.lookup', from_login='1'))
            else:
                current_app.logger.info(
                        "Login failed for invalid codename".format(codename))
                flash(gettext("Sorry, that is not a recognized codename."),
                      "error")
        return render_template('login.html')

    return view
