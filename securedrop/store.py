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
    "^(?P<index>\d+)\-[a-z0-9-_]+?(?P<file_type>msg|doc\.zip|)\.gpg$").match


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


def get_bulk_archive(filenames, zip_directory=''):
    zip_file = tempfile.NamedTemporaryFile(prefix='tmp_securedrop_bulk_dl_',
                                           dir=config.TEMP_DIR,
                                           delete=False)
    with zipfile.ZipFile(zip_file, 'w') as zip:
        for filename in filenames:
            verify(filename)
            zip.write(filename, arcname=os.path.join(
                zip_directory,
                os.path.basename(filename)
            ))
    return zip_file


def save_file_submission(sid, count, journalist_filename, filename, stream):
    sanitized_filename = secure_filename(filename)

    s = StringIO()
    with zipfile.ZipFile(s, 'w') as zf:
        zf.writestr(sanitized_filename, stream.read())
    s.seek(0)

    filename = "{0}-{1}-doc.zip.gpg".format(count, journalist_filename)
    file_loc = path(sid, filename)
    crypto_util.encrypt(s, config.JOURNALIST_KEY, file_loc)
    return filename


def save_message_submission(sid, count, journalist_filename, message):
    filename = "{0}-{1}-msg.gpg".format(count, journalist_filename)
    msg_loc = path(sid, filename)
    crypto_util.encrypt(message, config.JOURNALIST_KEY, msg_loc)
    return filename


def rename_submission(sid, orig_filename, journalist_filename):
    check_submission_name = VALIDATE_FILENAME(orig_filename)
    if check_submission_name:
        parsed_filename = check_submission_name.groupdict()
        if parsed_filename.get('file_type'):
            new_filename = "{}-{}-{}.gpg".format(
                parsed_filename['index'], journalist_filename,
                parsed_filename['file_type'])
            try:
                os.rename(path(sid, orig_filename), path(sid, new_filename))
            except OSError:
                pass
            else:
                return new_filename  # Only return new filename if successful
    return orig_filename


def secure_unlink(fn, recursive=False):
    verify(fn)
    command = ['srm']
    if recursive:
        command.append('-r')
    command.append(fn)
    return subprocess.check_call(command)


def delete_source_directory(source_id):
    secure_unlink(path(source_id), recursive=True)
