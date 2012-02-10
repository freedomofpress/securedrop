import os, time, datetime
import web
import config, crypto, store

urls = (
  '/', 'index',
  '/reply/', 'reply',
  '/([a-f0-9]+)/', 'col',
  '/([a-f0-9]+)/([0-9]+\.[0-9]+\.enc)', 'doc'
)

render = web.template.render('journalist_templates/', base='base')

class index:
    def GET(self):
        dirs = os.listdir(config.STORE_DIR)
        cols = []
        for d in dirs:
            if not os.listdir(store.path(d)): continue
            cols.append(web.storage(name=d, date=
              datetime.datetime.fromtimestamp(
                os.stat(store.path(d)).st_mtime
            )))
        cols.sort(lambda x,y: cmp(x.date, y.date), reverse=True)
        return render.index(cols)

class col:
    def GET(self, sid):
        fns = os.listdir(store.path(sid))
        docs = []
        for f in fns:
            docs.append(web.storage(
              name=f, 
              date=datetime.datetime.fromtimestamp(float(store.cleanname(f)
            ))))
        docs.sort(lambda x,y: cmp(x.date, y.date))
        
        haskey = bool(crypto.getkey(sid))
        return render.col(docs, sid, haskey)
 
class doc:
    def GET(self, sid, fn):
        return file(store.path(sid, fn)).read()

class reply:
    def GET(self):
        raise web.seeother('/')
    
    def POST(self):
        i = web.input('sid', 'msg')
        crypto.encrypt(crypto.getkey(i.sid), i.msg, output=
          store.path(i.sid, 'reply-%s.enc' % time.time())
        )
        return render.reply(i.sid)
        

app = web.application(urls, locals())
if __name__ == "__main__":
    app.run()