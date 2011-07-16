import os, time, datetime
import web
import config, crypto, background, store
web.config.debug = True

urls = (
  '/', 'index',
  '/generate/', 'generate',
  '/lookup/', 'lookup',
  '/upload/', 'upload',
  '/delete/', 'delete'
)

render = web.template.render('source_templates/')

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
        loc = store.path(crypto.shash(i.id))
        if not os.path.exists(loc): raise web.notfound()
        
        received = False
        
        if i.action == 'upload':
            loc += '/%s.enc' % time.time()
            if i.msg:
                crypto.encrypt(config.JOURNALIST_KEY, i.msg, loc)
            elif i.fh:
                crypto.encrypt(config.JOURNALIST_KEY, i.fh.file, loc)

            if not crypto.getkey(crypto.shash(i.id)):
                background.execute(lambda: crypto.genkeypair(crypto.shash(i.id), i.id))
            
            received = True
        
        elif i.action == 'delete':
            crypto.secureunlink(store.path(crypto.shash(i.id), i.mid))
        
        msgs = []
        for fn in os.listdir(store.path(crypto.shash(i.id))):
            if fn.startswith('reply-'):
                msgs.append(web.storage(
                  id=fn,
                  date=datetime.datetime.fromtimestamp(float(store.cleanname(fn))),
                  msg=crypto.decrypt(crypto.shash(i.id), i.id, file(store.path(crypto.shash(i.id), fn)).read())
                ))
        return render.lookup(i.id, msgs, received=received)
           

app = web.application(urls, locals())
if __name__ == "__main__":
    app.run()