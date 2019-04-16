# -*- coding: utf-8 -*-
import io
import os
import six
import pytest

from pretty_bad_protocol._util import _is_stream

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
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
    assert f.read().decode('utf-8') == MESSAGE


def test_write_twice_then_read_once():
    f = SecureTemporaryFile('/tmp')
    f.write(MESSAGE)
    f.write(MESSAGE)
    assert f.read().decode('utf-8') == MESSAGE * 2


def test_write_then_read_twice():
    f = SecureTemporaryFile('/tmp')
    f.write(MESSAGE)
    assert f.read().decode('utf-8') == MESSAGE
    assert f.read() == b''


def test_write_then_read_then_write():
    f = SecureTemporaryFile('/tmp')
    f.write(MESSAGE)
    f.read()

    with pytest.raises(AssertionError) as err:
        f.write('be gentle to each other so we can be dangerous together')
    assert 'You cannot write after reading!' in str(err)


def test_read_write_unicode():
    f = SecureTemporaryFile('/tmp')
    unicode_msg = six.u('鬼神 Kill Em All 1989')
    f.write(unicode_msg)
    assert f.read().decode('utf-8') == unicode_msg


def test_file_seems_encrypted():
    f = SecureTemporaryFile('/tmp')
    f.write(MESSAGE)
    with io.open(f.filepath, 'rb') as fh:
        contents = fh.read()

    assert MESSAGE.encode('utf-8') not in contents
    assert MESSAGE not in contents.decode()


def test_file_is_removed_from_disk():
    # once without reading the contents
    f = SecureTemporaryFile('/tmp')
    f.write(MESSAGE)
    assert os.path.exists(f.filepath)
    f.close()
    assert not os.path.exists(f.filepath)

    # once with reading the contents
    f = SecureTemporaryFile('/tmp')
    f.write(MESSAGE)
    f.read()
    assert os.path.exists(f.filepath)
    f.close()
    assert not os.path.exists(f.filepath)


def test_SecureTemporaryFile_is_a_STREAMLIKE_TYPE():
    assert _is_stream(SecureTemporaryFile('/tmp'))


def test_buffered_read():
    f = SecureTemporaryFile('/tmp')
    msg = MESSAGE * 1000
    f.write(msg)
    out = b''
    while True:
        chars = f.read(1024)
        if chars:
            out += chars
        else:
            break

    assert out.decode('utf-8') == msg


def test_tmp_file_id_omits_invalid_chars():
    """The `SecureTempFile.tmp_file_id` instance attribute is used as the filename
    for the secure temporary file. This attribute should not contain
    invalid characters such as '/' and '\0' (null)."""
    f = SecureTemporaryFile('/tmp')
    assert '/' not in f.tmp_file_id
    assert '\0' not in f.tmp_file_id
