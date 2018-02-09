# -*- coding: utf-8 -*-
import base64
import os
from tempfile import _TemporaryFileWrapper

from gnupg._util import _STREAMLIKE_TYPES
from Cryptodome.Cipher import AES
from Cryptodome.Random import random
from Cryptodome.Util import Counter


class SecureTemporaryFile(_TemporaryFileWrapper, object):
    """Temporary file that provides on-the-fly encryption.

    Buffering large submissions in memory as they come in requires too
    much memory for too long a period. By writing the file to disk as it
    comes in using a stream cipher, we are able to minimize memory usage
    as submissions come in, while minimizing the chances of plaintext
    recovery through forensic disk analysis. They key used to encrypt
    each secure temporary file is also ephemeral, and is only stored in
    memory only for as long as needed.

    Adapted from Globaleaks' GLSecureTemporaryFile:
    https://github.com/globaleaks/GlobaLeaks/blob/master/backend/globaleaks/security.py#L35

    WARNING: you can't use this like a normal file object. It supports
    being appended to however many times you wish (although content may not be
    overwritten), and then it's contents may be read only once (although it may
    be done in chunks) and only after it's been written to.
    """
    AES_key_size = 256
    AES_block_size = 128

    def __init__(self, store_dir):
        """Generates an AES key and an initialization vector, and opens
        a file in the `store_dir` directory with a
        pseudorandomly-generated filename.

        Args:
            store_dir (str): the directory to create the secure
                temporary file under.

        Returns: self
        """
        self.last_action = 'init'
        self.create_key()
        self.tmp_file_id = base64.urlsafe_b64encode(os.urandom(32)).strip('=')
        self.filepath = os.path.join(store_dir,
                                     '{}.aes'.format(self.tmp_file_id))
        self.file = open(self.filepath, 'w+b')
        super(SecureTemporaryFile, self).__init__(self.file, self.filepath)

    def create_key(self):
        """Generates a unique, pseudorandom AES key, stored ephemerally in
        memory as an instance attribute. Its destruction is ensured by the
        automatic nightly reboots of the SecureDrop application server combined
        with the freed memory-overwriting PAX_MEMORY_SANITIZE feature of the
        grsecurity-patched kernel it uses (for further details consult
        https://github.com/freedomofpress/securedrop/pull/477#issuecomment-168445450).
        """
        self.key = os.urandom(self.AES_key_size / 8)
        self.iv = random.getrandbits(self.AES_block_size)
        self.initialize_cipher()

    def initialize_cipher(self):
        """Creates the cipher-related objects needed for AES-CTR
        encryption and decryption.
        """
        self.ctr_e = Counter.new(self.AES_block_size, initial_value=self.iv)
        self.ctr_d = Counter.new(self.AES_block_size, initial_value=self.iv)
        self.encryptor = AES.new(self.key, AES.MODE_CTR, counter=self.ctr_e)
        self.decryptor = AES.new(self.key, AES.MODE_CTR, counter=self.ctr_d)

    def write(self, data):
        """Write `data` to the secure temporary file. This method may be
        called any number of times following instance initialization,
        but after calling :meth:`read`, you cannot write to the file
        again.
        """
        if self.last_action == 'read':
            raise AssertionError('You cannot write after reading!')
        self.last_action = 'write'

        if isinstance(data, unicode):  # noqa
            data = data.encode('utf-8')

        self.file.write(self.encryptor.encrypt(data))

    def read(self, count=None):
        """Read `data` from the secure temporary file. This method may
        be called any number of times following instance initialization
        and once :meth:`write has been called at least once, but not
        before.

        Before the first read operation, `seek(0, 0)` is called. So
        while you can call this method any number of times, the full
        contents of the file can only be read once. Additional calls to
        read will return an empty str, which is desired behavior in that
        it matches :class:`file` and because other modules depend on
        this behavior to let them know they've reached the end of the
        file.

        Args:
            count (int): the number of bytes to try to read from the
                file from the current position.
        """
        if self.last_action == 'init':
            raise AssertionError('You must write before reading!')
        if self.last_action == 'write':
            self.seek(0, 0)
            self.last_action = 'read'

        if count:
            return self.decryptor.decrypt(self.file.read(count))
        else:
            return self.decryptor.decrypt(self.file.read())


# python-gnupg will not recognize our SecureTemporaryFile as a stream-like type
# and will attempt to call encode on it, thinking it's a string-like type. To
# avoid this we append it the list of stream-like types.
_STREAMLIKE_TYPES.append(_TemporaryFileWrapper)
