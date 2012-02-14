import hmac, hashlib, subprocess, random
myrandom = random.SystemRandom()
import gnupg
import config

WORDS_IN_RANDOM_ID = 2
WORD_LIST = 'wordlist'
HASH_FUNCTION = hashlib.sha256
GPG_KEY_TYPE = "RSA"
GPG_KEY_LENGTH = "4096"

class CryptoException(Exception): pass

def clean(s):
    """
    >>> clean("Hello, world!")
    Traceback (most recent call last):
      ...
    CryptoException: invalid input
    >>> clean("Helloworld")
    'Helloworld'
    """
    ok = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    for c in s:
        if c not in ok: raise CryptoException("invalid input")
    return s

words = file(WORD_LIST).read().split('\n')
def genrandomid():
    return ' '.join(myrandom.choice(words) for x in range(WORDS_IN_RANDOM_ID))

def shash(s):
    """
    >>> shash('Hello, world!')
    '98015b0fbf815a630cbcda94b809d207490d7cc2c5c02cb33a242acfd5b73cc1'
    """
    return hmac.HMAC(config.HMAC_SECRET, s, HASH_FUNCTION).hexdigest()

GPG_BINARY = 'gpg2'
try:
    p = subprocess.Popen([GPG_BINARY, '--version'], stdout=subprocess.PIPE)
except OSError:
    GPG_BINARY = 'gpg'
    p = subprocess.Popen([GPG_BINARY, '--version'], stdout=subprocess.PIPE)

assert p.stdout.readline().split()[-1].split('.')[0] == '2', "upgrade GPG to 2.0"
gpg = gnupg.GPG(gpgbinary=GPG_BINARY, gnupghome=config.GPG_KEY_DIR)

def genkeypair(name, secret):
    """
    >>> if not gpg.list_keys(shash('randomid')):
    ...     genkeypair(shash('randomid'), 'randomid').type
    ... else:
    ...     u'P'
    u'P'
    """
    name, secret = clean(name), clean(secret)
    return gpg.gen_key(gpg.gen_key_input(
      key_type=GPG_KEY_TYPE, key_length=GPG_KEY_LENGTH,
      passphrase=secret,
      name_email="%s@deaddrop.example.com" % name
    ))

def getkey(name):
    for key in gpg.list_keys():
        for uid in key['uids']:
            if ' <%s@' % name in uid: return key['fingerprint']
    return None

def encrypt(fp, s, output=None):
    r"""
    >>> encrypt(shash('randomid'), "Goodbye, cruel world!")[:75]
    '-----BEGIN PGP MESSAGE-----\nVersion: GnuPG/MacGPG2 v2.0.17 (Darwin)\n\nhQIMA3'
    """
    fp = fp.replace(' ', '')
    if isinstance(s, unicode):
        s = s.encode('utf8')
    if isinstance(s, str):
        out = gpg.encrypt(s, [fp], output=output, always_trust=True)
    else:
        out = gpg.encrypt_file(s, [fp], output=output, always_trust=True)
    if out.ok:
        return out.data
    else:
        raise CryptoException(out.stderr)

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

# crash if we don't have srm:
subprocess.check_call(['srm', '--version'], stdout=subprocess.PIPE)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
