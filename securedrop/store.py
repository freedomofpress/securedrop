# -*- coding: utf-8 -*-
import os
import re
import config
import zipfile
import crypto_util
import uuid
import tempfile

VALIDATE_FILENAME = re.compile(
    "^(reply-)?[a-f0-9-]+(_msg|_doc\.zip|)\.gpg$").match


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

    if os.path.commonprefix([config.STORE_DIR, p]) != config.STORE_DIR:
        raise PathException("Invalid directory %s" % (p, ))

    filename = os.path.basename(p)
    ext = os.path.splitext(filename)[-1]

    if os.path.isfile(p):
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


def log(msg):
    file(path('NOTES'), 'a').write(msg)
