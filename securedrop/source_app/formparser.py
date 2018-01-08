# flake8: noqa
# -*- coding: utf-8 -*-
"""
    werkzeug.formparser
    ~~~~~~~~~~~~~~~~~~~

    This module implements the form parsing.  It supports url-encoded forms
    as well as non-nested multipart uploads.

    :copyright: (c) 2014 by the Werkzeug Team, see AUTHORS for more details.
    :copyright: (c) 2018 Freedom of the Press Foundation
    :license: BSD, see LICENSE for more details.
"""
from werkzeug.formparser import MultiPartParser, _begin_file,\
                    _begin_form, _cont, _end
from werkzeug.datastructures import FileStorage


class SDMultiPartParser(MultiPartParser):

    def parse_parts(self, file, boundary, content_length):
        """Generate ``('file', (name, val))`` and
        ``('form', (name, val))`` parts.
        """
        # The following two variables are to limit the maximum number of files
        # we will process in every request. Rest of the files will be silently
        # dropped. Only the first 10 files, and the message will be processed.
        # Related issue:
        MAX_FILE_ALLOWED = 10
        file_count = 0


        in_memory = 0

        for ellt, ell in self.parse_lines(file, boundary, content_length):
            if ellt == _begin_file:
                if file_count > MAX_FILE_ALLOWED:
                    continue
                headers, name, filename = ell
                is_file = True
                guard_memory = False
                filename, container = self.start_file_streaming(
                    filename, headers, content_length)
                _write = container.write

            elif ellt == _begin_form:
                headers, name = ell
                is_file = False
                container = []
                _write = container.append
                guard_memory = self.max_form_memory_size is not None

            elif ellt == _cont:
                _write(ell)
                # if we write into memory and there is a memory size limit we
                # count the number of bytes in memory and raise an exception if
                # there is too much data in memory.
                if guard_memory:
                    in_memory += len(ell)
                    if in_memory > self.max_form_memory_size:
                        self.in_memory_threshold_reached(in_memory)

            elif ellt == _end:
                if is_file:
                    container.seek(0)
                    file_count = file_count + 1
                    if file_count > MAX_FILE_ALLOWED:
                        continue
                    yield ('file',
                           (name, FileStorage(container, filename, name,
                                              headers=headers)))
                else:
                    part_charset = self.get_part_charset(headers)
                    yield ('form',
                           (name, b''.join(container).decode(
                               part_charset, self.errors)))

