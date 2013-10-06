# -*- coding: utf-8 -*-
import os, uuid, datetime
import web
import config, crypto, background, store

urls = (
  '/', 'index',
  '/generate/', 'generate',
  '/lookup/', 'lookup',
)

render = web.template.render(config.SOURCE_TEMPLATES_DIR, base='base')

class index:
  def GET(self):
    web.header('Cache-Control', 'no-cache, no-store, must-revalidate')
    web.header('Pragma', 'no-cache')
    web.header('Expires', '-1')
    return render.index()

class generate:
  def GET(self):
    raise web.seeother('/')
  
  def POST(self):
    iid = crypto.genrandomid()
    if os.path.exists(store.path(crypto.shash(iid))):
      # if this happens, we're not using very secure crypto
      store.log('Got a duplicate ID.')
    else:
      os.mkdir(store.path(crypto.shash(iid)))
      
    web.header('Cache-Control', 'no-cache, no-store, must-revalidate')
    web.header('Pragma', 'no-cache')
    web.header('Expires', '-1')
    return render.generate(iid)

class lookup:
  def GET(self):
    web.header('Cache-Control', 'no-cache, no-store, must-revalidate')
    web.header('Pragma', 'no-cache')
    web.header('Expires', '-1')
    return render.lookup_get()
  
  def POST(self):
    i = web.input('id', fh={}, msg=None, mid=None, action=None)
    sid = crypto.shash(i.id)
    loc = store.path(sid)
    if not os.path.exists(loc): raise web.notfound()
    
    received = False
    
    if i.action == 'upload':
      if i.msg:
        loc1 = store.path(sid, '%.2f_msg.gpg' % (uuid.uuid4().int, ))
        crypto.encrypt(config.JOURNALIST_KEY, i.msg, loc1)
        received = 2
        
      if i.fh.value:
        # we put two zeroes here so that we don't save a file 
        # with the same name as the message
        loc2 = store.path(sid, '%.2f_doc.gpg' % (uuid.uuid4().int, ))
        crypto.encrypt(config.JOURNALIST_KEY, i.fh.file, loc2, fn=i.fh.filename)
        received = i.fh.filename or '[unnamed]'

      if not crypto.getkey(sid):
        background.execute(lambda: crypto.genkeypair(sid, i.id))
    
    elif i.action == 'delete':
      potential_files = os.listdir(loc)
      if i.mid not in potential_files: raise web.notfound()
      assert '/' not in i.mid
      crypto.secureunlink(store.path(sid, i.mid))
    
    msgs = []
    for fn in os.listdir(loc):
      if fn.startswith('reply-'):
        msgs.append(web.storage(
          id=fn,
          date=str(datetime.datetime.fromtimestamp(os.stat(store.path(sid, fn)).st_mtime)),
          msg=crypto.decrypt(sid, i.id, file(store.path(sid, fn)).read())
        ))

    web.header('Cache-Control', 'no-cache, no-store, must-revalidate')
    web.header('Pragma', 'no-cache')
    web.header('Expires', '-1')
    return render.lookup(i.id, msgs, received=received)

def notfound():
  web.header('Cache-Control', 'no-cache, no-store, must-revalidate')
  web.header('Pragma', 'no-cache')
  web.header('Expires', '-1')
  return web.notfound(render.notfound())

web.config.debug = False
app = web.application(urls, locals())
app.notfound = notfound
application = app.wsgifunc()

if __name__ == "__main__":
  app.run()
