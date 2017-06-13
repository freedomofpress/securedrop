# -*- coding: utf-8 -*-

import os
from datetime import datetime
import functools

from flask import (Flask, request, render_template, send_file, redirect, flash,
                   url_for, g, abort, session)
from flask_wtf.csrf import CSRFProtect
from flask_assets import Environment
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.exc import IntegrityError
from werkzeug.routing import BaseConverter

import config
import version
import crypto_util
import store
import template_filters
from db import (db_session, Source, Journalist, Submission, Reply,
                SourceStar, get_one_or_else, NoResultFound,
                WrongPasswordException,
                LoginThrottledException, InvalidPasswordLength)
import worker

app = Flask(__name__, template_folder=config.JOURNALIST_TEMPLATES_DIR)
app.config.from_object(config.JournalistInterfaceFlaskConfig)
CSRFProtect(app)

assets = Environment(app)

app.jinja_env.globals['version'] = version.__version__
if getattr(config, 'CUSTOM_HEADER_IMAGE', None):
    app.jinja_env.globals['header_image'] = config.CUSTOM_HEADER_IMAGE
    app.jinja_env.globals['use_custom_header_image'] = True
else:
    app.jinja_env.globals['header_image'] = 'logo.png'
    app.jinja_env.globals['use_custom_header_image'] = False

app.jinja_env.filters['datetimeformat'] = template_filters.datetimeformat

class SidLookupConverter(BaseConverter):
    """A URL converter used for converting between Source filesystem
    identifier strings and corresponding Source objects.
    """
    def to_python(self, sid):
        return Source.query.filter(Source.filesystem_id == sid).one_or_none()

    def to_url(self, source):
        return source.filesystem_id

app.url_map.converters['sid'] = SidLookupConverter


def ensure_source_exists(func):
    """A wrapper to be placed above routes that use the
    :class:`SidLookupConverter`, this function provides user-friendly error
    handling of POST requests involving a single Source that no longer
    exists.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not kwargs.get('source'):
            flash('The source you were trying to reply to no longer '
                  'exists!', 'error')
            return redirect(url_for('index'))
        else:
            return func(*args, **kwargs)
    return wrapper


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Automatically remove database sessions at the end of the request, or
    when the application shuts down"""
    db_session.remove()


@app.before_request
def pre_process_request():
    """The first function run on all incoming requests to the Journalist
    Interface application.
 
    First, the authentication and privilege status of the client are
    checked. If they are trying to access a page they are not authorized
    to access, the request is immediately redirected to either the login
    page (for unauthenticated clients), or the index page (for
    authenticated clients trying to access admin pages they are not
    permitted to).

    Next, for POST requests containing `sid` strings coming from
    authnenticate users, we attempt to find the corresponding Source and
    store some commonly-used values in the thread-local g object for our
    later convenience in the next function(s) that will be called on the
    request. When such a corresponding Source object cannot be found, we
    redirect users to the index page, and flash an appropriate message.

    Returns:
        flask.Response: a redirect to the login page when an
            unauthenticated user makes a request besides to login; a
            redirect to the index page when an authenticated, but
            non-admin user requests an admin page; and a redirect to the
            home page when a user makes a POST request including a 'sid'
            string with no corresponding Source. If none of these cases
            apply to the request, this function does not return a
            response and instead execution of the next function in the
            request processing process begins.
    """
    # Only set g.user if the client provides a valid primary key corresponding
    # to a currently-existing Journalist object in their server-signed session.
    user = Journalist.query.get(session.get('uid', -1))
    if user:
        g.user = user

    # Instead of blacklisting URLs which only authenticated users can access,
    # we take a more cautious whitelisting approach. Authentication
    # verification is performed before doing any processing of request
    # parameters (such as form data) to prevent leaking information (e.g.,
    # timing leaks of lookups of Source objects by "sid" strings such as is
    # done by the :class:`SidLookupConverter` URL converter).
    rule = request.url_rule.rule
    if rule != '/login':
        if not hasattr(g, 'user'):
            flash("You must be logged in to access that page!",
                  "notification")
            return redirect(url_for('login'))
    if rule.startswith('/admin'):
        if not hasattr(g, 'user') or not g.user.is_admin:
            flash("You must be an administrator to access that page!",
                  "notification")
            return redirect(url_for('index'))

    if request.method == 'POST':
        # We must first ensure the client is authenticated before it's safe to
        # perform database lookups using input they've provided (note that
        # absent the `hasattr` check below, a user could make a malformed
        # POST request to the login page that contains a 'sid' string in the
        # form data).
        if hasattr(g, 'user'):
            sid = request.form.get('sid')
            if sid:
                try:
                    query = Source.query.filter(Source.filesystem_id == sid)
                    source = query.one()
                except NoResultFound:
                    flash('Sorry, this source no longer exists!', 'error')
                    return redirect(url_for('index'))
                else:
                    g.sid = sid
                    g.source = source


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
                login_flashed_msg += " Please wait at least 60 seconds before logging in again."
            else:
                try:
                    user = Journalist.query.filter_by(
                        username=request.form['username']).one()
                    if user.is_totp:
                        login_flashed_msg += " Please wait for a new two-factor token before logging in again."
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
            except InvalidPasswordLength:
                form_valid = False
                flash("Your password must be between {} and {} characters.".format(
                        Journalist.MIN_PASSWORD_LEN, Journalist.MAX_PASSWORD_LEN
                    ), "error")
            except IntegrityError as e:
                db_session.rollback()
                form_valid = False
                if "UNIQUE constraint failed: journalists.username" in str(e):
                    flash("That username is already in use",
                          "error")
                else:
                    flash("An error occurred saving this user to the database",
                          "error")

        if form_valid:
            return redirect(url_for('admin_new_user_two_factor',
                                    uid=new_user.id))

    return render_template("admin_add_user.html")


@app.route('/admin/2fa', methods=('GET', 'POST'))
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
def admin_reset_two_factor_totp():
    uid = request.form['uid']
    user = Journalist.query.get(uid)
    user.is_totp = True
    user.regenerate_totp_shared_secret()
    db_session.commit()
    return redirect(url_for('admin_new_user_two_factor', uid=uid))


@app.route('/admin/reset-2fa-hotp', methods=['POST'])
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


class PasswordMismatchError(Exception):
    pass


def edit_account_password(user, password, password_again):
    if password:
        if password != password_again:
            flash("Passwords didn't match!", "error")
            raise PasswordMismatchError
        try:
            user.set_password(password)
        except InvalidPasswordLength:
            flash("Your password must be between {} and {} characters.".format(
                    Journalist.MIN_PASSWORD_LEN, Journalist.MAX_PASSWORD_LEN
                ), "error")
            raise


def commit_account_changes(user):
    if db_session.is_modified(user):
        try:
            db_session.add(user)
            db_session.commit()
        except Exception as e:
            flash("An unexpected error occurred! Please check the application "
                  "logs or inform your adminstrator.", "error")
            app.logger.error("Account changes for '{}' failed: {}".format(user,
                                                                          e))
            db_session.rollback()
        else:
            flash("Account successfully updated!", "success")


@app.route('/admin/edit/<int:user_id>', methods=('GET', 'POST'))
def admin_edit_user(user_id):
    user = Journalist.query.get(user_id)

    if request.method == 'POST':
        if request.form['username']:
            new_username = request.form['username']
            if new_username == user.username:
                pass
            elif Journalist.query.filter_by(
                username=new_username).one_or_none():
                flash('Username "{}" is already taken!'.format(new_username),
                      "error")
                return redirect(url_for("admin_edit_user", user_id=user_id))
            else:
                user.username = new_username

        try:
            edit_account_password(user, request.form['password'],
                                  request.form['password_again'])
        except (PasswordMismatchError, InvalidPasswordLength):
            return redirect(url_for("admin_edit_user", user_id=user_id))

        user.is_admin = bool(request.form.get('is_admin'))

        commit_account_changes(user)

    return render_template("edit_account.html", user=user)


@app.route('/admin/delete/<int:user_id>', methods=('POST',))
def admin_delete_user(user_id):
    user = Journalist.query.get(user_id)
    if user:
        db_session.delete(user)
        db_session.commit()
        flash("Deleted user '{}'".format(user.username), "notification")
        return redirect(url_for('admin_index'))
    else:
        app.logger.error(
            "Admin {} tried to delete nonexistent user with pk={}".format(
            g.user.username, user_id))
        abort(404)


@app.route('/account', methods=('GET', 'POST'))
def edit_account():
    user = g.user

    if request.method == 'POST':
        try:
            edit_account_password(user, request.form['password'],
                                  request.form['password_again'])
        except (PasswordMismatchError, InvalidPasswordLength):
            return redirect(url_for('edit_account'))

        commit_account_changes(user)

    return render_template('edit_account.html')


@app.route('/account/2fa', methods=('GET', 'POST'))
def account_new_two_factor():
    user = g.user

    if request.method == 'POST':
        token = request.form['token']
        if user.verify_token(token):
            flash(
                "Two factor token successfully verified!",
                "notification")
            return redirect(url_for('edit_account'))
        else:
            flash("Two factor token failed to verify", "error")

    return render_template('account_new_two_factor.html', user=user)


@app.route('/account/reset-2fa-totp', methods=['POST'])
def account_reset_two_factor_totp():
    user = g.user
    user.is_totp = True
    user.regenerate_totp_shared_secret()
    db_session.commit()
    return redirect(url_for('account_new_two_factor'))


@app.route('/account/reset-2fa-hotp', methods=['POST'])
def account_reset_two_factor_hotp():
    user = g.user
    otp_secret = request.form.get('otp_secret', None)
    if otp_secret:
        user.set_hotp_secret(otp_secret)
        db_session.commit()
        return redirect(url_for('account_new_two_factor'))
    else:
        return render_template('account_edit_hotp_secret.html')


def make_star_true(source):
    if source.star:
        source.star.starred = True
    else:
        source_star = SourceStar(source)
        db_session.add(source_star)


def make_star_false(source):
    if not source.star:
        source_star = SourceStar(source)
        db_session.add(source_star)
        db_session.commit()
    source.star.starred = False


@app.route('/col/add_star/<sid:source>', methods=('POST',))
@ensure_source_exists
def add_star(source):
    make_star_true(source)
    db_session.commit()
    return redirect(url_for('index'))


@app.route("/col/remove_star/<sid:source>", methods=('POST',))
@ensure_source_exists
def remove_star(source):
    make_star_false(source)
    db_session.commit()
    return redirect(url_for('index'))


@app.route('/')
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

    return render_template('index.html', unstarred=unstarred, starred=starred)


@app.route('/col/<sid:source>')
@ensure_source_exists
def col(source):
    source.has_key = crypto_util.getkey(source.filesystem_id)
    return render_template("col.html", sid=source.filesystem_id, source=source)


def delete_collection(source):
    # Delete the source's collection of submissions
    job = worker.enqueue(store.delete_source_directory, source.filesystem_id)
    # Delete the source's reply keypair
    crypto_util.delete_reply_keypair(source.filesystem_id)
    # Delete their entry in the db
    db_session.delete(source)
    db_session.commit()
    return job


@app.route('/col/process', methods=('POST',))
def col_process():
    """Perform actions on multiple Source collections simultaneously:
    download unread, download all, star, un-star, and delete.

    Returns:
        flask.Response: returns a redirect to the homepage and flashes
            an appropriate error message if the request either did not
            specify any sources, or if any of the selected Sources no
            longer exist. Returns a 500 error if the action form field
            is invalid (indicates a malformed request). Returns the
            response from the subroutine indicated by the `action` form
            data field if none of the errors above are encountered
            during earlier processing of the request.
    """
    cols_selected = request.form.getlist('cols_selected')
    if not cols_selected:
        flash('No sources selected!', 'error')
        return redirect(url_for('index'))
    else:
        try:
            sources = [Source.query.filter(Source.filesystem_id == sid).one()
                       for sid in cols_selected]
        except NoResultFound:
            flash('Sorry, one or more of the selected sources no longer '
                  'exists!', 'error')
            return redirect(url_for('index'))

    actions = {'download-unread': col_download_unread,
               'download-all': col_download_all,
               'star': col_star,
               'un-star': col_un_star,
               'delete': col_delete}

    try:
        return actions[request.form['action']](sources)
    except KeyError:
        return abort(400)


def col_download_unread(sources):
    """Downloads all unread submissions from all selected sources.
    """
    submissions = []
    for source in sources:
        submissions += Submission.query \
                .filter(Submission.downloaded == False,
                        Submission.source_id == source.id) \
                .all()
    if not submissions:
        flash("No unread submissions in collections selected!", "error")
        return redirect(url_for('index'))
    else:
        return download("unread", submissions)


def col_download_all(sources):
    """Downloads all submissions from all selected sources.
    """
    submissions = []
    for source in sources:
        submissions += Submission.query \
                .filter(Submission.source_id == source.id) \
                .all()
    return download("all", submissions)


def col_star(sources):
    for source in sources:
        make_star_true(source)
    db_session.commit()
    return redirect(url_for('index'))


def col_un_star(sources):
    for source in sources:
        make_star_false(source)
    db_session.commit()
    return redirect(url_for('index'))


def col_delete(sources):
    """Deletes multiple Source collections from the index.
    """
    for source in sources:
        delete_collection(source)
    num_sources = len(sources)
    flash('{} source collection{} deleted!'.format(
        num_sources, '' if num_sources == 1 else 's'),
        'notification')
    return redirect(url_for('index'))


@app.route('/col/delete/<sid:source>', methods=('POST',))
@ensure_source_exists
def col_delete_single(source):
    """deleting a single collection from its /col page"""
    delete_collection(source)
    flash(
        "%s's collection deleted" %
        (source.journalist_designation,), "notification")
    return redirect(url_for('index'))


@app.route('/col/<sid:source>/<fn>')
@ensure_source_exists
def download_single_submission(source, fn):
    """Sends a client the contents of a single submission."""
    if '..' in fn or fn.startswith('/'):
        abort(404)

    try:
        Submission.query.filter(
            Submission.filename == fn).one().downloaded = True
        db_session.commit()
    except NoResultFound as e:
        app.logger.error("Could not mark " + fn + " as downloaded: %s" % (e,))

    return send_file(store.path(source.filesystem_id, fn),
                     mimetype="application/pgp-encrypted")


@app.route('/reply', methods=('POST',))
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
    msg = request.form['msg']
    # Reject empty replies
    if not msg:
        flash("You cannot send an empty reply!", "error")
        return redirect(url_for('col', source=g.source))

    g.source.interaction_count += 1
    filename = "{0}-{1}-reply.gpg".format(g.source.interaction_count,
                                          g.source.journalist_filename)
    crypto_util.encrypt(msg,
                        [crypto_util.getkey(g.sid), config.JOURNALIST_KEY],
                        output=store.path(g.sid, filename))
    reply = Reply(g.user, g.source, filename)

    try:
        db_session.add(reply)
        db_session.commit()
    except Exception as exc:
        flash("An unexpected error occurred! Please check the application "
              "logs or inform your adminstrator.", "error")
        # We take a cautious approach to logging here because we're dealing
        # with responses to sources. It's possible the exception message could
        # contain information we don't want to write to disk.
        app.logger.error(
            "Reply from '{}' (id {}) failed: {}!".format(g.user.username,
                                                         g.user.id,
                                                         exc.__class__))
    else:
        flash("Thanks! Your reply has been stored.", "notification")
    finally:
        return redirect(url_for('col', source=g.source))


@app.route('/regenerate-code', methods=('POST',))
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


@app.route('/download_unread/<sid:source>')
@ensure_source_exists
def download_unread_sid(source):
    submissions = Submission.query.filter(Submission.source_id == source.id,
                                          Submission.downloaded == False).all()
    if not submissions:
        flash("No unread submissions for this source!")
        return redirect(url_for('col', source=source))
    else:
        return download(source.journalist_filename, submissions)


@app.route('/bulk', methods=('POST',))
def bulk():
    action = request.form['action']

    doc_names_selected = request.form.getlist('doc_names_selected')
    selected_docs = [doc for doc in g.source.collection
                     if doc.filename in doc_names_selected]
    if selected_docs == []:
        if action == 'download':
            flash("No collections selected to download!", "error")
        elif action in ('delete', 'confirm_delete'):
            flash("No collections selected to delete!", "error")
        return redirect(url_for('col', source=g.source))

    if action == 'download':
        return download(g.source.journalist_filename, selected_docs)
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
    return redirect(url_for('col', source=source))


def download(zip_basename, submissions):
    """Send client contents of zipfile *zip_basename*-<timestamp>.zip
    containing *submissions*. The zipfile, being a
    :class:`tempfile.NamedTemporaryFile`, is stored on disk only
    temporarily.

    :param str zip_basename: The basename of the zipfile download.

    :param list submissions: A list of :class:`db.Submission`s to
                             include in the zipfile.
    """
    zf = store.get_bulk_archive(submissions,
                                zip_directory=zip_basename)
    attachment_filename = "{}--{}.zip".format(
        zip_basename, datetime.utcnow().strftime("%Y-%m-%d--%H-%M-%S"))

    # Mark the submissions that have been downloaded as such
    for submission in submissions:
        submission.downloaded = True
    db_session.commit()

    return send_file(zf.name, mimetype="application/zip",
                     attachment_filename=attachment_filename,
                     as_attachment=True)


@app.route('/flag', methods=('POST',))
def flag():
    g.source.flagged = True
    db_session.commit()
    return render_template('flag.html', source=g.source,
                           codename=g.source.journalist_designation)


def write_pidfile():
    pid = str(os.getpid())
    with open(config.JOURNALIST_PIDFILE, 'w') as fp:
        fp.write(pid)


if __name__ == "__main__":  # pragma: no cover
    write_pidfile()
    debug = getattr(config, 'env', 'prod') != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8081)
