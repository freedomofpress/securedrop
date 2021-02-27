# -*- coding: utf-8 -*-

from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
    Markup,
    escape,
)
import werkzeug
from flask_babel import gettext
from sqlalchemy.orm.exc import NoResultFound

from db import db
from models import Reply, Submission
from journalist_app.forms import ReplyForm
from journalist_app.utils import (make_star_true, make_star_false, get_source,
                                  delete_collection, col_download_unread,
                                  col_download_all, col_star, col_un_star,
                                  col_delete, col_delete_data, mark_seen)
from sdconfig import SDConfig


def make_blueprint(config: SDConfig) -> Blueprint:
    view = Blueprint('col', __name__)

    @view.route('/add_star/<filesystem_id>', methods=('POST',))
    def add_star(filesystem_id: str) -> werkzeug.Response:
        make_star_true(filesystem_id)
        db.session.commit()
        return redirect(url_for('main.index'))

    @view.route("/remove_star/<filesystem_id>", methods=('POST',))
    def remove_star(filesystem_id: str) -> werkzeug.Response:
        make_star_false(filesystem_id)
        db.session.commit()
        return redirect(url_for('main.index'))

    @view.route('/<filesystem_id>')
    def col(filesystem_id: str) -> str:
        form = ReplyForm()
        source = get_source(filesystem_id)
        source.has_key = current_app.crypto_util.get_fingerprint(filesystem_id)
        return render_template("col.html", filesystem_id=filesystem_id,
                               source=source, form=form)

    @view.route('/delete/<filesystem_id>', methods=('POST',))
    def delete_single(filesystem_id: str) -> werkzeug.Response:
        """deleting a single collection from its /col page"""
        source = get_source(filesystem_id)
        try:
            delete_collection(filesystem_id)
        except ValueError as e:
            current_app.logger.error("error deleting collection: %s", e)
            abort(500)

        flash(
            Markup(
                "<b>{}</b> {}".format(
                    # Translators: Precedes a message confirming the success of an operation.
                    escape(gettext("Success!")),
                    escape(gettext(
                        "The account and data for the source {} have been deleted.").format(
                            source.journalist_designation))
                )
            ), 'success')

        return redirect(url_for('main.index'))

    @view.route('/process', methods=('POST',))
    def process() -> werkzeug.Response:
        actions = {'download-unread': col_download_unread,
                   'download-all': col_download_all, 'star': col_star,
                   'un-star': col_un_star, 'delete': col_delete,
                   'delete-data': col_delete_data}
        if 'cols_selected' not in request.form:
            flash(
                Markup("<b>{}</b> {}".format(
                    # Translators: Error shown when a user has not selected items to act on.
                    escape(gettext('Nothing Selected')),
                    escape(gettext('You must select one or more items.'))
                    )
                ), 'error')
            return redirect(url_for('main.index'))

        # getlist is cgi.FieldStorage.getlist
        cols_selected = request.form.getlist('cols_selected')
        action = request.form['action']

        if action not in actions:
            return abort(500)

        method = actions[action]
        return method(cols_selected)

    @view.route('/<filesystem_id>/<fn>')
    def download_single_file(filesystem_id: str, fn: str) -> werkzeug.Response:
        """
        Marks the file being download (the file being downloaded is either a submission message,
        submission file attachement, or journalist reply) as seen by the current logged-in user and
        send the file to a client to be saved or opened.
        """
        if '..' in fn or fn.startswith('/'):
            abort(404)

        file = current_app.storage.path(filesystem_id, fn)
        if not Path(file).is_file():
            flash(
                gettext(
                    "Your download failed because a file could not be found. An admin can find "
                    + "more information in the system and monitoring logs."
                ),
                "error"
            )
            current_app.logger.error("File {} not found".format(file))
            return redirect(url_for("col.col", filesystem_id=filesystem_id))

        # mark as seen by the current user
        try:
            journalist = g.get("user")
            if fn.endswith("reply.gpg"):
                reply = Reply.query.filter(Reply.filename == fn).one()
                mark_seen([reply], journalist)
            elif fn.endswith("-doc.gz.gpg") or fn.endswith("doc.zip.gpg"):
                file = Submission.query.filter(Submission.filename == fn).one()
                mark_seen([file], journalist)
            else:
                message = Submission.query.filter(Submission.filename == fn).one()
                mark_seen([message], journalist)
        except NoResultFound as e:
            current_app.logger.error("Could not mark {} as seen: {}".format(fn, e))

        return send_file(current_app.storage.path(filesystem_id, fn),
                         mimetype="application/pgp-encrypted")

    return view
