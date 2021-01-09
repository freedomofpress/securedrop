import operator
import os
import io

from base64 import urlsafe_b64encode
from datetime import datetime
from typing import Union

import werkzeug
from flask import (Blueprint, render_template, flash, redirect, url_for, g,
                   session, current_app, request, Markup, abort)
from flask_babel import gettext

import i18n
import store

from db import db
from models import Submission, Reply, get_one_or_else
from passphrases import PassphraseGenerator
from sdconfig import SDConfig
from source_app.decorators import login_required
from source_app.utils import (logged_in,
                              async_genkey, normalize_timestamps,
                              valid_codename, get_entropy_estimate)
from source_app.forms import LoginForm, SubmissionForm
from source_user import create_source_user, SourcePassphraseCollisionError, \
    SourceDesignationCollisionError


def make_blueprint(config: SDConfig) -> Blueprint:
    view = Blueprint('main', __name__)

    @view.route('/')
    def index() -> str:
        return render_template('index.html')

    @view.route('/generate', methods=('GET', 'POST'))
    def generate() -> Union[str, werkzeug.Response]:
        if logged_in():
            flash(gettext(
                "You were redirected because you are already logged in. "
                "If you want to create a new account, you should log out "
                "first."),
                  "notification")
            return redirect(url_for('.lookup'))

        codename = PassphraseGenerator.get_default().generate_passphrase(
            preferred_language=i18n.get_language(config)
        )

        # Generate a unique id for each browser tab and associate the codename with this id.
        # This will allow retrieval of the codename displayed in the tab from which the source has
        # clicked to proceed to /generate (ref. issue #4458)
        tab_id = urlsafe_b64encode(os.urandom(64)).decode()
        codenames = session.get('codenames', {})
        codenames[tab_id] = codename
        session['codenames'] = codenames

        session['new_user'] = True
        return render_template('generate.html', codename=codename, tab_id=tab_id)

    @view.route('/org-logo')
    def select_logo() -> werkzeug.Response:
        if current_app.static_folder is None:
            abort(500)
        if os.path.exists(os.path.join(current_app.static_folder, 'i',
                          'custom_logo.png')):
            return redirect(url_for('static', filename='i/custom_logo.png'))
        else:
            return redirect(url_for('static', filename='i/logo.png'))

    @view.route('/create', methods=['POST'])
    def create() -> werkzeug.Response:
        if logged_in():
            flash(gettext("You are already logged in. Please verify your codename above as it " +
                          "may differ from the one displayed on the previous page."),
                  'notification')
        else:
            tab_id = request.form['tab_id']
            codename = session['codenames'][tab_id]
            del session['codenames']

            try:
                current_app.logger.info("Creating new source user...")
                create_source_user(
                    db_session=db.session,
                    source_passphrase=codename,
                    source_app_crypto_util=current_app.crypto_util,
                    source_app_storage=current_app.storage,
                )
            except (SourcePassphraseCollisionError, SourceDesignationCollisionError) as e:
                current_app.logger.error("Could not create a source: {}".format(e))

                # Issue 4361: Delete 'logged_in' if it's in the session
                try:
                    del session['logged_in']
                except KeyError:
                    pass

                flash(
                    gettext(
                        "There was a temporary problem creating your account. Please try again."
                    ),
                    "error"
                )
                return redirect(url_for('.index'))

            # All done - source user was successfully created
            current_app.logger.info("New source user created")
            session['logged_in'] = True
            session['codename'] = codename

        return redirect(url_for('.lookup'))

    @view.route('/lookup', methods=('GET',))
    @login_required
    def lookup() -> str:
        replies = []
        source_inbox = Reply.query.filter(Reply.source_id == g.source.id) \
                                  .filter(Reply.deleted_by_source == False).all()  # noqa

        for reply in source_inbox:
            reply_path = current_app.storage.path(
                g.filesystem_id,
                reply.filename,
            )
            try:
                with io.open(reply_path, "rb") as f:
                    contents = f.read()
                reply_obj = current_app.crypto_util.decrypt(g.codename, contents)
                reply.decrypted = reply_obj
            except UnicodeDecodeError:
                current_app.logger.error("Could not decode reply %s" %
                                         reply.filename)
            except FileNotFoundError:
                current_app.logger.error("Reply file missing: %s" %
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
        if not current_app.crypto_util.get_fingerprint(g.filesystem_id) and \
                g.source.flagged:
            db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
            async_genkey(current_app.crypto_util,
                         db_uri,
                         g.filesystem_id,
                         g.codename)

        return render_template(
            'lookup.html',
            allow_document_uploads=current_app.instance_config.allow_document_uploads,
            codename=g.codename,
            replies=replies,
            flagged=g.source.flagged,
            new_user=session.get('new_user', None),
            haskey=current_app.crypto_util.get_fingerprint(g.filesystem_id),
            form=SubmissionForm(),
        )

    @view.route('/submit', methods=('POST',))
    @login_required
    def submit() -> werkzeug.Response:
        allow_document_uploads = current_app.instance_config.allow_document_uploads
        form = SubmissionForm()
        if not form.validate():
            for field, errors in form.errors.items():
                for error in errors:
                    flash(error, "error")
            return redirect(url_for('main.lookup'))

        msg = request.form['msg']
        fh = None
        if allow_document_uploads and 'fh' in request.files:
            fh = request.files['fh']

        # Don't submit anything if it was an "empty" submission. #878
        if not (msg or fh):
            if allow_document_uploads:
                flash(gettext(
                    "You must enter a message or choose a file to submit."),
                      "error")
            else:
                flash(gettext("You must enter a message."), "error")
            return redirect(url_for('main.lookup'))

        fnames = []
        journalist_filename = g.source.journalist_filename
        first_submission = g.source.interaction_count == 0

        if msg:
            g.source.interaction_count += 1
            fnames.append(
                current_app.storage.save_message_submission(
                    g.filesystem_id,
                    g.source.interaction_count,
                    journalist_filename,
                    msg))
        if fh:
            g.source.interaction_count += 1
            fnames.append(
                current_app.storage.save_file_submission(
                    g.filesystem_id,
                    g.source.interaction_count,
                    journalist_filename,
                    fh.filename,
                    fh.stream))

        if first_submission:
            flash_message = render_template('first_submission_flashed_message.html')
            flash(Markup(flash_message), "success")

        else:
            if msg and not fh:
                html_contents = gettext('Thanks! We received your message.')
            elif fh and not msg:
                html_contents = gettext('Thanks! We received your document.')
            else:
                html_contents = gettext('Thanks! We received your message and '
                                        'document.')

            flash_message = render_template(
                'next_submission_flashed_message.html',
                html_contents=html_contents
            )
            flash(Markup(flash_message), "success")

        new_submissions = []
        for fname in fnames:
            submission = Submission(g.source, fname)
            db.session.add(submission)
            new_submissions.append(submission)

        if g.source.pending:
            g.source.pending = False

            # Generate a keypair now, if there's enough entropy (issue #303)
            # (gpg reads 300 bytes from /dev/random)
            entropy_avail = get_entropy_estimate()
            if entropy_avail >= 2400:
                db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']

                async_genkey(current_app.crypto_util,
                             db_uri,
                             g.filesystem_id,
                             g.codename)
                current_app.logger.info("generating key, entropy: {}".format(
                    entropy_avail))
            else:
                current_app.logger.warning(
                        "skipping key generation. entropy: {}".format(
                                entropy_avail))

        g.source.last_updated = datetime.utcnow()
        db.session.commit()

        for sub in new_submissions:
            store.async_add_checksum_for_file(sub)

        normalize_timestamps(g.filesystem_id)

        return redirect(url_for('main.lookup'))

    @view.route('/delete', methods=('POST',))
    @login_required
    def delete() -> werkzeug.Response:
        """This deletes the reply from the source's inbox, but preserves
        the history for journalists such that they can view conversation
        history.
        """

        query = Reply.query.filter_by(
            filename=request.form['reply_filename'],
            source_id=g.source.id)
        reply = get_one_or_else(query, current_app.logger, abort)
        reply.deleted_by_source = True
        db.session.add(reply)
        db.session.commit()

        flash(gettext("Reply deleted"), "notification")
        return redirect(url_for('.lookup'))

    @view.route('/delete-all', methods=('POST',))
    @login_required
    def batch_delete() -> werkzeug.Response:
        replies = Reply.query.filter(Reply.source_id == g.source.id) \
                             .filter(Reply.deleted_by_source == False).all()  # noqa
        if len(replies) == 0:
            current_app.logger.error("Found no replies when at least one was "
                                     "expected")
            return redirect(url_for('.lookup'))

        for reply in replies:
            reply.deleted_by_source = True
            db.session.add(reply)
        db.session.commit()

        flash(gettext("All replies have been deleted"), "notification")
        return redirect(url_for('.lookup'))

    @view.route('/login', methods=('GET', 'POST'))
    def login() -> Union[str, werkzeug.Response]:
        form = LoginForm()
        if form.validate_on_submit():
            codename = request.form['codename'].strip()
            if valid_codename(codename):
                session.update(codename=codename, logged_in=True)
                return redirect(url_for('.lookup', from_login='1'))
            else:
                current_app.logger.info(
                        "Login failed for invalid codename")
                flash(gettext("Sorry, that is not a recognized codename."),
                      "error")
        return render_template('login.html', form=form)

    @view.route('/logout')
    def logout() -> Union[str, werkzeug.Response]:
        """
        If a user is logged in, show them a logout page that prompts them to
        click the New Identity button in Tor Browser to complete their session.
        Otherwise redirect to the main Source Interface page.
        """
        if logged_in():

            # Clear the session after we render the message so it's localized
            # If a user specified a locale, save it and restore it
            user_locale = g.locale
            session.clear()
            session['locale'] = user_locale

            return render_template('logout.html')
        else:
            return redirect(url_for('.index'))

    return view
