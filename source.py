import os, time
import web
import config, crypto
web.config.debug = True

urls = (
  '/', 'index',
  '/generate/', 'generate',
  '/lookup/', 'lookup',
  '/upload/', 'upload'
)

render = web.template.render('templates/')

class index:
    def GET(self):
        return render.index()

class generate:
    def GET(self):
        raise web.seeother('/')
    
    def POST(self):
        randomid = crypto.genrandomid()
        return render.generate(randomid)

class lookup:
    def GET(self):
        return render.lookup_get()
    
    def POST(self):
        i = web.input('id')
        #@@look for messages
        return render.lookup(i.id)

class upload:
    def GET(self):
        raise web.seeother('/lookup/')
    
    def POST(self):
        i = web.input('id', fh={}, msg=None)
        loc = '%s/%s' % (config.STORE_DIR, crypto.shash(i.id))
        if not os.path.exists(loc): os.mkdir(loc)
        
        loc += '/%s.enc' % time.time()
        if i.msg:
            crypto.encrypt(config.JOURNALIST_KEY, i.msg, loc)
        elif i.fh:
            crypto.encrypt(config.JOURNALIST_KEY, i.fh.file, loc)
        
        return render.lookup(i.id, received=True)
        #if nokey:
        #    background.execute(lambda: crypto.genkeypair(crypto.shash(i.id), i.id))
        

app = web.application(urls, locals())
if __name__ == "__main__":
    app.run()