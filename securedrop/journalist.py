# -*- coding: utf-8 -*-
import os
from datetime import datetime
from functools import wraps

from flask import (Flask, request, render_template, send_file, redirect, flash,
                   url_for, g, abort, session)
from flask_wtf.csrf import CsrfProtect
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import config
import version
import crypto_util
import store
import template_filters
from db import (db_session, Source, Submission, SourceStar, get_one_or_else,
                Journalist)

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


def logged_in():
    return 'logged_in' in session


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not logged_in():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        journalist = Journalist.login(request.form['username'],
                                      request.form['password'])
        if journalist:
            session['id'] = journalist.id
            session['logged_in'] = True
            return redirect(url_for('index'))
        elif journalist == None:
            flash("Incorrect username", "notification")
        elif journalist == False:
            flash("Incorrect password", "notification")

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop('id', None)
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.before_request
def setup_g():
    """Store commonly used values in Flask's special g object"""
    if request.method == 'POST':
        sid = request.form.get('sid')
        if sid:
            g.sid = sid
            g.source = get_source(sid)


def get_docs(sid):
    """Get docs associated with source id `sid`, sorted by submission date"""
    docs = []
    for filename in os.listdir(store.path(sid)):
        os_stat = os.stat(store.path(sid, filename))
        docs.append(dict(
            name=filename,
            date=datetime.fromtimestamp(os_stat.st_mtime),
            size=os_stat.st_size,
        ))
    # sort in chronological order
    docs.sort(key=lambda x: int(x['name'].split('-')[0]))
    return docs


def make_star_true(sid):
    source = get_source(sid)
    if source.star:
        source.star.starred = True
    else:
        source_star = SourceStar(source)
        db_session.add(source_star)


def make_star_false(sid):
    source = get_source(sid)
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
    for source in Source.query.filter_by(pending=False).order_by(Source.last_updated.desc()).all():
        star = SourceStar.query.filter(SourceStar.source_id == source.id).first()
        if star and star.starred:
            starred.append(source)
        else:
            unstarred.append(source)
        source.num_unread = len(
            Submission.query.filter(Submission.source_id == source.id, Submission.downloaded == False).all())

    return render_template('index.html', unstarred=unstarred, starred=starred)


@app.route('/col/<sid>')
@login_required
def col(sid):
    source = get_source(sid)
    docs = get_docs(sid)
    submissions = [submission.filename for submission in Submission.query.filter(Submission.source_id == source.id).all()]
    # Only include documents loaded from the filesystem which are replies or which are also listed in the
    # submissions table to avoid displaying partially uploaded files (#561).
    docs = [doc for doc in docs if doc['name'] in submissions or doc['name'].endswith('reply.gpg')]

    haskey = crypto_util.getkey(sid)
    return render_template("col.html", sid=sid,
                           codename=source.journalist_designation, docs=docs, haskey=haskey,
                           flagged=source.flagged)


def delete_collection(source_id):
    # Delete the source's collection of submissions
    store.delete_source_directory(source_id)

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

    cols_selected = request.form.getlist('cols_selected') # getlist is cgi.FieldStorage.getlist
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
    flash("%s's collection deleted" % (source.journalist_designation,), "notification")
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
        Submission.query.filter(Submission.filename == fn).one().downloaded = True
    except NoResultFound as e:
        app.logger.error("Could not mark " + fn + " as downloaded: %s" % (e,))
    db_session.commit()
    return send_file(store.path(sid, fn), mimetype="application/pgp-encrypted")


@app.route('/reply', methods=('POST',))
@login_required
def reply():
    msg = request.form['msg']
    g.source.interaction_count += 1
    filename = "{0}-reply.gpg".format(g.source.interaction_count)

    crypto_util.encrypt(crypto_util.getkey(g.sid), msg, output=
    store.path(g.sid, filename))

    db_session.commit()
    return render_template('reply.html', sid=g.sid,
                           codename=g.source.journalist_designation)


@app.route('/regenerate-code', methods=('POST',))
@login_required
def generate_code():
    original_journalist_designation = g.source.journalist_designation
    g.source.journalist_designation = crypto_util.display_id()
    
    for doc in Submission.query.filter(Submission.source_id == g.source.id).all():
        doc.filename = store.rename_submission(g.sid, doc.filename, g.source.journalist_filename())
    db_session.commit()

    flash("The source '%s' has been renamed to '%s'" % (original_journalist_designation, g.source.journalist_designation), "notification")
    return redirect('/col/' + g.sid)


@app.route('/download_unread/<sid>')
@login_required
def download_unread(sid):
    id = Source.query.filter(Source.filesystem_id == sid).one().id
    docs = [doc.filename for doc in
            Submission.query.filter(Submission.source_id == id, Submission.downloaded == False).all()]
    return bulk_download(sid, docs)


@app.route('/bulk', methods=('POST',))
@login_required
def bulk():
    action = request.form['action']

    doc_names_selected = request.form.getlist('doc_names_selected')
    docs_selected = [
        doc for doc in get_docs(g.sid) if doc['name'] in doc_names_selected]
    filenames_selected = [
        doc['name'] for doc in docs_selected]

    if not docs_selected:
        if action == 'download':
            flash("No collections selected to download!", "error")
        elif action == 'delete':
            flash("No collections selected to delete!", "error")
        return redirect(url_for('col', sid=g.sid))

    if action == 'download':
        return bulk_download(g.sid, filenames_selected)
    elif action == 'delete':
        return bulk_delete(g.sid, docs_selected)
    else:
        abort(400)


def bulk_delete(sid, docs_selected):
    source = get_source(sid)
    confirm_delete = bool(request.form.get('confirm_delete', False))
    if confirm_delete:
        for doc in docs_selected:
            if not doc['name'].endswith('reply.gpg'):
                db_session.delete(Submission.query.filter(Submission.filename == doc['name']).one())
            fn = store.path(sid, doc['name'])
            store.secure_unlink(fn)
        db_session.commit()
    return render_template('delete.html', sid=sid,
                           codename=source.journalist_designation,
                           docs_selected=docs_selected, confirm_delete=confirm_delete)


def bulk_download(sid, docs_selected):
    source = get_source(sid)
    filenames = []
    for doc in docs_selected:
        filenames.append(store.path(sid, doc))
        try:
            Submission.query.filter(Submission.filename == doc).one().downloaded = True
        except NoResultFound as e:
            app.logger.error("Could not mark " + doc + " as downloaded: %s" % (e,))
    db_session.commit()
    zip = store.get_bulk_archive(filenames, zip_directory=source.journalist_filename())
    return send_file(zip.name, mimetype="application/zip",
                     attachment_filename=source.journalist_filename() + ".zip",
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
