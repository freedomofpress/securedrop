# -*- coding: utf-8 -*-

from flask import (request, render_template, send_file, redirect, flash,
                   url_for, abort)
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import false

import config
import crypto_util
from flask_babel import gettext
import store
from db import db_session, Source, Submission

from journalist_app import create_app
from journalist_app.decorators import login_required
from journalist_app.forms import ReplyForm
from journalist_app.utils import (get_source, download,
                                  make_star_true, make_star_false, col_star,
                                  col_un_star,
                                  delete_collection, col_delete,
                                  col_download_unread,
                                  col_download_all)

app = create_app(config)


@app.route('/col/add_star/<filesystem_id>', methods=('POST',))
@login_required
def add_star(filesystem_id):
    make_star_true(filesystem_id)
    db_session.commit()
    return redirect(url_for('main.index'))


@app.route("/col/remove_star/<filesystem_id>", methods=('POST',))
@login_required
def remove_star(filesystem_id):
    make_star_false(filesystem_id)
    db_session.commit()
    return redirect(url_for('main.index'))


@app.route('/col/<filesystem_id>')
@login_required
def col(filesystem_id):
    form = ReplyForm()
    source = get_source(filesystem_id)
    source.has_key = crypto_util.getkey(filesystem_id)
    return render_template("col.html", filesystem_id=filesystem_id,
                           source=source, form=form)


@app.route('/col/process', methods=('POST',))
@login_required
def col_process():
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


@app.route('/col/delete/<filesystem_id>', methods=('POST',))
@login_required
def col_delete_single(filesystem_id):
    """deleting a single collection from its /col page"""
    source = get_source(filesystem_id)
    delete_collection(filesystem_id)
    flash(gettext("{source_name}'s collection deleted")
          .format(source_name=source.journalist_designation),
          "notification")
    return redirect(url_for('main.index'))


@app.route('/col/<filesystem_id>/<fn>')
@login_required
def download_single_submission(filesystem_id, fn):
    """Sends a client the contents of a single submission."""
    if '..' in fn or fn.startswith('/'):
        abort(404)

    try:
        Submission.query.filter(
            Submission.filename == fn).one().downloaded = True
        db_session.commit()
    except NoResultFound as e:
        app.logger.error("Could not mark " + fn + " as downloaded: %s" % (e,))

    return send_file(store.path(filesystem_id, fn),
                     mimetype="application/pgp-encrypted")


@app.route('/download_unread/<filesystem_id>')
@login_required
def download_unread_filesystem_id(filesystem_id):
    id = Source.query.filter(Source.filesystem_id == filesystem_id).one().id
    submissions = Submission.query.filter(
        Submission.source_id == id,
        Submission.downloaded == false()).all()
    if submissions == []:
        flash(gettext("No unread submissions for this source."))
        return redirect(url_for('col', filesystem_id=filesystem_id))
    source = get_source(filesystem_id)
    return download(source.journalist_filename, submissions)


if __name__ == "__main__":  # pragma: no cover
    debug = getattr(config, 'env', 'prod') != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8081)
