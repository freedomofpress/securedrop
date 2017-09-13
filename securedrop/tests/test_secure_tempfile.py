# -*- coding: utf-8 -*-
import os
import unittest

from gnupg._util import _is_stream

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import config
import secure_tempfile
import utils


class TestSecureTempfile(unittest.TestCase):
    def setUp(self):
        utils.env.setup()
        self.f = secure_tempfile.SecureTemporaryFile(config.STORE_DIR)
        self.msg = '410,757,864,530'

    def tearDown(self):
        utils.env.teardown()

    def test_read_before_writing(self):
        with self.assertRaisesRegexp(AssertionError,
                                     'You must write before reading!'):
            self.f.read()

    def test_write_then_read_once(self):
        self.f.write(self.msg)

        self.assertEqual(self.f.read(), self.msg)

    def test_write_twice_then_read_once(self):
        self.f.write(self.msg)
        self.f.write(self.msg)

        self.assertEqual(self.f.read(), self.msg*2)

    def test_write_then_read_twice(self):
        self.f.write(self.msg)

        self.assertEqual(self.f.read(), self.msg)
        self.assertEqual(self.f.read(), '')

    def test_write_then_read_then_write(self):
        self.f.write(self.msg)
        self.f.read()

        with self.assertRaisesRegexp(AssertionError,
                                     'You cannot write after reading!'):
            self.f.write('BORN TO DIE')

    def test_read_write_unicode(self):
        unicode_msg = u'鬼神 Kill Em All 1989'
        self.f.write(unicode_msg)

        self.assertEqual(self.f.read().decode('utf-8'), unicode_msg)

    def test_file_seems_encrypted(self):
        self.f.write(self.msg)
        with open(self.f.filepath, 'rb') as fh:
            contents = fh.read().decode()

        self.assertNotIn(self.msg, contents)

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
