# -*- coding: utf-8 -*-
import os
from datetime import datetime
import uuid

from flask import Flask, request, render_template, session, redirect, url_for, \
    flash
from itsdangerous import Signer, BadSignature
from werkzeug import secure_filename

import config, version, crypto, store, background

app = Flask(__name__, template_folder=config.SOURCE_TEMPLATES_DIR)
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

@app.template_filter()
def sign(s):
  return Signer(config.SECRET_KEY).sign(s)

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/generate', methods=('GET', 'POST'))
def generate():
  number_words = 8
  if request.method == 'POST':
    number_words = int(request.form['number-words'])
    if number_words not in range(4, 11): abort(500)
  return render_template('generate.html',
      codename=crypto.genrandomid(number_words))

@app.route('/create', methods=['POST'])
def create():
  # TODO: need to unescape?
  codename = Signer(config.SECRET_KEY).unsign(request.form['codename'])
  sid = crypto.shash(codename)
  if os.path.exists(store.path(sid)):
    # if this happens, we're not using very secure crypto
    store.log('Got a duplicate ID %s' % sid)
  else:
    os.mkdir(store.path(sid))
  session['codename'] = codename
  return redirect(url_for('lookup'))

def get_codename_ids(codename):
  sid = crypto.shash(codename)
  loc = store.path(sid)
  return sid, loc

def valid_codename(codename):
  return os.path.exists(get_codename_ids(codename)[1])

def get_msgs(codename):
  sid, loc = get_codename_ids(codename)
  msgs = []
  for fn in os.listdir(loc):
    if fn.startswith('reply-'):
      msgs.append(dict(
        id=fn,
        date=str(datetime.fromtimestamp(os.stat(store.path(sid, fn)).st_mtime)),
        msg=crypto.decrypt(sid, codename, file(store.path(sid, fn)).read())
      ))
  return msgs

@app.route('/submit', methods=('POST',))
def submit():
  if 'codename' in session and valid_codename(session['codename']):
    codename = session['codename']
    sid, loc = get_codename_ids(codename)

    msg = request.form['msg']
    fh = request.files['fh']
    if msg:
      msg_loc = store.path(sid, '%s_msg.gpg' % uuid.uuid4())
      crypto.encrypt(config.JOURNALIST_KEY, msg, msg_loc)
      flash("Thanks! We received your message.", "notification")
    if fh:
      file_loc = store.path(sid, "%s_doc.gpg" % uuid.uuid4())
      # TODO - retain original filename
      crypto.encrypt(config.JOURNALIST_KEY, fh, file_loc)
      flash("Thanks! We received your document '%s'."
          % fh.filename or '[unnamed]', "notification")

    #if not crypto.getkey(sid):
    #  background.execute(lambda: crypto.genkeypair(sid, codename))

  return redirect(url_for('lookup'))

@app.route('/delete', methods=('POST',))
def delete():
  if 'codename' in session and valid_codename(session['codename']):
    codename = session['codename']
    sid, loc = get_codename_ids(codename)

    msgid = request.form['msgid']
    potential_files = os.listdir(loc)
    if msgid not in potential_files: abort(404) # TODO are the checks necessary?
    assert '/' not in msgid
    crypto.secureunlink(store.path(sid, msgid))
    flash("Reply successfully deleted.", "notification")

  return redirect(url_for('lookup'))

@app.route('/lookup', methods=('GET',))
def lookup():
  if 'codename' in session and valid_codename(session['codename']):
    codename = session['codename']
    return render_template('lookup.html', codename=codename,
        msgs=get_msgs(codename))

  return render_template('lookup_get.html')

@app.errorhandler(404)
def page_not_found(error):
  return render_template('notfound.html'), 404

if __name__ == "__main__":
  app.run(debug=True, port=8080)
