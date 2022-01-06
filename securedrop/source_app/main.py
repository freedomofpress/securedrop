import operator
import os
import io

from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from typing import Union

import werkzeug
from flask import (Blueprint, render_template, flash, redirect, url_for,
                   session, current_app, request, Markup, abort, g)
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
    clear_session_and_redirect_to_logged_out_page
from source_app.forms import LoginForm, SubmissionForm
from source_user import InvalidPassphraseError, create_source_user, \
    SourcePassphraseCollisionError, SourceDesignationCollisionError, SourceUser


def make_blueprint(config: SDConfig) -> Blueprint:
    view = Blueprint('main', __name__)

    @view.route('/')
    def index() -> str:
        return render_template('index.html')

    @view.route('/generate', methods=('GET',))
    def generate() -> Union[str, werkzeug.Response]:
        if SessionManager.is_user_logged_in(db_session=db.session):
            flash(gettext(
                "You were redirected because you are already logged in. "
                "If you want to create a new account, you should log out "
                "first."),
                  "notification")
            return redirect(url_for('.lookup'))

        codename = PassphraseGenerator.get_default().generate_passphrase(
            preferred_language=g.localeinfo.language
        )

        # Generate a unique id for each browser tab and associate the codename with this id.
        # This will allow retrieval of the codename displayed in the tab from which the source has
        # clicked to proceed to /generate (ref. issue #4458)
        tab_id = urlsafe_b64encode(os.urandom(64)).decode()
        codenames = session.get('codenames', {})
        codenames[tab_id] = codename
        session['codenames'] = fit_codenames_into_cookie(codenames)
        session["codenames_expire"] = datetime.now(timezone.utc) + timedelta(
            minutes=config.SESSION_EXPIRATION_MINUTES
        )
        return render_template('generate.html', codename=codename, tab_id=tab_id)

    @view.route('/create', methods=['POST'])
    def create() -> werkzeug.Response:
        if SessionManager.is_user_logged_in(db_session=db.session):
            flash(gettext("You are already logged in. Please verify your codename above as it " +
                          "may differ from the one displayed on the previous page."),
                  'notification')
        else:
            # Ensure the codenames have not expired
            date_codenames_expire = session.get("codenames_expire")
            if not date_codenames_expire or datetime.now(timezone.utc) >= date_codenames_expire:
                return clear_session_and_redirect_to_logged_out_page(flask_session=session)

            tab_id = request.form['tab_id']
            codename = session['codenames'][tab_id]
            del session['codenames']

            try:
                current_app.logger.info("Creating new source user...")
                create_source_user(
                    db_session=db.session,
                    source_passphrase=codename,
                    source_app_storage=Storage.get_default(),
                )
            except (SourcePassphraseCollisionError, SourceDesignationCollisionError) as e:
                current_app.logger.error("Could not create a source: {}".format(e))
                flash(
                    gettext(
                        "There was a temporary problem creating your account. Please try again."
                    ),
                    "error"
                )
                return redirect(url_for('.index'))

            # All done - source user was successfully created
            current_app.logger.info("New source user created")
            session['new_user_codename'] = codename
            SessionManager.log_user_in(db_session=db.session,
                                       supplied_passphrase=DicewarePassphrase(codename))

        return redirect(url_for('.lookup'))

    @view.route('/lookup', methods=('GET',))
    @login_required
    def lookup(logged_in_source: SourceUser) -> str:
        replies = []
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

        return render_template(
            'lookup.html',
            is_user_logged_in=True,
            allow_document_uploads=InstanceConfig.get_default().allow_document_uploads,
            replies=replies,
            new_user_codename=session.get('new_user_codename', None),
            form=SubmissionForm(),
        )

    @view.route('/submit', methods=('POST',))
    @login_required
    def submit(logged_in_source: SourceUser) -> werkzeug.Response:
        allow_document_uploads = InstanceConfig.get_default().allow_document_uploads
        form = SubmissionForm()
        if not form.validate():
            for field, errors in form.errors.items():
                for error in errors:
                    flash(error, "error")
            return redirect(f"{url_for('main.lookup')}#flashed")

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
            return redirect(f"{url_for('main.lookup')}#flashed")

        fnames = []
        logged_in_source_in_db = logged_in_source.get_db_record()
        first_submission = logged_in_source_in_db.interaction_count == 0

        if not os.path.exists(Storage.get_default().path(logged_in_source.filesystem_id)):
            current_app.logger.debug("Store directory not found for source '{}', creating one."
                                     .format(logged_in_source_in_db.journalist_designation))
            os.mkdir(Storage.get_default().path(logged_in_source.filesystem_id))

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

        if first_submission:
            flash_message = render_template(
                'first_submission_flashed_message.html',
                new_user_codename=session.get('new_user_codename', None),
            )
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
            submission = Submission(logged_in_source_in_db, fname, Storage.get_default())
            db.session.add(submission)
            new_submissions.append(submission)

        logged_in_source_in_db.pending = False
        logged_in_source_in_db.last_updated = datetime.now(timezone.utc)
        db.session.commit()

        for sub in new_submissions:
            store.async_add_checksum_for_file(sub, Storage.get_default())

        normalize_timestamps(logged_in_source)

        return redirect(f"{url_for('main.lookup')}#flashed")

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

        flash(gettext("Reply deleted"), "notification")
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

        flash(gettext("All replies have been deleted"), "notification")
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
                flash(gettext("Sorry, that is not a recognized codename."), "error")
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

    return view
