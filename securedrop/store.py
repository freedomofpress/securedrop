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


def save_file_submission(sid, count, journalist_filename, filename, stream):
    sanitized_filename = secure_filename(filename)

    s = StringIO()
    with zipfile.ZipFile(s, 'w') as zf:
        zf.writestr(sanitized_filename, stream.read())
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


def rename_submission(sid, filename, journalist_filename):
    count = int(filename.split('-', 1)[0])
    if filename.endswith('doc.zip.gpg'):
        new_filename = "{0}-{1}-doc.zip.gpg".format(count, journalist_filename)
    elif filename.endswith('msg.gpg'):
        new_filename = "{0}-{1}-msg.gpg".format(count, journalist_filename)
    else:
        return filename # Return reply.gpg files unrenamed
    os.rename(path(sid, filename), path(sid, new_filename))
    return new_filename
    

def secure_unlink(fn, recursive=False):
    verify(fn)
    command = ['srm']
    if recursive:
        command.append('-r')
    command.append(fn)
    return subprocess.check_call(command)


def delete_source_directory(source_id):
    secure_unlink(path(source_id), recursive=True)
