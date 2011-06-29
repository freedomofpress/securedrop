import hmac, hashlib, subprocess
import gnupg
import config

BITS_IN_RANDOM_ID = 256
HASH_FUNCTION = hashlib.sha256
GPG_KEY_TYPE = "RSA"
GPG_KEY_LENGTH = "4096"

def genrandomid():
    return hex(random.getrandbits(BITS_IN_RANDOM_ID))[2:-1]

def shash(s):
    """
    >>> shash('Hello, world!')
    '98015b0fbf815a630cbcda94b809d207490d7cc2c5c02cb33a242acfd5b73cc1'
    """
    return hmac.HMAC(config.HMAC_SECRET, s, HASH_FUNCTION).hexdigest()

gpg = gnupg.GPG(gnupghome=config.GPG_KEY_DIR)

def genkeypair(name, secret):
    """
    >>> if not gpg.list_keys(shash('randomid')):
    ...     genkeypair(shash('randomid'), 'randomid').type
    ... else:
    ...     u'P'
    u'P'
    """
    return gpg.gen_key(gpg.gen_key_input(
      key_type=GPG_KEY_TYPE, key_length=GPG_KEY_LENGTH,
      passphrase=secret,
      name_email="%s@wireleaks.example.com" % name
    ))

def encrypt(name, s):
    """
    >>> encrypt(shash('randomid'), "Goodbye, cruel world!")[:75]
    '-----BEGIN PGP MESSAGE-----\\nVersion: GnuPG v1.4.9 (Darwin)\\n\\nhQIMA3rf0hDNFTT'
    """
    fp = gpg.list_keys(name)[0]['fingerprint']
    if isinstance(s, unicode):
        s = s.encode('utf8')
    if isinstance(s, str):
        out = gpg.encrypt(s, [fp])
    else:
        out = gpg.encrypt_file(s, [fp])
    return out.data

def decrypt(name, secret, s):
    """
    >>> decrypt(shash('randomid'), 'randomid',
    ...   encrypt(shash('randomid'), 'Goodbye, cruel world!')
    ... )
    'Goodbye, cruel world!'
    """
    return gpg.decrypt(s, passphrase=secret).data

def secureunlink(fn):
    return subprocess.check_call(['srm', fn])

if __name__ == "__main__":
    import doctest
    doctest.testmod()
