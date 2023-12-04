# Integration tests for the redwood Python/Sequoia bridge
from io import StringIO

import pytest
from secure_tempfile import SecureTemporaryFile

import redwood

PASSPHRASE = "correcthorsebatterystaple"
SECRET_MESSAGE = "Rust-in-Python is really great 🦀"


@pytest.fixture(scope="session")
def key_pair():
    return redwood.generate_source_key_pair(PASSPHRASE, "foo@example.org")


def test_encrypt_stream(tmp_path, key_pair):
    (public_key, secret_key, fingerprint) = key_pair
    iterations = 100_000  # force a good amount of chunks
    file = tmp_path / "file.asc"
    with SecureTemporaryFile("/tmp") as stf:
        for _ in range(iterations):
            stf.write(SECRET_MESSAGE.encode())

        redwood.encrypt_stream([public_key], stf, file)
    ciphertext = file.read_bytes()
    actual = redwood.decrypt(ciphertext, secret_key, PASSPHRASE)
    assert (SECRET_MESSAGE * iterations) == actual.decode()


class DummyReadable:
    """A fake class with a read() method that fails"""

    def read(self, _len: int) -> None:
        raise RuntimeError("uhoh")


def test_encrypt_stream_bad(tmp_path, key_pair):
    (public_key, secret_key, fingerprint) = key_pair
    not_stream = SECRET_MESSAGE.encode()
    # Passing in a type/object that has no `.read()`
    with pytest.raises(
        redwood.RedwoodError, match="AttributeError: 'bytes' object has no attribute 'read'"
    ):
        redwood.encrypt_stream([public_key], not_stream, tmp_path / "file1.asc")
    # When `.read()` returns something other than bytes
    with pytest.raises(
        redwood.RedwoodError, match="TypeError: 'str' object cannot be converted to 'PyBytes'"
    ):
        redwood.encrypt_stream([public_key], StringIO(SECRET_MESSAGE), tmp_path / "file2.asc")
    with pytest.raises(redwood.RedwoodError, match='error: "RuntimeError: uhoh"'):
        redwood.encrypt_stream([public_key], DummyReadable(), tmp_path / "file3.asc")
