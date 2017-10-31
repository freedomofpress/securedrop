# -*- coding: utf-8 -*-

from flask import (request, render_template, send_file, redirect, flash,
                   url_for, g, abort)
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import false

import config
import crypto_util
from flask_babel import gettext
import store
from db import db_session, Source, Journalist, Submission, Reply

from journalist_app import create_app
from journalist_app.decorators import login_required, admin_required
from journalist_app.forms import ReplyForm
from journalist_app.utils import (get_source, validate_user, download,
                                  bulk_delete, confirm_bulk_delete,
                                  make_star_true, make_star_false, col_star,
                                  col_un_star, make_password,
                                  delete_collection, col_delete,
                                  set_diceware_password, col_download_unread,
                                  col_download_all)

app = create_app(config)


class PasswordMismatchError(Exception):
    pass


@app.route('/admin/edit/<int:user_id>/new-password', methods=('POST',))
@admin_required
def admin_set_diceware_password(user_id):
    try:
        user = Journalist.query.get(user_id)
    except NoResultFound:
        abort(404)

    password = request.form.get('password')
    set_diceware_password(user, password)
    return redirect(url_for('admin.edit_user', user_id=user_id))


@app.route('/admin/delete/<int:user_id>', methods=('POST',))
@admin_required
def admin_delete_user(user_id):
    user = Journalist.query.get(user_id)
    if user:
        db_session.delete(user)
        db_session.commit()
        flash(gettext("Deleted user '{user}'").format(
            user=user.username), "notification")
    else:
        app.logger.error(
            "Admin {} tried to delete nonexistent user with pk={}".format(
                g.user.username, user_id))
        abort(404)

    return redirect(url_for('admin.index'))


@app.route('/account', methods=('GET',))
@login_required
def edit_account():
    password = make_password()
    return render_template('edit_account.html',
                           password=password)


@app.route('/account/new-password', methods=('POST',))
@login_required
def new_password():
    user = g.user
    current_password = request.form.get('current_password')
    token = request.form.get('token')
    error_message = gettext('Incorrect password or two-factor code.')
    # If the user is validated, change their password
    if validate_user(user.username, current_password, token, error_message):
        password = request.form.get('password')
        set_diceware_password(user, password)
    return redirect(url_for('edit_account'))


@app.route('/admin/edit/<int:user_id>/new-password', methods=('POST',))
@admin_required
def admin_new_password(user_id):
    try:
        user = Journalist.query.get(user_id)
    except NoResultFound:
        abort(404)

    password = request.form.get('password')
    set_diceware_password(user, password)
    return redirect(url_for('admin.edit_user', user_id=user_id))


@app.route('/account/2fa', methods=('GET', 'POST'))
@login_required
def account_new_two_factor():
    if request.method == 'POST':
        token = request.form['token']
        if g.user.verify_token(token):
            flash(gettext("Token in two-factor authentication verified."),
                  "notification")
            return redirect(url_for('edit_account'))
        else:
            flash(gettext(
                "Could not verify token in two-factor authentication."),
                  "error")

    return render_template('account_new_two_factor.html', user=g.user)


@app.route('/account/reset-2fa-totp', methods=['POST'])
@login_required
def account_reset_two_factor_totp():
    g.user.is_totp = True
    g.user.regenerate_totp_shared_secret()
    db_session.commit()
    return redirect(url_for('account_new_two_factor'))


@app.route('/account/reset-2fa-hotp', methods=['POST'])
@login_required
def account_reset_two_factor_hotp():
    otp_secret = request.form.get('otp_secret', None)
    if otp_secret:
        g.user.set_hotp_secret(otp_secret)
        db_session.commit()
        return redirect(url_for('account_new_two_factor'))
    else:
        return render_template('account_edit_hotp_secret.html')


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


@app.route('/reply', methods=('POST',))
@login_required
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
        return redirect(url_for('col', filesystem_id=g.filesystem_id))

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
        # with responses to sources. It's possible the exception message could
        # contain information we don't want to write to disk.
        app.logger.error(
            "Reply from '{}' (ID {}) failed: {}!".format(g.user.username,
                                                         g.user.id,
                                                         exc.__class__))
    else:
        flash(gettext("Thanks. Your reply has been stored."),
              "notification")
    finally:
        return redirect(url_for('col', filesystem_id=g.filesystem_id))


@app.route('/regenerate-code', methods=('POST',))
@login_required
def generate_code():
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
    return redirect('/col/' + g.filesystem_id)


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


@app.route('/bulk', methods=('POST',))
@login_required
def bulk():
    action = request.form['action']

    doc_names_selected = request.form.getlist('doc_names_selected')
    selected_docs = [doc for doc in g.source.collection
                     if doc.filename in doc_names_selected]
    if selected_docs == []:
        if action == 'download':
            flash(gettext("No collections selected for download."), "error")
        elif action in ('delete', 'confirm_delete'):
            flash(gettext("No collections selected for deletion."), "error")
        return redirect(url_for('col', filesystem_id=g.filesystem_id))

    if action == 'download':
        source = get_source(g.filesystem_id)
        return download(source.journalist_filename, selected_docs)
    elif action == 'delete':
        return bulk_delete(g.filesystem_id, selected_docs)
    elif action == 'confirm_delete':
        return confirm_bulk_delete(g.filesystem_id, selected_docs)
    else:
        abort(400)


@app.route('/flag', methods=('POST',))
@login_required
def flag():
    g.source.flagged = True
    db_session.commit()
    return render_template('flag.html', filesystem_id=g.filesystem_id,
                           codename=g.source.journalist_designation)


if __name__ == "__main__":  # pragma: no cover
    debug = getattr(config, 'env', 'prod') != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8081)
