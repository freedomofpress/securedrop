# -*- coding: utf-8 -*-
import os
import re
import web
import config

# taken from store.urls mapping
VALIDATE_FILENAME = re.compile("^[0-9]+\.[0-9]+(?:_msg|_doc|)\.gpg$").match

def verify(p):
    if os.path.commonprefix([config.STORE_DIR, p]) != config.STORE_DIR:
        raise Exception("Invalid directory %s" % (p, ))

    filename = os.path.basename(p)
    ext = os.path.splitext(filename)[-1]

    if not ext:
        # if there's no extension, we're at a subdirectory
        return

    elif ext != '.gpg':
        # if there's an extension, verify it's a GPG
        raise Exception("Invalid file extension %s" % (ext, ))

    if not VALIDATE_FILENAME(filename):
        raise Exception("Invalid filename %s" % (filename, ))
    return

def path(*s):
    joined = os.path.join(os.path.abspath(config.STORE_DIR), *s)
    absolute = os.path.abspath(joined)
    verify(absolute)
    return absolute

def log(msg):
    file(path('NOTES'), 'a').write(msg)

def cleanname(fn):
    return web.rstrips(web.rstrips(web.lstrips(web.rstrips(fn, '.gpg'), 'reply-'), '_doc'), '_msg')
