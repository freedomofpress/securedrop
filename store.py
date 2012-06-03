import os
import web
import config

def path(*s):
    return os.path.join(config.STORE_DIR, *s)

def log(msg):
    file(path('NOTES'), 'a').write(msg)

def cleanname(fn):
    return web.lstrips(web.rstrips(fn, '.gpg'), 'reply-')
