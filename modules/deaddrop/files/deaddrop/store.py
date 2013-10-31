# -*- coding: utf-8 -*-
import os
import re
import web
import config

# taken from store.urls mapping
VALIDATE_FILENAME = re.compile("^(reply-)?[0-9]+\.[0-9]+(?:_msg|_doc\.zip|)\.gpg$").match

def verify(p):
    if not os.path.isabs(config.STORE_DIR):
        raise Exception("config.STORE_DIR(%s) is not absolute" % (
                        config.STORE_DIR, ))

    if os.path.commonprefix([config.STORE_DIR, p]) != config.STORE_DIR:
        raise Exception("Invalid directory %s" % (p, ))

    filename = os.path.basename(p)
    ext = os.path.splitext(filename)[-1]

    if os.path.isfile(p):
        if ext != '.gpg':
            # if there's an extension, verify it's a GPG
            raise Exception("Invalid file extension %s" % (ext, ))

        if not VALIDATE_FILENAME(filename):
            raise Exception("Invalid filename %s" % (filename, ))

def path(*s):
    joined = os.path.join(os.path.abspath(config.STORE_DIR), *s)
    absolute = os.path.abspath(joined)
    verify(absolute)
    return absolute

def log(msg):
    file(path('NOTES'), 'a').write(msg)

def cleanname(fn):
    return web.rstrips(web.rstrips(web.lstrips(web.rstrips(fn, '.gpg'), 'reply-'), '_doc'), '_msg')
