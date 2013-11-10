# -*- coding: utf-8 -*-
import os, datetime, uuid
import web
import config, crypto, store, version
import zipfile

urls = (
  '/', 'index',
  '/reply/', 'reply',
  '/([A-Z1-7]+)/', 'col',
  '/([A-Z1-7]+)/download', 'download',
  '/([A-Z1-7]+)/([0-9]+\.[0-9]+(?:_msg|_doc\.zip|)\.gpg)', 'doc' 
)

render = web.template.render(config.JOURNALIST_TEMPLATES_DIR, base='base', 
    globals={'version':version.__version__})

class index:
    def GET(self):
        dirs = os.listdir(config.STORE_DIR)
        cols = []
        for d in dirs:
            if not os.listdir(store.path(d)): continue
            cols.append(web.storage(name=d, codename=crypto.displayid(d), date=
              str(datetime.datetime.fromtimestamp(
                os.stat(store.path(d)).st_mtime
              )).split('.')[0]
            ))
        cols.sort(lambda x,y: cmp(x.date, y.date), reverse=True)

        web.header('Cache-Control', 'no-cache, no-store, must-revalidate')
        web.header('Pragma', 'no-cache')
        web.header('Expires', '-1')
        return render.index(cols)

class col:
    def GET(self, sid):
        fns = os.listdir(store.path(sid))
        docs = []
        for f in fns:
            docs.append(web.storage(
              name=f, 
              date=str(datetime.datetime.fromtimestamp(os.stat(store.path(sid, f)).st_mtime))
            ))
        docs.sort(lambda x,y: cmp(x.date, y.date))
        
        haskey = bool(crypto.getkey(sid))

        web.header('Cache-Control', 'no-cache, no-store, must-revalidate')
        web.header('Pragma', 'no-cache')
        web.header('Expires', '-1')
        return render.col(docs, sid, haskey, codename=crypto.displayid(sid))
 
class doc:
    def GET(self, sid, fn):
        web.header('Content-Type', 'application/octet-stream')
        web.header('Content-Disposition', 'attachment; filename="' + 
          crypto.displayid(sid).replace(' ', '_') + '_' + fn + '"')

        web.header('Cache-Control', 'no-cache, no-store, must-revalidate')
        web.header('Pragma', 'no-cache')
        web.header('Expires', '-1')
        return file(store.path(sid, fn)).read()

class download:
    def POST(self, sid):
        files = web.data().replace('=on','').split('&')
        zipfilename = 'selected_' + str(datetime.datetime.now().microsecond) + '.zip'
        zip = zipfile.ZipFile(zipfilename, 'w')
        for file in files:
            zip.write(store.path(sid, file), file)
        zip.close()
        
        web.header('Content-Type', 'application/octet-stream')
        web.header('Content-Disposition', 'attachment; filename="' + zipfilename + '"')
        web.header('Cache-Control', 'no-cache, no-store, must-revalidate')
        web.header('Pragma', 'no-cache')
        web.header('Expires', '-1')
        
        zip = open(zipfilename, 'r')
        writeback = zip.read()
        zip.close()
        return writeback

class reply:
    def GET(self):
        raise web.seeother('/')
    
    def POST(self):
        i = web.input('sid', 'msg')
        crypto.encrypt(crypto.getkey(i.sid), i.msg, output=
          store.path(i.sid, 'reply-%.2f.gpg' % (uuid.uuid4().int, ))
        )

        web.header('Cache-Control', 'no-cache, no-store, must-revalidate')
        web.header('Pragma', 'no-cache')
        web.header('Expires', '-1')
        return render.reply(i.sid)
        

web.config.debug = False
app = web.application(urls, locals())
application = app.wsgifunc()

if __name__ == "__main__":
    app.run()
