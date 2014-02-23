# -*- coding: utf-8 -*-
import os
from datetime import datetime
import uuid

from flask import (Flask, request, render_template, send_file, redirect,
                   flash, url_for)
from flask_wtf.csrf import CsrfProtect

import config
import version
import crypto_util
import store
import background
import db

app = Flask(__name__, template_folder=config.JOURNALIST_TEMPLATES_DIR)
app.config.from_object(config.FlaskConfig)
CsrfProtect(app)

app.jinja_env.globals['version'] = version.__version__
if getattr(config, 'CUSTOM_HEADER_IMAGE', None):
    app.jinja_env.globals['header_image'] = config.CUSTOM_HEADER_IMAGE
    app.jinja_env.globals['use_custom_header_image'] = True
else:
    app.jinja_env.globals['header_image'] = 'securedrop.png'
    app.jinja_env.globals['use_custom_header_image'] = False


def get_docs(sid):
    """Get docs associated with source id `sid` sorted by submission date"""
    docs = []
    flagged = False
    for filename in os.listdir(store.path(sid)):
        if filename == '_FLAG':
            flagged = True
            continue
        os_stat = os.stat(store.path(sid, filename))
        docs.append(dict(
            name=filename,
            date=str(datetime.fromtimestamp(os_stat.st_mtime)),
            size=os_stat.st_size,
        ))
    # sort by date since ordering by filename is meaningless
    docs.sort(key=lambda x: x['date'])
    return docs, flagged


@app.after_request
def no_cache(response):
    """Minimize potential traces of site access by telling the browser not to
    cache anything"""
    no_cache_headers = {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '-1',
    }
    for header, header_value in no_cache_headers.iteritems():
        response.headers.add(header, header_value)
    return response


@app.route('/')
def index():
    dirs = os.listdir(config.STORE_DIR)
    cols = []
    db_session = db.sqlalchemy_handle()
    for source_id in dirs:
        display_id = db.display_id(source_id, db_session)
        cols.append(dict(
            sid=source_id,
            name=display_id,
            date=str(datetime.fromtimestamp(os.stat(store.path(source_id)).st_mtime)
                     ).split('.')[0]
        ))
    db_session.close()
    cols.sort(key=lambda x: x['date'], reverse=True)
    return render_template('index.html', cols=cols)


@app.route('/col/<sid>')
def col(sid):
    docs, flagged = get_docs(sid)
    haskey = crypto_util.getkey(sid)
    return render_template("col.html", sid=sid,
                           codename=db.display_id(sid, db.sqlalchemy_handle()), docs=docs,
                           haskey=haskey, flagged=flagged)


def delete_collection(source_id):
    store.delete_source_directory(source_id)
    crypto_util.delete_reply_keypair(source_id)
    db.delete_source(source_id)


@app.route('/col/delete', methods=('POST',))
def col_delete():
    if 'cols_selected' in request.form:
        # deleting multiple collections from the index
        if len('cols_selected') < 1:
            flash("No collections selected to delete!", "warning")
        else:
            cols_selected = request.form.getlist('cols_selected')
            for source_id in cols_selected:
                delete_collection(source_id)
            flash("%s %s deleted" % (
                len(cols_selected),
                "collection" if len(cols_selected) == 1 else "collections"
            ), "notification")
    else:
        # deleting a single collection from its /col page
        source_id, col_name = request.form['sid'], request.form['col_name']
        delete_collection(source_id)
        flash("%s's collection deleted" % (col_name,), "notification")

    return redirect(url_for('index'))

@app.route('/col/<sid>/<fn>')
def doc(sid, fn):
    if '..' in fn or fn.startswith('/'):
        abort(404)
    return send_file(store.path(sid, fn), mimetype="application/pgp-encrypted")


@app.route('/reply', methods=('POST',))
def reply():
    sid = request.form['sid']
    msg = request.form['msg']
    crypto_util.encrypt(crypto_util.getkey(sid), msg, output=
                        store.path(sid, 'reply-%s.gpg' % uuid.uuid4()))
    return render_template('reply.html', sid=sid, codename=db.display_id(sid,
        db.sqlalchemy_handle()))


@app.route('/regenerate-code', methods=('POST',))
def generate_code():
    sid = request.form['sid']
    db.regenerate_display_id(sid)
    return redirect('/col/' + sid)


@app.route('/bulk', methods=('POST',))
def bulk():
    action = request.form['action']

    sid = request.form['sid']
    doc_names_selected = request.form.getlist('doc_names_selected')
    docs_selected = [
        doc for doc in get_docs(sid)[0] if doc['name'] in doc_names_selected]

    if action == 'download':
        return bulk_download(sid, docs_selected)
    elif action == 'delete':
        return bulk_delete(sid, docs_selected)
    else:
        abort(400)


def bulk_delete(sid, docs_selected):
    confirm_delete = bool(request.form.get('confirm_delete', False))
    if confirm_delete:
        for doc in docs_selected:
            fn = store.path(sid, doc['name'])
            store.secure_unlink(fn)
    return render_template(
        'delete.html', sid=sid, codename=db.display_id(sid, db.sqlalchemy_handle()),
        docs_selected=docs_selected, confirm_delete=confirm_delete)


def bulk_download(sid, docs_selected):
    filenames = [store.path(sid, doc['name']) for doc in docs_selected]
    zip = store.get_bulk_archive(filenames)
    return send_file(zip.name, mimetype="application/zip",
                     attachment_filename=db.display_id(sid, db.sqlalchemy_handle()) + ".zip",
                     as_attachment=True)


@app.route('/flag', methods=('POST',))
def flag():
    def create_flag(sid):
        """Flags a SID by creating an empty _FLAG file in their collection directory"""
        flag_file = store.path(sid, '_FLAG')
        open(flag_file, 'a').close()
        return flag_file
    sid = request.form['sid']
    create_flag(sid)
    return render_template('flag.html', sid=sid, codename=db.display_id(sid, db.sqlalchemy_handle()))

if __name__ == "__main__":
    # TODO make sure debug=False in production
    app.run(debug=True, host='0.0.0.0', port=8081)
