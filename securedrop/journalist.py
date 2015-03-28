# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime
import functools

from flask import (Flask, request, render_template, send_file, redirect, flash,
                   url_for, g, abort, session)
from flask_wtf.csrf import CsrfProtect
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.exc import IntegrityError

import config
import version
import crypto_util
import store
import template_filters
from db import (db_session, Source, Journalist, Submission, Reply,
                SourceStar, get_one_or_else, NoResultFound,
                WrongPasswordException, BadTokenException,
                LoginThrottledException)
import worker

app = Flask(__name__, template_folder=config.JOURNALIST_TEMPLATES_DIR)
app.config.from_object(config.JournalistInterfaceFlaskConfig)
CsrfProtect(app)

app.jinja_env.globals['version'] = version.__version__
if getattr(config, 'CUSTOM_HEADER_IMAGE', None):
    app.jinja_env.globals['header_image'] = config.CUSTOM_HEADER_IMAGE
    app.jinja_env.globals['use_custom_header_image'] = True
else:
    app.jinja_env.globals['header_image'] = 'logo.png'
    app.jinja_env.globals['use_custom_header_image'] = False

app.jinja_env.filters['datetimeformat'] = template_filters.datetimeformat


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Automatically remove database sessions at the end of the request, or
    when the application shuts down"""
    db_session.remove()


def get_source(sid):
    """Return a Source object, representing the database row, for the source
    with id `sid`"""
    source = None
    query = Source.query.filter(Source.filesystem_id == sid)
    source = get_one_or_else(query, app.logger, abort)

    return source


@app.before_request
def setup_g():
    """Store commonly used values in Flask's special g object"""
    uid = session.get('uid', None)
    if uid:
        g.user = Journalist.query.get(uid)

    if request.method == 'POST':
        sid = request.form.get('sid')
        if sid:
            g.sid = sid
            g.source = get_source(sid)


def logged_in():
    # When a user is logged in, we push their user id (database primary key)
    # into the session. setup_g checks for this value, and if it finds it,
    # stores a reference to the user's Journalist object in g.
    #
    # This check is good for the edge case where a user is deleted but still
    # has an active session - we will not authenticate a user if they are not
    # in the database.
    return bool(g.get('user', None))


def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not logged_in():
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if logged_in() and g.user.is_admin:
            return func(*args, **kwargs)
        # TODO: sometimes this gets flashed 2x (Chrome only?)
        flash("You must be an administrator to access that page",
              "notification")
        return redirect(url_for('index'))
    return wrapper


@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        try:
            user = Journalist.login(request.form['username'],
                                    request.form['password'],
                                    request.form['token'])
        except Exception as e:
            app.logger.error("Login for '{}' failed: {}".format(
                request.form['username'], e))
            login_flashed_msg = "Login failed."

            if isinstance(e, LoginThrottledException):
                login_flashed_msg += (" Please wait at least 60 seconds "
                                      "before logging in again.")
            else:
                try:
                    user = Journalist.query.filter_by(
                        username=request.form['username']).one()
                    if user.is_totp:
                        login_flashed_msg += (" Please wait for a new "
                                              "two-factor token before "
                                              "logging in again.")
                except:
                    pass

            flash(login_flashed_msg, "error")
        else:
            app.logger.info("Successful login for '{}' with token {}".format(
                request.form['username'], request.form['token']))

            # Update access metadata
            user.last_access = datetime.utcnow()
            db_session.add(user)
            db_session.commit()

            session['uid'] = user.id
            return redirect(url_for('index'))

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop('uid', None)
    return redirect(url_for('index'))


@app.route('/admin', methods=('GET', 'POST'))
@admin_required
def admin_index():
    users = Journalist.query.all()
    return render_template("admin.html", users=users)


@app.route('/admin/add', methods=('GET', 'POST'))
def admin_add_user():
    if request.method == 'POST':
        form_valid = True

        username = request.form['username']
        if len(username) == 0:
            form_valid = False
            flash("Missing username", "error")

        password = request.form['password']
        password_again = request.form['password_again']
        if password != password_again:
            form_valid = False
            flash("Passwords didn't match", "error")

        is_admin = bool(request.form.get('is_admin'))

        if form_valid:
            try:
                otp_secret = None
                if request.form.get('is_hotp', False):
                    otp_secret = request.form.get('otp_secret', '')
                new_user = Journalist(username=username,
                                      password=password,
                                      is_admin=is_admin,
                                      otp_secret=otp_secret)
                db_session.add(new_user)
                db_session.commit()
            except IntegrityError as e:
                form_valid = False
                if "username is not unique" in str(e):
                    flash("That username is already in use",
                          "error")
                else:
                    flash(("An error occurred saving this "
                           "user to the database"),
                          "error")

        if form_valid:
            return redirect(url_for('admin_new_user_two_factor',
                                    uid=new_user.id))

    return render_template("admin_add_user.html")


@app.route('/admin/2fa', methods=('GET', 'POST'))
@admin_required
def admin_new_user_two_factor():
    user = Journalist.query.get(request.args['uid'])

    if request.method == 'POST':
        token = request.form['token']
        if user.verify_token(token):
            flash(
                "Two factor token successfully verified for user {}!".format(
                    user.username),
                "notification")
            return redirect(url_for("admin_index"))
        else:
            flash("Two factor token failed to verify", "error")

    return render_template("admin_new_user_two_factor.html", user=user)


@app.route('/admin/reset-2fa-totp', methods=['POST'])
@admin_required
def admin_reset_two_factor_totp():
    uid = request.form['uid']
    user = Journalist.query.get(uid)
    user.is_totp = True
    user.regenerate_totp_shared_secret()
    db_session.commit()
    return redirect(url_for('admin_new_user_two_factor', uid=uid))


@app.route('/admin/reset-2fa-hotp', methods=['POST'])
@admin_required
def admin_reset_two_factor_hotp():
    uid = request.form['uid']
    otp_secret = request.form.get('otp_secret', None)
    if otp_secret:
        user = Journalist.query.get(uid)
        user.set_hotp_secret(otp_secret)
        db_session.commit()
        return redirect(url_for('admin_new_user_two_factor', uid=uid))
    else:
        return render_template('admin_edit_hotp_secret.html', uid=uid)


@app.route('/admin/edit/<int:user_id>', methods=('GET', 'POST'))
@admin_required
def admin_edit_user(user_id):
    user = Journalist.query.get(user_id)

    if request.method == 'POST':
        if request.form['username'] != "":
            user.username = request.form['username']

        if request.form['password'] != "":
            if request.form['password'] != request.form['password_again']:
                flash("Passwords didn't match", "error")
                return redirect(url_for("admin_edit_user", user_id=user_id))
            user.set_password(request.form['password'])

        user.is_admin = bool(request.form.get('is_admin'))

        try:
            db_session.add(user)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            if "username is not unique" in str(e):
                flash("That username is already in use", "notification")
            else:
                flash(
                    ("An unknown error occurred, please inform "
                     "your administrator"),
                    "error")

    return render_template("admin_edit_user.html", user=user)


@app.route('/admin/delete/<int:user_id>', methods=('POST',))
@admin_required
def admin_delete_user(user_id):
    user = Journalist.query.get(user_id)
    db_session.delete(user)
    db_session.commit()
    return redirect(url_for('admin_index'))


def make_star_true(sid):
    source = get_source(sid)
    if source.star:
        source.star.starred = True
    else:
        source_star = SourceStar(source)
        db_session.add(source_star)


def make_star_false(sid):
    source = get_source(sid)
    if not source.star:
        source_star = SourceStar(source)
        db_session.add(source_star)
        db_session.commit()
    source.star.starred = False


@app.route('/col/add_star/<sid>', methods=('POST',))
@login_required
def add_star(sid):
    make_star_true(sid)
    db_session.commit()
    return redirect(url_for('index'))


@app.route("/col/remove_star/<sid>", methods=('POST',))
@login_required
def remove_star(sid):
    make_star_false(sid)
    db_session.commit()
    return redirect(url_for('index'))


@app.route('/')
@login_required
def index():
    unstarred = []
    starred = []
    for source in Source.query.filter_by(
            pending=False).order_by(
            Source.last_updated.desc()).all():
        star = SourceStar.query.filter(
            SourceStar.source_id == source.id).first()
        if star and star.starred:
            starred.append(source)
        else:
            unstarred.append(source)
        source.num_unread = len(
            Submission.query.filter(
                Submission.source_id == source.id,
                Submission.downloaded is False).all())

    return render_template('index.html', unstarred=unstarred, starred=starred)


@app.route('/col/<sid>')
@login_required
def col(sid):
    source = get_source(sid)
    source.has_key = crypto_util.getkey(sid)
    return render_template("col.html", sid=sid, source=source)


def delete_collection(source_id):
    # Delete the source's collection of submissions
    worker.enqueue(store.delete_source_directory, source_id)

    # Delete the source's reply keypair
    crypto_util.delete_reply_keypair(source_id)

    # Delete their entry in the db
    source = get_source(source_id)
    db_session.delete(source)
    db_session.commit()


@app.route('/col/process', methods=('POST',))
@login_required
def col_process():
    actions = {'delete': col_delete, 'star': col_star, 'un-star': col_un_star}
    if 'cols_selected' not in request.form:
        return redirect(url_for('index'))

    # getlist is cgi.FieldStorage.getlist
    cols_selected = request.form.getlist('cols_selected')
    action = request.form['action']

    if action not in actions:
        return abort(500)

    method = actions[action]
    return method(cols_selected)


def col_star(cols_selected):
    for sid in cols_selected:
        make_star_true(sid)

    db_session.commit()
    return redirect(url_for('index'))


def col_un_star(cols_selected):
    for source_id in cols_selected:
        make_star_false(source_id)

    db_session.commit()
    return redirect(url_for('index'))


@app.route('/col/delete/<sid>', methods=('POST',))
@login_required
def col_delete_single(sid):
    """deleting a single collection from its /col page"""
    source = get_source(sid)
    delete_collection(sid)
    flash(
        "%s's collection deleted" %
        (source.journalist_designation,), "notification")
    return redirect(url_for('index'))


def col_delete(cols_selected):
    """deleting multiple collections from the index"""
    if len(cols_selected) < 1:
        flash("No collections selected to delete!", "error")
    else:
        for source_id in cols_selected:
            delete_collection(source_id)
        flash("%s %s deleted" % (
            len(cols_selected),
            "collection" if len(cols_selected) == 1 else "collections"
        ), "notification")

    return redirect(url_for('index'))


@app.route('/col/<sid>/<fn>')
@login_required
def doc(sid, fn):
    if '..' in fn or fn.startswith('/'):
        abort(404)
    try:
        Submission.query.filter(
            Submission.filename == fn).one().downloaded = True
    except NoResultFound as e:
        app.logger.error("Could not mark " + fn + " as downloaded: %s" % (e,))
    db_session.commit()
    return send_file(store.path(sid, fn), mimetype="application/pgp-encrypted")


@app.route('/reply', methods=('POST',))
@login_required
def reply():
    g.source.interaction_count += 1
    filename = "{0}-{1}-reply.gpg".format(g.source.interaction_count,
                                          g.source.journalist_filename)
    crypto_util.encrypt(request.form['msg'],
                        [crypto_util.getkey(g.sid), config.JOURNALIST_KEY],
                        output=store.path(g.sid, filename))
    reply = Reply(g.user, g.source, filename)
    db_session.add(reply)
    db_session.commit()

    flash("Thanks! Your reply has been stored.", "notification")
    return redirect(url_for('col', sid=g.sid))


@app.route('/regenerate-code', methods=('POST',))
@login_required
def generate_code():
    original_journalist_designation = g.source.journalist_designation
    g.source.journalist_designation = crypto_util.display_id()

    for item in g.source.collection:
        item.filename = store.rename_submission(
            g.sid,
            item.filename,
            g.source.journalist_filename)
    db_session.commit()

    flash(
        "The source '%s' has been renamed to '%s'" %
        (original_journalist_designation,
         g.source.journalist_designation),
        "notification")
    return redirect('/col/' + g.sid)


@app.route('/download_unread/<sid>')
@login_required
def download_unread(sid):
    id = Source.query.filter(Source.filesystem_id == sid).one().id
    docs = Submission.query.filter(
        Submission.source_id == id,
        Submission.downloaded is False).all()
    return bulk_download(sid, docs)


@app.route('/bulk', methods=('POST',))
@login_required
def bulk():
    action = request.form['action']

    doc_names_selected = request.form.getlist('doc_names_selected')
    selected_docs = [doc for doc in g.source.collection
                     if doc.filename in doc_names_selected]

    if selected_docs == []:
        if action == 'download':
            flash("No collections selected to download!", "error")
        elif action == 'delete' or action == 'confirm_delete':
            flash("No collections selected to delete!", "error")
        return redirect(url_for('col', sid=g.sid))

    if action == 'download':
        return bulk_download(g.sid, selected_docs)
    elif action == 'delete':
        return bulk_delete(g.sid, selected_docs)
    elif action == 'confirm_delete':
        return confirm_bulk_delete(g.sid, selected_docs)
    else:
        abort(400)


def confirm_bulk_delete(sid, items_selected):
    return render_template('delete.html',
                           sid=sid,
                           source=g.source,
                           items_selected=items_selected)


def bulk_delete(sid, items_selected):
    for item in items_selected:
        item_path = store.path(sid, item.filename)
        worker.enqueue(store.secure_unlink, item_path)
        db_session.delete(item)
    db_session.commit()

    flash(
        "Submission{} deleted.".format(
            "s" if len(items_selected) > 1 else ""),
        "notification")
    return redirect(url_for('col', sid=sid))


def bulk_download(sid, items_selected):
    source = get_source(sid)
    filenames = [store.path(sid, item.filename) for item in items_selected]

    # Mark the submissions that are about to be downloaded as such
    for item in items_selected:
        if isinstance(item, Submission):
            item.downloaded = True
    db_session.commit()

    zf = store.get_bulk_archive(
        filenames,
        zip_directory=source.journalist_filename)
    attachment_filename = "{}--{}.zip".format(
        source.journalist_filename,
        datetime.utcnow().strftime("%Y-%m-%d--%H-%M-%S"))
    return send_file(zf.name, mimetype="application/zip",
                     attachment_filename=attachment_filename,
                     as_attachment=True)


@app.route('/flag', methods=('POST',))
@login_required
def flag():
    g.source.flagged = True
    db_session.commit()
    return render_template('flag.html', sid=g.sid,
                           codename=g.source.journalist_designation)


def write_pidfile():
    pid = str(os.getpid())
    with open(config.JOURNALIST_PIDFILE, 'w') as fp:
        fp.write(pid)


if __name__ == "__main__":
    write_pidfile()
    # TODO make sure debug=False in production
    app.run(debug=True, host='0.0.0.0', port=8081)
