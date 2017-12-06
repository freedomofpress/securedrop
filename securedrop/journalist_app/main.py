# -*- coding: utf-8 -*-

from datetime import datetime
from flask import (Blueprint, request, current_app, session, url_for, redirect,
                   render_template, g, flash, abort)
from flask_babel import gettext
from sqlalchemy.sql.expression import false

import crypto_util
import store

from db import db_session, Source, SourceStar, Submission, Reply
from journalist_app.forms import ReplyForm
from journalist_app.utils import (validate_user, bulk_delete, download,
                                  confirm_bulk_delete, get_source)


def make_blueprint(config):
    view = Blueprint('main', __name__)

    @view.route('/login', methods=('GET', 'POST'))
    def login():
        if request.method == 'POST':
            user = validate_user(request.form['username'],
                                 request.form['password'],
                                 request.form['token'])
            if user:
                current_app.logger.info("'{}' logged in with the token {}"
                                        .format(request.form['username'],
                                                request.form['token']))

                # Update access metadata
                user.last_access = datetime.utcnow()
                db_session.add(user)
                db_session.commit()

                session['uid'] = user.id
                return redirect(url_for('main.index'))

        return render_template("login.html")

    @view.route('/logout')
    def logout():
        session.pop('uid', None)
        session.pop('expires', None)
        return redirect(url_for('main.index'))

    @view.route('/')
    def index():
        unstarred = []
        starred = []

        # Long SQLAlchemy statements look best when formatted according to
        # the Pocoo style guide, IMHO:
        # http://www.pocoo.org/internal/styleguide/
        sources = Source.query.filter_by(pending=False) \
                              .order_by(Source.last_updated.desc()) \
                              .all()
        for source in sources:
            star = SourceStar.query.filter_by(source_id=source.id).first()
            if star and star.starred:
                starred.append(source)
            else:
                unstarred.append(source)
            source.num_unread = len(
                Submission.query.filter_by(source_id=source.id,
                                           downloaded=False).all())

        return render_template('index.html',
                               unstarred=unstarred,
                               starred=starred)

    @view.route('/reply', methods=('POST',))
    def reply():
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
        crypto_util.encrypt(form.message.data,
                            [crypto_util.getkey(g.filesystem_id),
                             config.JOURNALIST_KEY],
                            output=store.path(g.filesystem_id, filename))
        reply = Reply(g.user, g.source, filename)

        try:
            db_session.add(reply)
            db_session.commit()
        except Exception as exc:
            flash(gettext(
                "An unexpected error occurred! Please "
                "inform your administrator."), "error")
            # We take a cautious approach to logging here because we're dealing
            # with responses to sources. It's possible the exception message
            # could contain information we don't want to write to disk.
            current_app.logger.error(
                "Reply from '{}' (ID {}) failed: {}!".format(g.user.username,
                                                             g.user.id,
                                                             exc.__class__))
        else:
            flash(gettext("Thanks. Your reply has been stored."),
                  "notification")
        finally:
            return redirect(url_for('col.col', filesystem_id=g.filesystem_id))

    @view.route('/flag', methods=('POST',))
    def flag():
        g.source.flagged = True
        db_session.commit()
        return render_template('flag.html', filesystem_id=g.filesystem_id,
                               codename=g.source.journalist_designation)

    @view.route('/bulk', methods=('POST',))
    def bulk():
        action = request.form['action']

        doc_names_selected = request.form.getlist('doc_names_selected')
        selected_docs = [doc for doc in g.source.collection
                         if doc.filename in doc_names_selected]
        if selected_docs == []:
            if action == 'download':
                flash(gettext("No collections selected for download."),
                      "error")
            elif action in ('delete', 'confirm_delete'):
                flash(gettext("No collections selected for deletion."),
                      "error")
            return redirect(url_for('col.col', filesystem_id=g.filesystem_id))

        if action == 'download':
            source = get_source(g.filesystem_id)
            return download(source.journalist_filename, selected_docs)
        elif action == 'delete':
            return bulk_delete(g.filesystem_id, selected_docs)
        elif action == 'confirm_delete':
            return confirm_bulk_delete(g.filesystem_id, selected_docs)
        else:
            abort(400)

    @view.route('/regenerate-code', methods=('POST',))
    def regenerate_code():
        original_journalist_designation = g.source.journalist_designation
        g.source.journalist_designation = crypto_util.display_id()

        for item in g.source.collection:
            item.filename = store.rename_submission(
                g.filesystem_id,
                item.filename,
                g.source.journalist_filename)
        db_session.commit()

        flash(gettext(
            "The source '{original_name}' has been renamed to '{new_name}'")
              .format(original_name=original_journalist_designation,
                      new_name=g.source.journalist_designation),
              "notification")
        return redirect(url_for('col.col', filesystem_id=g.filesystem_id))

    @view.route('/download_unread/<filesystem_id>')
    def download_unread_filesystem_id(filesystem_id):
        id = Source.query.filter(Source.filesystem_id == filesystem_id) \
            .one().id
        submissions = Submission.query.filter(
            Submission.source_id == id,
            Submission.downloaded == false()).all()
        if submissions == []:
            flash(gettext("No unread submissions for this source."))
            return redirect(url_for('col.col', filesystem_id=filesystem_id))
        source = get_source(filesystem_id)
        return download(source.journalist_filename, submissions)

    return view
