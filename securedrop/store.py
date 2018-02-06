# -*- coding: utf-8 -*-
import gzip
import os
import re
import tempfile
import zipfile

from werkzeug.utils import secure_filename

import crypto_util

from secure_tempfile import SecureTemporaryFile


VALIDATE_FILENAME = re.compile(
    "^(?P<index>\d+)\-[a-z0-9-_]*"
    "(?P<file_type>msg|doc\.(gz|zip)|reply)\.gpg$").match


class PathException(Exception):

    """An exception raised by `util.verify` when it encounters a bad path. A path
    can be bad when it is not absolute or not normalized.
    """
    pass


class Storage:

    def __init__(self, storage_path, temp_dir, gpg_key):
        if not os.path.isabs(storage_path):
            raise PathException("storage_path {} is not absolute".format(
                storage_path))
        self.__storage_path = storage_path

        if not os.path.isabs(temp_dir):
            raise PathException("temp_dir {} is not absolute".format(
                temp_dir))
        self.__temp_dir = temp_dir

        self.__gpg_key = gpg_key

    def verify(self, p):
        """Assert that the path is absolute, normalized, inside
           `self.__storage_path`, and matches the filename format.
        """

        # os.path.abspath makes the path absolute and normalizes
        # '/foo/../bar' to '/bar', etc. We have to check that the path is
        # normalized before checking that it starts with the
        # `self.__storage_path` or else a malicious actor could append a
        # bunch of '../../..' to access files outside of the store.
        if not p == os.path.abspath(p):
            raise PathException("The path is not absolute and/or normalized")

        # Check that the path p is in self.__storage_path
        if os.path.relpath(p, self.__storage_path).startswith('..'):
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

    def path(self, *s):
        """Get the normalized, absolute file path, within
           `self.__storage_path`.
        """
        joined = os.path.join(os.path.abspath(self.__storage_path), *s)
        absolute = os.path.abspath(joined)
        self.verify(absolute)
        return absolute

    def get_bulk_archive(self, selected_submissions, zip_directory=''):
        """Generate a zip file from the selected submissions"""
        zip_file = tempfile.NamedTemporaryFile(
            prefix='tmp_securedrop_bulk_dl_',
            dir=self.__temp_dir,
            delete=False)
        sources = set([i.source.journalist_designation
                       for i in selected_submissions])
        # The below nested for-loops are there to create a more usable
        # folder structure per #383
        with zipfile.ZipFile(zip_file, 'w') as zip:
            for source in sources:
                fname = ""
                submissions = [s for s in selected_submissions
                               if s.source.journalist_designation == source]
                for submission in submissions:
                    filename = self.path(submission.source.filesystem_id,
                                         submission.filename)
                    self.verify(filename)
                    document_number = submission.filename.split('-')[0]
                    if zip_directory == submission.source.journalist_filename:
                        fname = zip_directory
                    else:
                        fname = os.path.join(zip_directory, source)
                    zip.write(filename, arcname=os.path.join(
                        fname,
                        "%s_%s" % (document_number,
                                   submission.source.last_updated.date()),
                        os.path.basename(filename)
                    ))
        return zip_file

    def save_file_submission(self, filesystem_id, count, journalist_filename,
                             filename, stream):
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
        encrypted_file_path = self.path(filesystem_id, encrypted_file_name)
        with SecureTemporaryFile("/tmp") as stf:
            with gzip.GzipFile(filename=sanitized_filename,
                               mode='wb', fileobj=stf) as gzf:
                # Buffer the stream into the gzip file to avoid excessive
                # memory consumption
                while True:
                    buf = stream.read(1024 * 8)
                    if not buf:
                        break
                    gzf.write(buf)

            crypto_util.encrypt(stf, self.__gpg_key, encrypted_file_path)

        return encrypted_file_name

    def save_message_submission(self, filesystem_id, count,
                                journalist_filename, message):
        filename = "{0}-{1}-msg.gpg".format(count, journalist_filename)
        msg_loc = self.path(filesystem_id, filename)
        crypto_util.encrypt(message, self.__gpg_key, msg_loc)
        return filename

    def rename_submission(self,
                          filesystem_id,
                          orig_filename,
                          journalist_filename):
        check_submission_name = VALIDATE_FILENAME(orig_filename)
        if check_submission_name:
            parsed_filename = check_submission_name.groupdict()
            if parsed_filename.get('file_type'):
                new_filename = "{}-{}-{}.gpg".format(
                    parsed_filename['index'], journalist_filename,
                    parsed_filename['file_type'])
                try:
                    os.rename(self.path(filesystem_id, orig_filename),
                              self.path(filesystem_id, new_filename))
                except OSError:
                    pass
                else:
                    # Only return new filename if successful
                    return new_filename
        return orig_filename
