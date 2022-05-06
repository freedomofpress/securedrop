import operator
import os
import io

from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from typing import Union

import werkzeug
from flask import (Blueprint, render_template, redirect, url_for,
                   session, current_app, request, abort, g, make_response)
from flask_babel import gettext

import store

from store import Storage

from db import db
from encryption import EncryptionManager, GpgKeyNotFoundError

from models import Submission, Reply, get_one_or_else, InstanceConfig
from passphrases import PassphraseGenerator, DicewarePassphrase
from sdconfig import SDConfig
from source_app.decorators import login_required
from source_app.session_manager import SessionManager
from source_app.utils import normalize_timestamps, fit_codenames_into_cookie, \
    clear_session_and_redirect_to_logged_out_page, codename_detected, flash_msg
from source_app.forms import LoginForm, SubmissionForm
from source_user import InvalidPassphraseError, create_source_user, \
    SourcePassphraseCollisionError, SourceDesignationCollisionError, SourceUser


def make_blueprint(config: SDConfig) -> Blueprint:
    view = Blueprint('main', __name__)

    @view.route('/')
    def index() -> Union[str, werkzeug.Response]:
        # Behave like a webmail application
        if SessionManager.is_user_logged_in(db_session=db.session):
            return redirect(url_for('.lookup'))
        return render_template('index.html')

    @view.route('/lookup', methods=('POST', 'GET'))
    def lookup() -> Union[str, werkzeug.Response]:
        if request.method == 'POST':
            # Try to detect Tor2Web usage by looking to see if tor2web_check got mangled
            tor2web_check = request.form.get('tor2web_check')
            if tor2web_check is None:
                # Missing form field
                abort(403)
            elif tor2web_check != 'href="fake.onion"':
                return redirect(url_for('info.tor2web_warning'))

        is_user_logged_in = SessionManager.is_user_logged_in(db_session=db.session)
        replies = []
        if is_user_logged_in:
            logged_in_source = SessionManager.get_logged_in_user(db_session=db.session)
            logged_in_source_in_db = logged_in_source.get_db_record()
            source_inbox = Reply.query.filter_by(
                source_id=logged_in_source_in_db.id, deleted_by_source=False
            ).all()

            for reply in source_inbox:
                reply_path = Storage.get_default().path(
                    logged_in_source.filesystem_id,
                    reply.filename,
                )
                try:
                    with io.open(reply_path, "rb") as f:
                        contents = f.read()
                    decrypted_reply = EncryptionManager.get_default().decrypt_journalist_reply(
                        for_source_user=logged_in_source,
                        ciphertext_in=contents
                    )
                    reply.decrypted = decrypted_reply
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

            # If not done yet, generate a keypair to encrypt replies from the journalist
            encryption_mgr = EncryptionManager.get_default()
            try:
                encryption_mgr.get_source_public_key(logged_in_source.filesystem_id)
            except GpgKeyNotFoundError:
                encryption_mgr.generate_source_key_pair(logged_in_source)

            # If this user is logged in, they already submitted at least once
            min_message_length = 0
        else:
            min_message_length = InstanceConfig.get_default().initial_message_min_len

        return render_template(
            'lookup.html',
            is_user_logged_in=is_user_logged_in,
            allow_document_uploads=InstanceConfig.get_default().allow_document_uploads,
            replies=replies,
            min_len=min_message_length,
            new_user_codename=session.get('new_user_codename', None),
            form=SubmissionForm(),
        )

    @view.route('/submit', methods=('POST',))
    def submit() -> werkzeug.Response:
        # Flow inversion: generate codename and create user before processing their submission
        # rather than on the screen before
        if not SessionManager.is_user_logged_in(db_session=db.session):
            codename = PassphraseGenerator.get_default().generate_passphrase(
                preferred_language=g.localeinfo.language
            )
            try:
                current_app.logger.info("Creating new source user...")
                create_source_user(
                    db_session=db.session,
                    source_passphrase=codename,
                    source_app_storage=Storage.get_default(),
                )
            except (SourcePassphraseCollisionError, SourceDesignationCollisionError) as e:
                current_app.logger.error("Could not create a source: {}".format(e))
                flash_msg("error", None, gettext(
                    "There was a temporary problem creating your account. Please try again."))
                return redirect(url_for('.index'))

            # All done - source user was successfully created
            current_app.logger.info("New source user created")
            # Track that this user was generated during this session
            session['new_user_codename'] = codename
            logged_in_source = SessionManager.log_user_in(
                db_session=db.session,
                supplied_passphrase=DicewarePassphrase(codename)
            )
        else:
            logged_in_source = SessionManager.get_logged_in_user(db_session=db.session)

        allow_document_uploads = InstanceConfig.get_default().allow_document_uploads
        form = SubmissionForm()
        if not form.validate():
            for field, errors in form.errors.items():
                for error in errors:
                    flash_msg("error", None, error)
            return redirect(url_for('main.lookup'))

        msg = request.form['msg']
        fh = None
        if allow_document_uploads and 'fh' in request.files:
            fh = request.files['fh']

        # Don't submit anything if it was an "empty" submission. #878
        if not (msg or fh):
            if allow_document_uploads:
                html_contents = gettext("You must enter a message or choose a file to submit.")
            else:
                html_contents = gettext("You must enter a message.")

            flash_msg("error", None, html_contents)
            return redirect(url_for('main.lookup'))

        logged_in_source_in_db = logged_in_source.get_db_record()
        first_submission = logged_in_source_in_db.interaction_count == 0

        if first_submission:
            min_len = InstanceConfig.get_default().initial_message_min_len
            if (min_len > 0) and (msg and not fh) and (len(msg) < min_len):
                flash_msg("error", None, gettext(
                    "Your first message must be at least {} characters long.").format(min_len))
                return redirect(url_for('main.lookup'))

        # if the new_user_codename key is not present in the session, this is
        # not a first session - during the first session, the codename is displayed
        # throughout but we want to discourage sources from sharing it
        new_codename = session.get('new_user_codename', None)
        codenames_rejected = InstanceConfig.get_default().reject_message_with_codename

        if new_codename is not None and codenames_rejected and codename_detected(msg, new_codename):
            flash_msg("error", None, gettext("Please do not submit your codename!"),
                      gettext("Keep your codename secret, and use it to log in later to "
                              "check for replies."))
            return redirect(url_for('main.lookup'))

        if not os.path.exists(Storage.get_default().path(logged_in_source.filesystem_id)):
            current_app.logger.debug("Store directory not found for source '{}', creating one."
                                     .format(logged_in_source_in_db.journalist_designation))
            os.mkdir(Storage.get_default().path(logged_in_source.filesystem_id))

        fnames = []

        if msg:
            logged_in_source_in_db.interaction_count += 1
            fnames.append(
                Storage.get_default().save_message_submission(
                    logged_in_source_in_db.filesystem_id,
                    logged_in_source_in_db.interaction_count,
                    logged_in_source_in_db.journalist_filename,
                    msg))
        if fh:
            logged_in_source_in_db.interaction_count += 1
            fnames.append(
                Storage.get_default().save_file_submission(
                    logged_in_source_in_db.filesystem_id,
                    logged_in_source_in_db.interaction_count,
                    logged_in_source_in_db.journalist_filename,
                    fh.filename,
                    fh.stream))

        if first_submission or msg or fh:
            if first_submission:
                html_contents = gettext("Thank you for sending this information to us. Please "
                                        "check back later for replies.")
            elif msg and not fh:
                html_contents = gettext("Thanks! We received your message.")
            elif fh and not msg:
                html_contents = gettext("Thanks! We received your document.")
            else:
                html_contents = gettext("Thanks! We received your message and document.")

            flash_msg("success", gettext("Success!"), html_contents)

        new_submissions = []

        for fname in fnames:
            submission = Submission(logged_in_source_in_db, fname, Storage.get_default())
            db.session.add(submission)
            new_submissions.append(submission)

        logged_in_source_in_db.pending = False
        logged_in_source_in_db.last_updated = datetime.now(timezone.utc)
        db.session.commit()

        for sub in new_submissions:
            store.async_add_checksum_for_file(sub, Storage.get_default())

        normalize_timestamps(logged_in_source)

        return redirect(url_for('main.lookup'))

    @view.route('/delete', methods=('POST',))
    @login_required
    def delete(logged_in_source: SourceUser) -> werkzeug.Response:
        """This deletes the reply from the source's inbox, but preserves
        the history for journalists such that they can view conversation
        history.
        """

        query = Reply.query.filter_by(
            filename=request.form['reply_filename'],
            source_id=logged_in_source.db_record_id)
        reply = get_one_or_else(query, current_app.logger, abort)
        reply.deleted_by_source = True
        db.session.add(reply)
        db.session.commit()

        flash_msg("success", gettext("Success!"), gettext("Reply deleted"))
        return redirect(url_for('.lookup'))

    @view.route('/delete-all', methods=('POST',))
    @login_required
    def batch_delete(logged_in_source: SourceUser) -> werkzeug.Response:
        replies = Reply.query.filter(Reply.source_id == logged_in_source.db_record_id) \
                             .filter(Reply.deleted_by_source == False).all()  # noqa
        if len(replies) == 0:
            current_app.logger.error("Found no replies when at least one was "
                                     "expected")
            return redirect(url_for('.lookup'))

        for reply in replies:
            reply.deleted_by_source = True
            db.session.add(reply)
        db.session.commit()

        flash_msg("success", gettext("Success!"), gettext("All replies have been deleted"))
        return redirect(url_for('.lookup'))

    @view.route('/login', methods=('GET', 'POST'))
    def login() -> Union[str, werkzeug.Response]:
        form = LoginForm()
        if form.validate_on_submit():
            try:
                SessionManager.log_user_in(
                    db_session=db.session,
                    supplied_passphrase=DicewarePassphrase(request.form['codename'].strip())
                )
            except InvalidPassphraseError:
                current_app.logger.info("Login failed for invalid codename")
                flash_msg("error", None, gettext("Sorry, that is not a recognized codename."))
            else:
                # Success: a valid passphrase was supplied
                return redirect(url_for('.lookup', from_login='1'))

        return render_template('login.html', form=form)

    @view.route('/logout')
    def logout() -> Union[str, werkzeug.Response]:
        """
        If a user is logged in, show them a logout page that prompts them to
        click the New Identity button in Tor Browser to complete their session.
        Otherwise redirect to the main Source Interface page.
        """
        if SessionManager.is_user_logged_in(db_session=db.session):
            SessionManager.log_user_out()

            # Clear the session after we render the message so it's localized
            # If a user specified a locale, save it and restore it
            session.clear()
            session['locale'] = g.localeinfo.id

            return render_template('logout.html')
        else:
            return redirect(url_for('.index'))

    @view.route('/robots.txt')
    def robots_txt() -> werkzeug.Response:
        """Tell robots we don't want them"""
        resp = make_response("User-agent: *\nDisallow: /")
        resp.headers["content-type"] = "text/plain"
        return resp

    return view
