# -*- coding: utf-8 -*-
import io
import os
import pytest
import unittest

from gnupg._util import _is_stream

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from sdconfig import config
import journalist_app
import secure_tempfile
import utils

from secure_tempfile import SecureTemporaryFile

MESSAGE = '410,757,864,530'


def test_read_before_writing():
    f = SecureTemporaryFile('/tmp')
    with pytest.raises(AssertionError) as err:
        f.read()
    assert 'You must write before reading!' in str(err)


def test_write_then_read_once():
    f = SecureTemporaryFile('/tmp')
    f.write(MESSAGE)
    assert f.read() == MESSAGE


def test_write_twice_then_read_once():
    f = SecureTemporaryFile('/tmp')
    f.write(MESSAGE)
    f.write(MESSAGE)
    assert f.read() == MESSAGE * 2


def test_write_then_read_twice():
    f = SecureTemporaryFile('/tmp')
    f.write(MESSAGE)
    assert f.read() == MESSAGE
    assert f.read() == ''


def test_write_then_read_then_write():
    f = SecureTemporaryFile('/tmp')
    f.write(MESSAGE)
    f.read()

    with pytest.raises(AssertionError) as err:
        f.write('be gentle to each other so we can be dangerous together')
    assert 'You cannot write after reading!' in str(err)


def test_read_write_unicode():
    f = SecureTemporaryFile('/tmp')
    unicode_msg = u'鬼神 Kill Em All 1989'
    f.write(unicode_msg)
    assert f.read().decode('utf-8') == unicode_msg


def test_file_seems_encrypted():
    f = SecureTemporaryFile('/tmp')
    f.write(MESSAGE)
    with io.open(f.filepath, 'rb') as fh:
        contents = fh.read()

    assert MESSAGE.encode('utf-8') not in contents
    assert MESSAGE not in contents.decode()


class TestSecureTempfile(unittest.TestCase):

    def setUp(self):
        self.__context = journalist_app.create_app(config).app_context()
        self.__context.push()
        utils.env.setup()
        self.f = secure_tempfile.SecureTemporaryFile(config.STORE_DIR)
        self.msg = '410,757,864,530'

    def tearDown(self):
        utils.env.teardown()
        self.__context.pop()

    def test_file_is_removed_from_disk(self):
        fp = self.f.filepath
        self.f.write(self.msg)
        self.f.read()

        self.assertTrue(os.path.exists(fp))

        self.f.close()

        self.assertFalse(os.path.exists(fp))

    def test_SecureTemporaryFile_is_a_STREAMLIKE_TYPE(self):
        self.assertTrue(_is_stream(
            secure_tempfile.SecureTemporaryFile('/tmp')))

    def test_buffered_read(self):
        msg = self.msg * 1000
        self.f.write(msg)
        str = ''
        while True:
            char = self.f.read(1024)
            if char:
                str += char
            else:
                break

        self.assertEqual(str, msg)

    def test_tmp_file_id_omits_invalid_chars(self):
        """The `SecureTempFile.tmp_file_id` instance attribute is used as the filename
        for the secure temporary file. This attribute should not contain
        invalid characters such as '/' and '\0' (null)."""
        self.assertNotIn('/', self.f.tmp_file_id)
        self.assertNotIn('\0', self.f.tmp_file_id)
