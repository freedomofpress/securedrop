# -*- coding: utf-8 -*-

from datetime import datetime
import functools

from flask import (Flask, request, render_template, send_file, redirect, flash,
                   url_for, g, abort, session)
from flask_wtf.csrf import CSRFProtect
from flask_assets import Environment
from jinja2 import Markup
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import false

import config
import version
import crypto_util
from rm import srm
import i18n
from flask_babel import gettext, ngettext
import store
import template_filters
from db import (db_session, Source, Journalist, Submission, Reply,
                SourceStar, get_one_or_else, LoginThrottledException,
                PasswordError, InvalidUsernameException)
import worker

app = Flask(__name__, template_folder=config.JOURNALIST_TEMPLATES_DIR)
app.config.from_object(config.JournalistInterfaceFlaskConfig)
CSRFProtect(app)

i18n.setup_app(app)

assets = Environment(app)

app.jinja_env.globals['version'] = version.__version__
if getattr(config, 'CUSTOM_HEADER_IMAGE', None):
    app.jinja_env.globals['header_image'] = config.CUSTOM_HEADER_IMAGE
    app.jinja_env.globals['use_custom_header_image'] = True
else:
    app.jinja_env.globals['header_image'] = 'logo.png'
    app.jinja_env.globals['use_custom_header_image'] = False

app.jinja_env.filters['datetimeformat'] = template_filters.datetimeformat
app.jinja_env.filters['filesizeformat'] = template_filters.filesizeformat


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Automatically remove database sessions at the end of the request, or
    when the application shuts down"""
    db_session.remove()


def get_source(filesystem_id):
    """Return a Source object, representing the database row, for the source
    with the `filesystem_id`"""
    source = None
    query = Source.query.filter(Source.filesystem_id == filesystem_id)
    source = get_one_or_else(query, app.logger, abort)

    return source


@app.before_request
def setup_g():
    """Store commonly used values in Flask's special g object"""
    uid = session.get('uid', None)
    if uid:
        g.user = Journalist.query.get(uid)

    g.locale = i18n.get_locale()
    g.text_direction = i18n.get_text_direction(g.locale)
    g.locales = i18n.get_locale2name()

    if request.method == 'POST':
        filesystem_id = request.form.get('filesystem_id')
        if filesystem_id:
            g.filesystem_id = filesystem_id
            g.source = get_source(filesystem_id)


def logged_in():
    # When a user is logged in, we push their user ID (database primary key)
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
        flash(gettext("Only administrators can access this page."),
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
            login_flashed_msg = gettext('Login failed.')

            if isinstance(e, LoginThrottledException):
                login_flashed_msg += " "
                login_flashed_msg += gettext(
                    "Please wait at least {seconds} seconds "
                    "before logging in again.").format(
                        seconds=Journalist._LOGIN_ATTEMPT_PERIOD)
            else:
                try:
                    user = Journalist.query.filter_by(
                        username=request.form['username']).one()
                    if user.is_totp:
                        login_flashed_msg += " "
                        login_flashed_msg += gettext(
                            "Please wait for a new two-factor token"
                            " before logging in again.")
                except:
                    pass

            flash(login_flashed_msg, "error")
        else:
            app.logger.info("'{}' logged in with the token {}".format(
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
@admin_required
def admin_add_user():
    if request.method == 'POST':
        form_valid = True
        username = request.form['username']

        password = request.form['password']
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
            except PasswordError:
                flash(gettext(
                    'There was an error with the autogenerated password. '
                    'User not created. Please try again.'), 'error')
                form_valid = False
            except InvalidUsernameException as e:
                form_valid = False
                flash('Invalid username: ' + str(e), "error")
            except IntegrityError as e:
                db_session.rollback()
                form_valid = False
                if "UNIQUE constraint failed: journalists.username" in str(e):
                    flash(gettext("That username is already in use"),
                          "error")
                else:
                    flash(gettext("An error occurred saving this user"
                                  " to the database."
                                  " Please check the application logs."),
                          "error")
                    app.logger.error("Adding user '{}' failed: {}".format(
                        username, e))

        if form_valid:
            return redirect(url_for('admin_new_user_two_factor',
                                    uid=new_user.id))

    return render_template("admin_add_user.html", password=_make_password())


@app.route('/admin/2fa', methods=('GET', 'POST'))
@admin_required
def admin_new_user_two_factor():
    user = Journalist.query.get(request.args['uid'])

    if request.method == 'POST':
        token = request.form['token']
        if user.verify_token(token):
            flash(gettext(
                "Token in two-factor authentication "
                "accepted for user {user}.").format(
                    user=user.username),
                "notification")
            return redirect(url_for("admin_index"))
        else:
            flash(gettext(
                "Could not verify token in two-factor authentication."),
                  "error")

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
        try:
            user.set_hotp_secret(otp_secret)
        except TypeError as e:
            if "Non-hexadecimal digit found" in str(e):
                flash(gettext(
                    "Invalid secret format: "
                    "please only submit letters A-F and numbers 0-9."),
                      "error")
            elif "Odd-length string" in str(e):
                flash(gettext(
                    "Invalid secret format: "
                    "odd-length secret. Did you mistype the secret?"),
                      "error")
            else:
                flash(gettext(
                    "An unexpected error occurred! "
                    "Please check the application "
                    "logs or inform your adminstrator."), "error")
                app.logger.error(
                    "set_hotp_secret '{}' (id {}) failed: {}".format(
                        otp_secret, uid, e))
            return render_template('admin_edit_hotp_secret.html', uid=uid)
        else:
            db_session.commit()
            return redirect(url_for('admin_new_user_two_factor', uid=uid))
    else:
        return render_template('admin_edit_hotp_secret.html', uid=uid)


class PasswordMismatchError(Exception):
    pass


def commit_account_changes(user):
    if db_session.is_modified(user):
        try:
            db_session.add(user)
            db_session.commit()
        except Exception as e:
            flash(gettext(
                "An unexpected error occurred! Please check the application "
                  "logs or inform your adminstrator."), "error")
            app.logger.error("Account changes for '{}' failed: {}".format(user,
                                                                          e))
            db_session.rollback()
        else:
            flash(gettext("Account updated."), "success")


@app.route('/admin/edit/<int:user_id>', methods=('GET', 'POST'))
@admin_required
def admin_edit_user(user_id):
    user = Journalist.query.get(user_id)

    if request.method == 'POST':
        if request.form.get('username', None):
            new_username = request.form['username']

            try:
                Journalist.check_username_acceptable(new_username)
            except InvalidUsernameException as e:
                flash('Invalid username: ' + str(e), 'error')
                return redirect(url_for("admin_edit_user", user_id=user_id))

            if new_username == user.username:
                pass
            elif Journalist.query.filter_by(
                    username=new_username).one_or_none():
                flash(gettext(
                    'Username "{user}" is already taken!').format(
                        user=new_username),
                    "error")
                return redirect(url_for("admin_edit_user", user_id=user_id))
            else:
                user.username = new_username

        user.is_admin = bool(request.form.get('is_admin'))

        commit_account_changes(user)

    password = _make_password()
    return render_template("edit_account.html", user=user,
                           password=password)


@app.route('/admin/edit/<int:user_id>/new-password', methods=('POST',))
@admin_required
def admin_set_diceware_password(user_id):
    try:
        user = Journalist.query.get(user_id)
    except NoResultFound:
        abort(404)

    password = request.form.get('password')
    _set_diceware_password(user, password)
    return redirect(url_for('admin_edit_user', user_id=user_id))


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

    return redirect(url_for('admin_index'))


@app.route('/account', methods=('GET',))
@login_required
def edit_account():
    password = _make_password()
    return render_template('edit_account.html',
                           password=password)


@app.route('/account/new-password', methods=['POST'])
@login_required
def new_password():
    user = g.user
    password = request.form.get('password')
    _set_diceware_password(user, password)
    return redirect(url_for('edit_account'))


@app.route('/admin/edit/<int:user_id>/new-password', methods=('POST',))
@admin_required
def admin_new_password(user_id):
    try:
        user = Journalist.query.get(user_id)
    except NoResultFound:
        abort(404)

    password = request.form.get('password')
    _set_diceware_password(user, password)
    return redirect(url_for('admin_edit_user', user_id=user_id))


def _make_password():
    while True:
        password = crypto_util.genrandomid(7, i18n.get_language())
        try:
            Journalist.check_password_acceptable(password)
            return password
        except PasswordError:
            continue


def _set_diceware_password(user, password):
    try:
        user.set_password(password)
    except PasswordError:
        flash(gettext(
            'You submitted a bad password! Password not changed.'), 'error')
        return

    try:
        db_session.commit()
    except Exception:
        flash(gettext(
            'There was an error, and the new password might not have been '
            'saved correctly. To prevent you from getting locked '
            'out of your account, you should reset your password again.'),
            'error')
        app.logger.error('Failed to update a valid password.')
        return

    # using Markup so the HTML isn't escaped
    flash(Markup("<p>" + gettext(
        "The password was successfully updated! Don't forget to "
        "save it in your KeePassX database. The new password is:") +
        ' <span><code>{}</code></span></p>'.format(password)),
        'success')


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


def make_star_true(filesystem_id):
    source = get_source(filesystem_id)
    if source.star:
        source.star.starred = True
    else:
        source_star = SourceStar(source)
        db_session.add(source_star)


def make_star_false(filesystem_id):
    source = get_source(filesystem_id)
    if not source.star:
        source_star = SourceStar(source)
        db_session.add(source_star)
        db_session.commit()
    source.star.starred = False


@app.route('/col/add_star/<filesystem_id>', methods=('POST',))
@login_required
def add_star(filesystem_id):
    make_star_true(filesystem_id)
    db_session.commit()
    return redirect(url_for('index'))


@app.route("/col/remove_star/<filesystem_id>", methods=('POST',))
@login_required
def remove_star(filesystem_id):
    make_star_false(filesystem_id)
    db_session.commit()
    return redirect(url_for('index'))


@app.route('/')
@login_required
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


@app.route('/col/<filesystem_id>')
@login_required
def col(filesystem_id):
    source = get_source(filesystem_id)
    source.has_key = crypto_util.getkey(filesystem_id)
    return render_template("col.html", filesystem_id=filesystem_id,
                           source=source)


def delete_collection(filesystem_id):
    # Delete the source's collection of submissions
    job = worker.enqueue(srm, store.path(filesystem_id))

    # Delete the source's reply keypair
    crypto_util.delete_reply_keypair(filesystem_id)

    # Delete their entry in the db
    source = get_source(filesystem_id)
    db_session.delete(source)
    db_session.commit()
    return job


@app.route('/col/process', methods=('POST',))
@login_required
def col_process():
    actions = {'download-unread': col_download_unread,
               'download-all': col_download_all, 'star': col_star,
               'un-star': col_un_star, 'delete': col_delete}
    if 'cols_selected' not in request.form:
        flash(gettext('No collections selected!'), 'error')
        return redirect(url_for('index'))

    # getlist is cgi.FieldStorage.getlist
    cols_selected = request.form.getlist('cols_selected')
    action = request.form['action']

    if action not in actions:
        return abort(500)

    method = actions[action]
    return method(cols_selected)


def col_download_unread(cols_selected):
    """Download all unread submissions from all selected sources."""
    submissions = []
    for filesystem_id in cols_selected:
        id = Source.query.filter(Source.filesystem_id == filesystem_id) \
                   .one().id
        submissions += Submission.query.filter(
            Submission.downloaded == false(),
            Submission.source_id == id).all()
    if submissions == []:
        flash(gettext("No unread submissions in selected collections."),
              "error")
        return redirect(url_for('index'))
    return download("unread", submissions)


def col_download_all(cols_selected):
    """Download all submissions from all selected sources."""
    submissions = []
    for filesystem_id in cols_selected:
        id = Source.query.filter(Source.filesystem_id == filesystem_id) \
                   .one().id
        submissions += Submission.query.filter(
            Submission.source_id == id).all()
    return download("all", submissions)


def col_star(cols_selected):
    for filesystem_id in cols_selected:
        make_star_true(filesystem_id)

    db_session.commit()
    return redirect(url_for('index'))


def col_un_star(cols_selected):
    for filesystem_id in cols_selected:
        make_star_false(filesystem_id)

    db_session.commit()
    return redirect(url_for('index'))


@app.route('/col/delete/<filesystem_id>', methods=('POST',))
@login_required
def col_delete_single(filesystem_id):
    """deleting a single collection from its /col page"""
    source = get_source(filesystem_id)
    delete_collection(filesystem_id)
    flash(gettext("{source_journalist_designation}'s collection deleted")
          .format(source_journalist_designation=source.journalist_designation),
          "notification")
    return redirect(url_for('index'))


def col_delete(cols_selected):
    """deleting multiple collections from the index"""
    if len(cols_selected) < 1:
        flash(gettext("No collections selected for deletion."), "error")
    else:
        for filesystem_id in cols_selected:
            delete_collection(filesystem_id)
        num = len(cols_selected)
        flash(ngettext('{num} collection deleted', '{num} collections deleted',
                       num).format(num=num),
              "notification")

    return redirect(url_for('index'))


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
    msg = request.form['msg']
    # Reject empty replies
    if not msg:
        flash(gettext("You cannot send an empty reply!"), "error")
        return redirect(url_for('col', filesystem_id=g.filesystem_id))

    g.source.interaction_count += 1
    filename = "{0}-{1}-reply.gpg".format(g.source.interaction_count,
                                          g.source.journalist_filename)
    crypto_util.encrypt(msg,
                        [crypto_util.getkey(g.filesystem_id),
                         config.JOURNALIST_KEY],
                        output=store.path(g.filesystem_id, filename))
    reply = Reply(g.user, g.source, filename)

    try:
        db_session.add(reply)
        db_session.commit()
    except Exception as exc:
        flash(gettext(
            "An unexpected error occurred! Please check the application "
            "logs or inform your adminstrator."), "error")
        # We take a cautious approach to logging here because we're dealing
        # with responses to sources. It's possible the exception message could
        # contain information we don't want to write to disk.
        app.logger.error(
            "Reply from '{}' (id {}) failed: {}!".format(g.user.username,
                                                         g.user.id,
                                                         exc.__class__))
    else:
        flash(gettext("Thanks! Your reply has been stored."),
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
        "The source '{original_source}' has been"
        " renamed to '{new_source}'")
          .format(original_source=original_journalist_designation,
                  new_source=g.source.journalist_designation),
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
        flash(gettext("No unread submissions for this source!"))
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
            flash(gettext("No collections selected for download!"), "error")
        elif action in ('delete', 'confirm_delete'):
            flash(gettext("No collections selected for deletion!"), "error")
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


def confirm_bulk_delete(filesystem_id, items_selected):
    return render_template('delete.html',
                           filesystem_id=filesystem_id,
                           source=g.source,
                           items_selected=items_selected)


def bulk_delete(filesystem_id, items_selected):
    for item in items_selected:
        item_path = store.path(filesystem_id, item.filename)
        worker.enqueue(srm, item_path)
        db_session.delete(item)
    db_session.commit()

    flash(ngettext("Submission deleted.",
                   "Submissions deleted.",
                   len(items_selected)), "notification")
    return redirect(url_for('col', filesystem_id=filesystem_id))


def download(zip_basename, submissions):
    """Send client contents of ZIP-file *zip_basename*-<timestamp>.zip
    containing *submissions*. The ZIP-file, being a
    :class:`tempfile.NamedTemporaryFile`, is stored on disk only
    temporarily.

    :param str zip_basename: The basename of the ZIP-file download.

    :param list submissions: A list of :class:`db.Submission`s to
                             include in the ZIP-file.
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
@login_required
def flag():
    g.source.flagged = True
    db_session.commit()
    return render_template('flag.html', filesystem_id=g.filesystem_id,
                           codename=g.source.journalist_designation)


if __name__ == "__main__":  # pragma: no cover
    debug = getattr(config, 'env', 'prod') != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8081)
