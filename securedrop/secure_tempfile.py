import base64
import os
from tempfile import _TemporaryFileWrapper

from Crypto.Cipher import AES
from Crypto.Random import random
from Crypto.Util import Counter

class SecureTemporaryFile(_TemporaryFileWrapper):
    """Temporary file that is ephemerally encrypted on the fly.

    Since only encrypted data is ever written to disk, using this
    classes minimizes the chances of plaintext recovery through
    forensic disk analysis.

    Adapated from Globaleaks' GLSecureTemporaryFile: https://github.com/globaleaks/GlobaLeaks/blob/master/backend/globaleaks/security.py#L35

    WARNING: you can't use this like a normal file object. It supports
    being written to exactly once, then read from exactly once.
    """

    AES_key_size = 256
    AES_block_size = 128

    def __init__(self, store_dir):
        self.last_action = 'init'
        self.create_key()

        self.tmp_file_id = base64.urlsafe_b64encode(os.urandom(32)).strip('=')
        self.filepath = os.path.join(store_dir, "{}.aes".format(self.tmp_file_id))
        self.file = open(self.filepath, 'w+b')

        _TemporaryFileWrapper.__init__(self, self.file, self.filepath, delete=True)

    def create_key(self):
        """
        Randomly generate an AES key to encrypt the file
        """
        self.key = os.urandom(self.AES_key_size / 8)
        self.iv  = random.getrandbits(self.AES_block_size)
        self.initialize_cipher()

    def initialize_cipher(self):
        self.ctr_e = Counter.new(self.AES_block_size, initial_value=self.iv)
        self.ctr_d = Counter.new(self.AES_block_size, initial_value=self.iv)
        self.encryptor = AES.new(self.key, AES.MODE_CTR, counter=self.ctr_e)
        self.decryptor = AES.new(self.key, AES.MODE_CTR, counter=self.ctr_d)

    def write(self, data):
        """
        We track the internal status and don't allow writing after reading.
        It might be possible to be smarter about this.
        """
        assert self.last_action != 'read', "You cannot write after read!"
        self.last_action = 'write'

        try:
            if isinstance(data, unicode):
                data = data.encode('utf-8')
            self.file.write(self.encryptor.encrypt(data))
        except Exception as err:
            raise err

    def read(self, count=None):
        """
        The first time 'read' is called after a write, automatically seek(0).
        """
        if self.last_action == 'write':
            self.seek(0, 0)
            self.last_action = 'read'

        if count is None:
            return self.decryptor.decrypt(self.file.read())
        else:
            return self.decryptor.decrypt(self.file.read(count))

    def close(self):
        return _TemporaryFileWrapper.close(self)

