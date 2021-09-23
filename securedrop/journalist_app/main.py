# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Union

import werkzeug
from flask import (Blueprint, request, current_app, session, url_for, redirect,
                   render_template, g, flash, abort, Markup, escape)
from flask_babel import gettext
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func

import store

from db import db
from models import SeenReply, Source, SourceStar, Submission, Reply
from journalist_app.forms import ReplyForm
from journalist_app.utils import (validate_user, bulk_delete, download,
                                  confirm_bulk_delete, get_source)
from sdconfig import SDConfig


def make_blueprint(config: SDConfig) -> Blueprint:
    view = Blueprint('main', __name__)

    @view.route('/login', methods=('GET', 'POST'))
    def login() -> Union[str, werkzeug.Response]:
        if request.method == 'POST':
            user = validate_user(request.form['username'],
                                 request.form['password'],
                                 request.form['token'])
            if user:
                current_app.logger.info("'{}' logged in with the two-factor code {}"
                                        .format(request.form['username'],
                                                request.form['token']))

                # Update access metadata
                user.last_access = datetime.utcnow()
                db.session.add(user)
                db.session.commit()

                session['uid'] = user.id
                session['nonce'] = user.session_nonce
                return redirect(url_for('main.index'))

        return render_template("login.html")

    @view.route('/logout')
    def logout() -> werkzeug.Response:
        session.pop('uid', None)
        session.pop('expires', None)
        session.pop('nonce', None)
        return redirect(url_for('main.index'))

    @view.route("/")
    def index() -> str:
        # Gather the count of unread submissions for each source
        # ID. This query will be joined in the queries for starred and
        # unstarred sources below, and the unread counts added to
        # their result sets as an extra column.
        unread_stmt = (
            db.session.query(Submission.source_id, func.count("*").label("num_unread"))
            .filter_by(seen_files=None, seen_messages=None)
            .group_by(Submission.source_id)
            .subquery()
        )

        # Query for starred sources, along with their unread
        # submission counts.
        starred = (
            db.session.query(Source, unread_stmt.c.num_unread)
            .filter_by(pending=False, deleted_at=None)
            .filter(Source.last_updated.isnot(None))
            .filter(SourceStar.starred.is_(True))
            .outerjoin(SourceStar)
            .options(joinedload(Source.submissions))
            .options(joinedload(Source.star))
            .outerjoin(unread_stmt, Source.id == unread_stmt.c.source_id)
            .order_by(Source.last_updated.desc())
            .all()
        )

        # Now, add "num_unread" attributes to the source entities.
        for source, num_unread in starred:
            source.num_unread = num_unread or 0
        starred = [source for source, num_unread in starred]

        # Query for sources without stars, along with their unread
        # submission counts.
        unstarred = (
            db.session.query(Source, unread_stmt.c.num_unread)
            .filter_by(pending=False, deleted_at=None)
            .filter(Source.last_updated.isnot(None))
            .filter(~Source.star.has(SourceStar.starred.is_(True)))
            .options(joinedload(Source.submissions))
            .options(joinedload(Source.star))
            .outerjoin(unread_stmt, Source.id == unread_stmt.c.source_id)
            .order_by(Source.last_updated.desc())
            .all()
        )

        # Again, add "num_unread" attributes to the source entities.
        for source, num_unread in unstarred:
            source.num_unread = num_unread or 0
        unstarred = [source for source, num_unread in unstarred]

        response = render_template("index.html", unstarred=unstarred, starred=starred)
        return response

    @view.route('/reply', methods=('POST',))
    def reply() -> werkzeug.Response:
        """Attempt to send a Reply from a Journalist to a Source. Empty
        messages are rejected, and an informative error message is flashed
        on the client. In the case of unexpected errors involving database
        transactions (potentially caused by racing request threads that
        modify the same the database object) logging is done in such a way
        so as not to write potentially sensitive information to disk, and a
        generic error message is flashed on the client.

        Returns:
           flask.Response: The user is redirected to the same Source
               collection view, regardless if the Reply is created
               successfully.
        """
        form = ReplyForm()
        if not form.validate_on_submit():
            for error in form.message.errors:
                flash(error, "error")
            return redirect(url_for('col.col', filesystem_id=g.filesystem_id))

        g.source.interaction_count += 1
        filename = "{0}-{1}-reply.gpg".format(g.source.interaction_count,
                                              g.source.journalist_filename)
        current_app.crypto_util.encrypt(
            form.message.data,
            [current_app.crypto_util.get_fingerprint(g.filesystem_id),
             config.JOURNALIST_KEY],
            output=current_app.storage.path(g.filesystem_id, filename),
        )

        try:
            reply = Reply(g.user, g.source, filename)
            db.session.add(reply)
            db.session.flush()
            seen_reply = SeenReply(reply_id=reply.id, journalist_id=g.user.id)
            db.session.add(seen_reply)
            db.session.commit()
            store.async_add_checksum_for_file(reply)
        except Exception as exc:
            flash(gettext(
                "An unexpected error occurred! Please "
                "inform your admin."), "error")
            # We take a cautious approach to logging here because we're dealing
            # with responses to sources. It's possible the exception message
            # could contain information we don't want to write to disk.
            current_app.logger.error(
                "Reply from '{}' (ID {}) failed: {}!".format(g.user.username,
                                                             g.user.id,
                                                             exc.__class__))
        else:

            flash(
                Markup(
                    "<b>{}</b> {}".format(
                        # Translators: Precedes a message confirming the success of an operation.
                        escape(gettext("Success!")),
                        escape(gettext("The source will receive your reply "
                                       "next time they log in."))
                    )
                ), 'success')
        finally:
            return redirect(url_for('col.col', filesystem_id=g.filesystem_id))

    @view.route('/bulk', methods=('POST',))
    def bulk() -> Union[str, werkzeug.Response]:
        action = request.form['action']
        error_redirect = url_for('col.col', filesystem_id=g.filesystem_id)
        doc_names_selected = request.form.getlist('doc_names_selected')
        selected_docs = [doc for doc in g.source.collection
                         if doc.filename in doc_names_selected]
        if selected_docs == []:
            if action == 'download':
                flash(
                    Markup(
                        "<b>{}</b> {}".format(
                            # Translators: Error shown when a user has not selected items to act on.
                            escape(gettext("Nothing Selected")),
                            escape(gettext("You must select one or more items for download"))
                        )
                    ), 'error')
            elif action in ('delete', 'confirm_delete'):
                flash(
                    Markup(
                        "<b>{}</b> {}".format(
                            # Translators: Error shown when a user has not selected items to act on.
                            escape(gettext("Nothing Selected")),
                            escape(gettext("You must select one or more items for deletion"))
                        )
                    ), 'error')

            return redirect(error_redirect)

        if action == 'download':
            source = get_source(g.filesystem_id)
            return download(
                source.journalist_filename, selected_docs, on_error_redirect=error_redirect
            )
        elif action == 'delete':
            return bulk_delete(g.filesystem_id, selected_docs)
        elif action == 'confirm_delete':
            return confirm_bulk_delete(g.filesystem_id, selected_docs)
        else:
            abort(400)

    @view.route('/download_unread/<filesystem_id>')
    def download_unread_filesystem_id(filesystem_id: str) -> werkzeug.Response:
        unseen_submissions = (
            Submission.query.join(Source)
            .filter(
                Source.deleted_at.is_(None),
                Source.filesystem_id == filesystem_id
            )
            .filter(~Submission.seen_files.any(), ~Submission.seen_messages.any())
            .all()
        )
        if len(unseen_submissions) == 0:
            flash(gettext("No unread submissions for this source."), "error")
            return redirect(url_for('col.col', filesystem_id=filesystem_id))
        source = get_source(filesystem_id)
        return download(source.journalist_filename, unseen_submissions)

    return view
