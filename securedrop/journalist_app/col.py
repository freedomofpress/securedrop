# -*- coding: utf-8 -*-

from flask import (Blueprint, redirect, url_for, render_template, flash,
                   request, abort, send_file, current_app)
from flask_babel import gettext
from sqlalchemy.orm.exc import NoResultFound

import crypto_util
import store

from db import db_session, Submission
from journalist_app.forms import ReplyForm
from journalist_app.utils import (make_star_true, make_star_false, get_source,
                                  delete_collection, col_download_unread,
                                  col_download_all, col_star, col_un_star,
                                  col_delete)


def make_blueprint(config):
    view = Blueprint('col', __name__)

    @view.route('/add_star/<filesystem_id>', methods=('POST',))
    def add_star(filesystem_id):
        make_star_true(filesystem_id)
        db_session.commit()
        return redirect(url_for('main.index'))

    @view.route("/remove_star/<filesystem_id>", methods=('POST',))
    def remove_star(filesystem_id):
        make_star_false(filesystem_id)
        db_session.commit()
        return redirect(url_for('main.index'))

    @view.route('/<filesystem_id>')
    def col(filesystem_id):
        form = ReplyForm()
        source = get_source(filesystem_id)
        source.has_key = crypto_util.getkey(filesystem_id)
        return render_template("col.html", filesystem_id=filesystem_id,
                               source=source, form=form)

    @view.route('/delete/<filesystem_id>', methods=('POST',))
    def delete_single(filesystem_id):
        """deleting a single collection from its /col page"""
        source = get_source(filesystem_id)
        delete_collection(filesystem_id)
        flash(gettext("{source_name}'s collection deleted")
              .format(source_name=source.journalist_designation),
              "notification")
        return redirect(url_for('main.index'))

    @view.route('/process', methods=('POST',))
    def process():
        actions = {'download-unread': col_download_unread,
                   'download-all': col_download_all, 'star': col_star,
                   'un-star': col_un_star, 'delete': col_delete}
        if 'cols_selected' not in request.form:
            flash(gettext('No collections selected.'), 'error')
            return redirect(url_for('main.index'))

        # getlist is cgi.FieldStorage.getlist
        cols_selected = request.form.getlist('cols_selected')
        action = request.form['action']

        if action not in actions:
            return abort(500)

        method = actions[action]
        return method(cols_selected)

    @view.route('/<filesystem_id>/<fn>')
    def download_single_submission(filesystem_id, fn):
        """Sends a client the contents of a single submission."""
        if '..' in fn or fn.startswith('/'):
            abort(404)

        try:
            Submission.query.filter(
                Submission.filename == fn).one().downloaded = True
            db_session.commit()
        except NoResultFound as e:
            current_app.logger.error(
                "Could not mark " + fn + " as downloaded: %s" % (e,))

        return send_file(store.path(filesystem_id, fn),
                         mimetype="application/pgp-encrypted")

    return view
