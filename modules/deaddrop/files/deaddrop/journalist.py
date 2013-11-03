# -*- coding: utf-8 -*-
import os
from datetime import datetime
import uuid

from flask import Flask, request, render_template, send_file

import config, version, crypto, store, background

app = Flask(__name__, template_folder=config.JOURNALIST_TEMPLATES_DIR)
app.secret_key = config.SECRET_KEY

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

@app.context_processor
def global_template_vars():
  return dict(version=version.__version__)

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

@app.route('/<sid>')
def col(sid):
  fns = os.listdir(store.path(sid))
  docs = []
  for f in fns:
    docs.append(dict(
      name=f,
      date=str(datetime.fromtimestamp(os.stat(store.path(sid, f)).st_mtime))
    ))

  docs.sort(key=lambda x: x['date'])
  haskey = bool(crypto.getkey(sid))

  return render_template("col.html", sid=sid,
      codename=crypto.displayid(sid), docs=docs, haskey=haskey)

@app.route('/<sid>/<fn>')
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

if __name__ == "__main__":
  app.run(debug=True, port=8081)
