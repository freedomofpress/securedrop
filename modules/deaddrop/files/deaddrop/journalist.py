# -*- coding: utf-8 -*-
import os
from datetime import datetime
import uuid

from flask import Flask, request, render_template, send_file
from flask_wtf.csrf import CsrfProtect

import config, version, crypto, store, background

app = Flask(__name__, template_folder=config.JOURNALIST_TEMPLATES_DIR)
app.secret_key = config.SECRET_KEY

app.jinja_env.globals['version'] = version.__version__

def get_docs(sid):
  """Get docs associated with source id `sid`"""
  fns = os.listdir(store.path(sid))
  docs = []
  for f in fns:
    docs.append(dict(
      name=f,
      date=str(datetime.fromtimestamp(os.stat(store.path(sid, f)).st_mtime))
    ))
  # sort by date since ordering by filename is meaningless
  docs.sort(key=lambda x: x['date'])
  return docs

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
  for d in dirs:
    if not os.listdir(store.path(d)): continue
    cols.append(dict(
      name=d,
      sid=crypto.displayid(d),
      date=str(datetime.fromtimestamp(os.stat(store.path(d)).st_mtime)).split('.')[0]
    ))
  cols.sort(key=lambda x: x['date'], reverse=True)
  return render_template('index.html', cols=cols)

@app.route('/col/<sid>')
def col(sid):
  docs = get_docs(sid)
  docs.sort(key=lambda x: x['date'])
  haskey = bool(crypto.getkey(sid))

  return render_template("col.html", sid=sid,
      codename=crypto.displayid(sid), docs=docs, haskey=haskey)

@app.route('/col/<sid>/<fn>')
def doc(sid, fn):
  if '..' in fn or fn.startswith('/'):
    abort(404)
  return send_file(store.path(sid, fn), mimetype="application/pgp-encrypted")

@app.route('/reply', methods=('POST',))
def reply():
  sid, msg = request.form['sid'], request.form['msg']
  crypto.encrypt(crypto.getkey(sid), request.form['msg'], output=
    store.path(sid, 'reply-%s.gpg' % uuid.uuid4()))
  return render_template('reply.html', sid=sid, codename=crypto.displayid(sid))

@app.route('/delete', methods=('POST',))
def delete():
  sid = request.form['sid']
  doc_names_selected = request.form.getlist('doc_names_selected')
  docs_selected = [doc for doc in get_docs(sid) if doc['name'] in doc_names_selected]
  confirm_delete = bool(request.form.get('confirm_delete', False))
  if confirm_delete:
      for doc in docs_selected:
          fn = store.path(sid, doc['name'])
          crypto.secureunlink(fn)
  return render_template('delete.html', sid=sid, codename=crypto.displayid(sid),
                         docs_selected=docs_selected, confirm_delete=confirm_delete)

if __name__ == "__main__":
  # TODO: make sure this gets run by the web server
  CsrfProtect(app)
  app.run(debug=True, port=8081)
