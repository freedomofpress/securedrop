# -*- coding: utf-8 -*-
import config
import version
import crypto_util
import store
from db import db_session, Source, Submission, SourceStar, get_one_or_else

import os
from datetime import datetime
from flask import (Flask, request, render_template, send_file, redirect, flash, url_for, g, abort)
from flask_wtf.csrf import CsrfProtect
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import config
import version
import crypto_util
import store
import background
import util
from db import db_session, Source, Submission, SourceStar

app = Flask(__name__, template_folder=config.JOURNALIST_TEMPLATES_DIR)
app.config.from_object(config.FlaskConfig)
CsrfProtect(app)

app.jinja_env.globals['version'] = version.__version__
if getattr(config, 'CUSTOM_HEADER_IMAGE', None):
    app.jinja_env.globals['header_image'] = config.CUSTOM_HEADER_IMAGE
    app.jinja_env.globals['use_custom_header_image'] = True
else:
    app.jinja_env.globals['header_image'] = 'logo.png'
    app.jinja_env.globals['use_custom_header_image'] = False


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
            date=str(datetime.fromtimestamp(os_stat.st_mtime)),
            size=os_stat.st_size,
        ))
    # sort in chronological order
    docs.sort(key=lambda x: int(x['name'].split('-')[0]))
    return docs


@app.route('/')
def index():
    sources = []
    starred = []
    for source in Source.query.filter_by(pending=False).order_by(Source.last_updated.desc()).all():
        star = SourceStar.query.filter(SourceStar.source_id == source.id).first()
        if star and star.starred:
            starred.append(source)
        else:
            sources.append(source)
        source.num_unread = len(
            Submission.query.filter(Submission.source_id == source.id, Submission.downloaded == False).all())

    return render_template('index.html', sources=sources, starred=starred)


@app.route('/col/<sid>')
def col(sid):
    source = get_source(sid)
    docs = get_docs(sid)
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
def col_process():
    action = request.form['action']
    if action == 'delete':
        return col_delete()
    elif action == 'star':
        return col_star()
    elif action == 'un-star':
        return col_un_star()
    else:
        return abort(404)


def col_star():
    if 'cols_selected' not in request.form:
        return redirect(url_for('index'))

    cols_selected = request.form.getlist('cols_selected')
    for source_id in cols_selected:
        source = get_source(source_id)
        source_star = SourceStar.query.filter(SourceStar.source_id == source.id).first()
        if source_star:
            source_star.starred = True
        else:
            source_star = SourceStar(source)
            db_session.add(source_star)

    db_session.commit()
    return redirect(url_for('index'))


def col_un_star():
    if 'cols_selected' not in request.form:
        return redirect(url_for('index'))

    cols_selected = request.form.getlist('cols_selected')

    for source_id in cols_selected:
        source = get_source(source_id)
        query = SourceStar.query.filter(SourceStar.source_id == source.id)
        source_star = get_one_or_else(query, app.logger, abort)
        source_star.starred = False

    db_session.commit()
    return redirect(url_for('index'))


def col_delete():
    if 'cols_selected' in request.form:
        # deleting multiple collections from the index
        # Note: getlist is cgi.FieldStorage.getlist
        cols_selected = request.form.getlist('cols_selected')
        if len(cols_selected) < 1:
            flash("No collections selected to delete!", "warning")
        else:
            for source_id in cols_selected:
                delete_collection(source_id)
            flash("%s %s deleted" % (
                len(cols_selected),
                "collection" if len(cols_selected) == 1 else "collections"
            ), "notification")
    elif 'col_name' in request.form:
        # deleting a single collection from its /col page
        source_id, col_name = request.form['sid'], request.form['col_name']
        delete_collection(source_id)
        flash("%s's collection deleted" % (col_name,), "notification")

    return redirect(url_for('index'))

@app.route('/col/<sid>/<fn>')
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
def generate_code():
    g.source.journalist_designation = crypto_util.display_id()
    db_session.commit()
    return redirect('/col/' + g.sid)

@app.route('/download_unread/<sid>')
def download_unread(sid):
    id = Source.query.filter(Source.filesystem_id == sid).one().id
    docs = [doc.filename for doc in
            Submission.query.filter(Submission.source_id == id, Submission.downloaded == False).all()]
    return bulk_download(sid, docs)

@app.route('/bulk', methods=('POST',))
def bulk():
    action = request.form['action']

    doc_names_selected = request.form.getlist('doc_names_selected')
    docs_selected = [
        doc for doc in get_docs(g.sid) if doc['name'] in doc_names_selected]
    filenames_selected = [
        doc['name'] for doc in docs_selected]

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
    zip = store.get_bulk_archive(filenames)
    return send_file(zip.name, mimetype="application/zip",
                     attachment_filename=source.journalist_designation + ".zip",
                     as_attachment=True)


@app.route('/flag', methods=('POST',))
def flag():
    g.source.flagged = True
    db_session.commit()
    return render_template('flag.html', sid=g.sid,
                           codename=g.source.journalist_designation)


if __name__ == "__main__":
    # TODO make sure debug=False in production
    app.run(debug=True, host='0.0.0.0', port=8081)
