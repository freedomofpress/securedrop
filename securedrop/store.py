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
import gzip
from werkzeug import secure_filename

from secure_tempfile import SecureTemporaryFile

import logging
log = logging.getLogger(__name__)

VALIDATE_FILENAME = re.compile(
    "^(?P<index>\d+)\-[a-z0-9-_]*(?P<file_type>msg|doc\.(gz|zip)|reply)\.gpg$").match


class PathException(Exception):

    """An exception raised by `store.verify` when it encounters a bad path. A path
    can be bad when it is not absolute, not normalized, not within
    `config.STORE_DIR`, or doesn't match the filename format.
    """
    pass


def verify(p):
    """Assert that the path is absolute, normalized, inside `config.STORE_DIR`, and
    matches the filename format.
    """
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
    """Get the normalized, absolute file path, within `config.STORE_DIR`."""
    joined = os.path.join(os.path.abspath(config.STORE_DIR), *s)
    absolute = os.path.abspath(joined)
    verify(absolute)
    return absolute


def get_bulk_archive(items_selected, zip_directory=''):
    zip_file = tempfile.NamedTemporaryFile(prefix='tmp_securedrop_bulk_dl_',
                                           dir=config.TEMP_DIR,
                                           delete=False)
    sources = set([i.source.journalist_designation for i in items_selected])
    # The below nested for-loops are there to create a more usable
    # folder structure per #383
    with zipfile.ZipFile(zip_file, 'w') as zip:
        for source in sources:
            submissions = [s for s in items_selected if s.source.journalist_designation == source]
            i = 1
            for submission in submissions:
                filename = path(submission.source.filesystem_id, submission.filename)
                verify(filename)
                zip.write(filename, arcname=os.path.join(
                    zip_directory,
                    source,
                    "%s_%s" % (i, submission.source.last_updated.date()),
                    os.path.basename(filename)
                ))
                i += 1
    return zip_file


def save_file_submission(sid, count, journalist_filename, filename, stream):
    sanitized_filename = secure_filename(filename)

    # We store file submissions in a .gz file for two reasons:
    #
    # 1. Downloading large files over Tor is very slow. If we can
    # compress the file, we can speed up future downloads.
    #
    # 2. We want to record the original filename because it might be
    # useful, either for context about the content of the submission
    # or for figuring out which application should be used to open
    # it. However, we'd like to encrypt that info and have the
    # decrypted file automatically have the name of the original
    # file. Given various usability constraints in GPG and Tails, this
    # is the most user-friendly way we have found to do this.

    encrypted_file_name = "{0}-{1}-doc.gz.gpg".format(
        count,
        journalist_filename)
    encrypted_file_path = path(sid, encrypted_file_name)
    with SecureTemporaryFile("/tmp") as stf:
        with gzip.GzipFile(filename=sanitized_filename, mode='wb', fileobj=stf) as gzf:
            # Buffer the stream into the gzip file to avoid excessive
            # memory consumption
            while True:
                buf = stream.read(1024 * 8)
                if not buf:
                    break
                gzf.write(buf)

        crypto_util.encrypt(stf, config.JOURNALIST_KEY, encrypted_file_path)

    return encrypted_file_name


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
    subprocess.check_call(command)
    return "success"


def delete_source_directory(source_id):
    secure_unlink(path(source_id), recursive=True)
    return "success"
