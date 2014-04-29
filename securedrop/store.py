# -*- coding: utf-8 -*-
import os
import re
import config
import zipfile
import crypto_util
import uuid
import tempfile
import subprocess
from cStringIO import StringIO
from shutil import copyfileobj

from MAT import mat
from MAT import strippers

import logging
log = logging.getLogger(__name__)

from werkzeug import secure_filename

VALIDATE_FILENAME = re.compile(
    "^(reply-)?[a-z0-9-_]+(-msg|-doc\.zip|)\.gpg$").match


class PathException(Exception):

    '''An exception raised by `store.verify` when it encounters a bad path. A path
    can be bad when it is not absolute, not normalized, not within
    `config.STORE_DIR`, or doesn't match the filename format.
    '''
    pass


def verify(p):
    '''Assert that the path is absolute, normalized, inside `config.STORE_DIR`, and
    matches the filename format.
    '''
    if not os.path.isabs(config.STORE_DIR):
        raise PathException("config.STORE_DIR(%s) is not absolute" % (
            config.STORE_DIR, ))

    # os.path.abspath makes the path absolute and normalizes '/foo/../bar' to
    # '/bar', etc. We have to check that the path is normalized before checking
    # that it starts with the `config.STORE_DIR` or else a malicious actor could
    # append a bunch of '../../..' to access files outside of the store.
    if not p == os.path.abspath(p):
        raise PathException("The path is not absolute and/or normalized")

    # Check that the path p is in config.STORE_DIR
    if os.path.relpath(p, config.STORE_DIR).startswith('..'):
        raise PathException("Invalid directory %s" % (p, ))

    if os.path.isfile(p):
        filename = os.path.basename(p)
        ext = os.path.splitext(filename)[-1]
        if filename == '_FLAG':
            return True
        if ext != '.gpg':
            # if there's an extension, verify it's a GPG
            raise PathException("Invalid file extension %s" % (ext, ))
        if not VALIDATE_FILENAME(filename):
            raise PathException("Invalid filename %s" % (filename, ))


def path(*s):
    '''Get the normalized, absolute file path, within `config.STORE_DIR`.'''
    joined = os.path.join(os.path.abspath(config.STORE_DIR), *s)
    absolute = os.path.abspath(joined)
    verify(absolute)
    return absolute


def get_bulk_archive(filenames):
    zip_file = tempfile.NamedTemporaryFile(prefix='tmp_securedrop_bulk_dl_')
    with zipfile.ZipFile(zip_file, 'w') as zip:
        for filename in filenames:
            verify(filename)
            zip.write(filename, arcname=os.path.basename(filename))
    return zip_file


def save_file_submission(sid, count, journalist_filename, filename, stream, content_type, strip_metadata):
    sanitized_filename = secure_filename(filename)
    clean_file = sanitize_metadata(stream, content_type, strip_metadata)

    s = StringIO()
    with zipfile.ZipFile(s, 'w') as zf:
        zf.writestr(sanitized_filename, clean_file.read() if clean_file else stream.read())
    s.reset()

    filename = "{0}-{1}-doc.zip.gpg".format(count, journalist_filename)
    file_loc = path(sid, filename)
    crypto_util.encrypt(config.JOURNALIST_KEY, s, file_loc)
    return filename


def save_message_submission(sid, count, journalist_filename, message):
    filename = "{0}-{1}-msg.gpg".format(count, journalist_filename)
    msg_loc = path(sid, filename)
    crypto_util.encrypt(config.JOURNALIST_KEY, message, msg_loc)
    return filename


def secure_unlink(fn, recursive=False, do_verify = True):
    if do_verify:
        verify(fn)
    command = ['srm']
    if recursive:
        command.append('-r')
    command.append(fn)
    return subprocess.check_call(command)


def delete_source_directory(source_id):
    secure_unlink(path(source_id), recursive=True)

def metadata_handler(f):
    return mat.create_class_file(f, False, add2archive=True)

def sanitize_metadata(stream, content_type, strip_metadata):
    text_plain = content_type == 'text/plain'

    s = None
    t = None
    clean_file = False

    if strip_metadata and not text_plain:
        t = tempfile.NamedTemporaryFile(delete = False)
        copyfileobj(stream, t)
        t.flush()
        file_meta = metadata_handler(t.name)

        if not file_meta.is_clean():
            file_meta.remove_all()
            f = open(t.name)
            s = StringIO()
            s.write(f.read())
            f.close()
            s.reset()
            secure_unlink(t.name, do_verify = False)
            t.close()
        else:
            secure_unlink(t.name, do_verify = False)
            t.close()

    return s

