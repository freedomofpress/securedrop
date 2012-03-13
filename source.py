import os, time, datetime
import web
import config, crypto, background, store

urls = (
  '/', 'index',
  '/generate/', 'generate',
  '/lookup/', 'lookup',
  '/upload/', 'upload',
  '/delete/', 'delete'
)

render = web.template.render(config.SOURCE_TEMPLATES_DIR, base='base')

class index:
    def GET(self):
        return render.index()

class generate:
    def GET(self):
        raise web.seeother('/')
    
    def POST(self):
        iid = crypto.genrandomid()
        if os.path.exists(store.path(iid)):
            # if this happens, we're not using very secure crypto
            store.log('Got a duplicate ID.')
        else:
            os.mkdir(store.path(crypto.shash(iid)))
            
        return render.generate(iid)

class lookup:
    def GET(self):
        return render.lookup_get()
    
    def POST(self):
        i = web.input('id', fh={}, msg=None, mid=None, action=None)
        sid = crypto.shash(i.id)
        loc = store.path(sid)
        if not os.path.exists(loc): raise web.notfound()
        
        received = False
        
        if i.action == 'upload':
            if i.msg:
                loc1 = store.path(sid, '%s.enc' % time.time())
                crypto.encrypt(config.JOURNALIST_KEY, i.msg, loc1)
            if i.fh.file:
                # we put two zeroes here so that we don't save a file 
                # with the same name as the message
                loc2 = store.path(sid, '%s00.enc' % time.time())
                crypto.encrypt(config.JOURNALIST_KEY, i.fh.file, loc2)

            if not crypto.getkey(sid):
                background.execute(lambda: crypto.genkeypair(sid, i.id))
            
            received = True
        
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
                  date=datetime.datetime.fromtimestamp(float(store.cleanname(fn))),
                  msg=crypto.decrypt(sid, i.id, file(store.path(sid, fn)).read())
                ))
        return render.lookup(i.id, msgs, received=received)
           

app = web.application(urls, locals())
application = app.wsgifunc()
if __name__ == "__main__":
    app.run()
