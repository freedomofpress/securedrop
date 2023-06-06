# -*- coding: utf-8 -*-
#
# This file is part of python-gnupg, a Python interface to GnuPG.
# Copyright © 2013 Isis Lovecruft, <isis@leap.se> 0xA3ADB67A2CDB8B35
#           © 2013 Andrej B.
#           © 2013 LEAP Encryption Access Project
#           © 2008-2012 Vinay Sajip
#           © 2005 Steve Traugott
#           © 2004 A.M. Kuchling
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the included LICENSE file for details.

'''Extra utilities for python-gnupg.'''

from __future__ import absolute_import
from datetime   import datetime
from socket     import gethostname
from time       import localtime
from time       import mktime

import codecs
import encodings
import os
import threading
import random
import re
import string
import sys

# These are all the classes which are stream-like; they are used in
# :func:`_is_stream`.
_STREAMLIKE_TYPES = []

# These StringIO classes are actually utilised.
try:
    import io
    from io import StringIO
    from io import BytesIO
except ImportError:
    from cStringIO import StringIO
else:
    # The io.IOBase type covers the above example for an open file handle in
    # Python3, as well as both io.BytesIO and io.StringIO.
    _STREAMLIKE_TYPES.append(io.IOBase)

# The remaining StringIO classes which are imported are used to determine if a
# object is a stream-like in :func:`_is_stream`.
if 2 == sys.version_info[0]:
    # Import the StringIO class from the StringIO module since it is a
    # commonly used stream class. It is distinct from either of the
    # StringIO's that may be loaded in the above try/except clause, so the
    # name is prefixed with an underscore to distinguish it.
    from StringIO import StringIO as _StringIO_StringIO
    _STREAMLIKE_TYPES.append(_StringIO_StringIO)

    # Import the cStringIO module to test for the cStringIO stream types,
    # InputType and OutputType. See
    # http://stackoverflow.com/questions/14735295/to-check-an-instance-is-stringio
    import cStringIO as _cStringIO
    _STREAMLIKE_TYPES.append(_cStringIO.InputType)
    _STREAMLIKE_TYPES.append(_cStringIO.OutputType)

    # In Python2:
    #
    #     >>> type(open('README.md', 'rb'))
    #     <open file 'README.md', mode 'rb' at 0x7f9493951d20>
    #
    # whereas, in Python3, the `file` builtin doesn't exist and instead we get:
    #
    #     >>> type(open('README.md', 'rb'))
    #     <_io.BufferedReader name='README.md'>
    #
    # which is covered by the above addition of io.IOBase.
    _STREAMLIKE_TYPES.append(file)


from . import _logger


try:
    unicode
    _py3k = False
    try:
        isinstance(__name__, basestring)
    except NameError:
        msg  = "Sorry, python-gnupg requires a Python version with proper"
        msg += " unicode support. Please upgrade to Python>=2.6."
        raise SystemExit(msg)
except NameError:
    _py3k = True

_running_windows = sys.platform.startswith("win")

## Directory shortcuts:
## we don't want to use this one because it writes to the install dir:
#_here = getabsfile(currentframe()).rsplit(os.path.sep, 1)[0]
_here = os.path.join(os.getcwd(), 'pretty_bad_protocol')     ## current dir
_test = os.path.join(os.path.join(_here, 'test'), 'tmp')     ## ./tests/tmp
_user = os.environ.get('HOME')                               ## $HOME

# Fix for Issue #74: we shouldn't expect that a $HOME directory is set in all
# environs. https://github.com/isislovecruft/python-gnupg/issues/74
if not _user:
    _user = '/tmp/python-gnupg'
    try:
        os.makedirs(_user)
    except (OSError, IOError):
        _user = os.getcwd()
    # If we can't use $HOME, but we have (or can create) a
    # /tmp/python-gnupg/gnupghome directory, then we'll default to using
    # that. Otherwise, we'll use the current directory + /gnupghome.
    _user = os.path.sep.join([_user, 'gnupghome'])

_ugpg = os.path.join(_user, '.gnupg')                        ## $HOME/.gnupg
_conf = os.path.join(os.path.join(_user, '.config'), 'python-gnupg')
                                     ## $HOME/.config/python-gnupg

## Logger is disabled by default
log = _logger.create_logger(0)

#: Compiled regex for determining a GnuPG binary's version:
_VERSION_STRING_REGEX = re.compile('(\d)(\.)(\d)(\.)(\d+)')


class GnuPGVersionError(ValueError):
    """Raised when we couldn't parse GnuPG's version info."""


def find_encodings(enc=None, system=False):
    """Find functions for encoding translations for a specific codec.

    :param str enc: The codec to find translation functions for. It will be
                    normalized by converting to lowercase, excluding
                    everything which is not ascii, and hyphens will be
                    converted to underscores.

    :param bool system: If True, find encodings based on the system's stdin
                        encoding, otherwise assume utf-8.

    :raises: :exc:LookupError if the normalized codec, ``enc``, cannot be
             found in Python's encoding translation map.
    """
    if not enc:
        enc = 'utf-8'

    if system:
        if getattr(sys.stdin, 'encoding', None) is None:
            enc = sys.stdin.encoding
            log.debug("Obtained encoding from stdin: %s" % enc)
        else:
            enc = 'ascii'

    ## have to have lowercase to work, see
    ## http://docs.python.org/dev/library/codecs.html#standard-encodings
    enc = enc.lower()
    codec_alias = encodings.normalize_encoding(enc)

    codecs.register(encodings.search_function)
    coder = codecs.lookup(codec_alias)

    return coder


if _py3k:
    def b(x):
        """See http://python3porting.com/problems.html#nicer-solutions"""
        coder = find_encodings()
        if isinstance(x, bytes):
            return coder.encode(x.decode(coder.name))[0]
        else:
            return coder.encode(x)[0]

    def s(x):
        if isinstance(x, str):
            return x
        elif isinstance(x, (bytes, bytearray)):
            return x.decode(find_encodings().name)
        else:
            raise NotImplemented
else:
    def b(x):
        """See http://python3porting.com/problems.html#nicer-solutions"""
        return x

    def s(x):
        if isinstance(x, basestring):
            return x
        elif isinstance(x, (bytes, bytearray)):
            return x.decode(find_encodings().name)
        else:
            raise NotImplemented

def binary(data):
    coder = find_encodings()

    if _py3k and isinstance(data, str):
        encoded = coder.encode(data)[0]
    elif not _py3k and type(data) is not str:
        encoded = coder.encode(data)[0]
    else:
        encoded = data

    return encoded


def author_info(name, contact=None, public_key=None):
    """Easy object-oriented representation of contributor info.

    :param str name: The contributor´s name.
    :param str contact: The contributor´s email address or contact
                        information, if given.
    :param str public_key: The contributor´s public keyid, if given.
    """
    return Storage(name=name, contact=contact, public_key=public_key)

def _copy_data(instream, outstream):
    """Copy data from one stream to another.

    :type instream: :class:`io.BytesIO` or :class:`io.StringIO` or file
    :param instream: A byte stream or open file to read from.
    :param file outstream: The file descriptor of a tmpfile to write to.
    """
    sent = 0

    while True:
        if ((_py3k and isinstance(instream, str)) or
            (not _py3k and isinstance(instream, basestring))):
            data = instream[:1024]
            instream = instream[1024:]
        else:
            data = instream.read(1024)
        if len(data) == 0:
            break

        sent += len(data)
        if ((_py3k and isinstance(data, str)) or
            (not _py3k and isinstance(data, basestring))):
            encoded = binary(data)
        else:
            encoded = data
        log.debug("Sending %d bytes of data..." % sent)
        log.debug("Encoded data (type %s):\n%s" % (type(encoded), encoded))

        if not _py3k:
            try:
                outstream.write(encoded)
            except IOError as ioe:
                # Can get 'broken pipe' errors even when all data was sent
                if 'Broken pipe' in str(ioe):
                    log.error('Error sending data: Broken pipe')
                else:
                    log.exception(ioe)
                break
            else:
                log.debug("Wrote data type <type 'str'> to outstream.")
        else:
            try:
                outstream.write(bytes(encoded))
            except TypeError as te:
                # XXX FIXME This appears to happen because
                # _threaded_copy_data() sometimes passes the `outstream` as an
                # object with type <_io.BufferredWriter> and at other times
                # with type <encodings.utf_8.StreamWriter>.  We hit the
                # following error when the `outstream` has type
                # <encodings.utf_8.StreamWriter>.
                if not "convert 'bytes' object to str implicitly" in str(te):
                    log.error(str(te))
                try:
                    outstream.write(encoded.decode())
                except TypeError as yate:
                    # We hit the "'str' does not support the buffer interface"
                    # error in Python3 when the `outstream` is an io.BytesIO and
                    # we try to write a str to it.  We don't care about that
                    # error, we'll just try again with bytes.
                    if not "does not support the buffer interface" in str(yate):
                        log.error(str(yate))
                except IOError as ioe:
                    # Can get 'broken pipe' errors even when all data was sent
                    if 'Broken pipe' in str(ioe):
                        log.error('Error sending data: Broken pipe')
                    else:
                        log.exception(ioe)
                    break
                else:
                    log.debug("Wrote data type <class 'str'> outstream.")
            except IOError as ioe:
                # Can get 'broken pipe' errors even when all data was sent
                if 'Broken pipe' in str(ioe):
                    log.error('Error sending data: Broken pipe')
                else:
                    log.exception(ioe)
                break
            else:
                log.debug("Wrote data type <class 'bytes'> to outstream.")

    try:
        outstream.close()
    except IOError as ioe:
        log.error("Unable to close outstream %s:\r\t%s" % (outstream, ioe))
    else:
        log.debug("Closed outstream: %d bytes sent." % sent)

def _create_if_necessary(directory):
    """Create the specified directory, if necessary.

    :param str directory: The directory to use.
    :rtype: bool
    :returns: True if no errors occurred and the directory was created or
              existed beforehand, False otherwise.
    """

    if not os.path.isabs(directory):
        log.debug("Got non-absolute path: %s" % directory)
        directory = os.path.abspath(directory)

    if not os.path.isdir(directory):
        log.info("Creating directory: %s" % directory)
        try:
            os.makedirs(directory, 0x1C0)
        except OSError as ose:
            log.error(ose, exc_info=1)
            return False
        else:
            log.debug("Created directory.")
    return True

def create_uid_email(username=None, hostname=None):
    """Create an email address suitable for a UID on a GnuPG key.

    :param str username: The username portion of an email address.  If None,
                         defaults to the username of the running Python
                         process.

    :param str hostname: The FQDN portion of an email address. If None, the
                         hostname is obtained from gethostname(2).

    :rtype: str
    :returns: A string formatted as <username>@<hostname>.
    """
    if hostname:
        hostname = hostname.replace(' ', '_')
    if not username:
        try: username = os.environ['LOGNAME']
        except KeyError: username = os.environ['USERNAME']

        if not hostname: hostname = gethostname()

        uid = "%s@%s" % (username.replace(' ', '_'), hostname)
    else:
        username = username.replace(' ', '_')
        if (not hostname) and (username.find('@') == 0):
            uid = "%s@%s" % (username, gethostname())
        elif hostname:
            uid = "%s@%s" % (username, hostname)
        else:
            uid = username

    return uid

def _deprefix(line, prefix, callback=None):
    """Remove the prefix string from the beginning of line, if it exists.

    :param string line: A line, such as one output by GnuPG's status-fd.
    :param string prefix: A substring to remove from the beginning of
        ``line``. Case insensitive.
    :type callback: callable
    :param callback: Function to call if the prefix is found. The signature to
        callback will be only one argument, the ``line`` without the ``prefix``, i.e.
        ``callback(line)``.
    :rtype: string
    :returns: If the prefix was found, the ``line`` without the prefix is
        returned. Otherwise, the original ``line`` is returned.
    """
    try:
        assert line.upper().startswith(u''.join(prefix).upper())
    except AssertionError:
        log.debug("Line doesn't start with prefix '%s':\n%s" % (prefix, line))
        return line
    else:
        newline = line[len(prefix):]
        if callback is not None:
            try:
                callback(newline)
            except Exception as exc:
                log.exception(exc)
        return newline

def _find_binary(binary=None):
    """Find the absolute path to the GnuPG binary.

    Also run checks that the binary is not a symlink, and check that
    our process real uid has exec permissions.

    :param str binary: The path to the GnuPG binary.
    :raises: :exc:`~exceptions.RuntimeError` if it appears that GnuPG is not
             installed.
    :rtype: str
    :returns: The absolute path to the GnuPG binary to use, if no exceptions
              occur.
    """
    found = None
    if binary is not None:
        if os.path.isabs(binary) and os.path.isfile(binary):
            return binary
        if not os.path.isabs(binary):
            try:
                found = _which(binary)
                log.debug("Found potential binary paths: %s"
                          % '\n'.join([path for path in found]))
                found = found[0]
            except IndexError as ie:
                log.info("Could not determine absolute path of binary: '%s'"
                          % binary)
        elif os.access(binary, os.X_OK):
            found = binary
    if found is None:
        try: found = _which('gpg', abspath_only=True, disallow_symlinks=True)[0]
        except IndexError as ie:
            log.error("Could not find binary for 'gpg'.")
            try: found = _which('gpg2')[0]
            except IndexError as ie:
                log.error("Could not find binary for 'gpg2'.")
    if found is None:
        raise RuntimeError("GnuPG is not installed!")

    return found

def _has_readwrite(path):
    """
    Determine if the real uid/gid of the executing user has read and write
    permissions for a directory or a file.

    :param str path: The path to the directory or file to check permissions
                     for.
    :rtype: bool
    :returns: True if real uid/gid has read+write permissions, False otherwise.
    """
    return os.access(path, os.R_OK | os.W_OK)

def _is_file(filename):
    """Check that the size of the thing which is supposed to be a filename has
    size greater than zero, without following symbolic links or using
    :func:os.path.isfile.

    :param filename: An object to check.
    :rtype: bool
    :returns: True if **filename** is file-like, False otherwise.
    """
    try:
        statinfo = os.lstat(filename)
        log.debug("lstat(%r) with type=%s gave us %r"
                  % (repr(filename), type(filename), repr(statinfo)))
        if not (statinfo.st_size > 0):
            raise ValueError("'%s' appears to be an empty file!" % filename)
    except OSError as oserr:
        log.error(oserr)
        if filename == '-':
            log.debug("Got '-' for filename, assuming sys.stdin...")
            return True
    except (ValueError, TypeError, IOError) as err:
        log.error(err)
    else:
        return True
    return False

def _is_stream(input):
    """Check that the input is a byte stream.

    :param input: An object provided for reading from or writing to.
    :rtype: bool
    :returns: True if :param:input is a stream, False if otherwise.
    """
    return isinstance(input, tuple(_STREAMLIKE_TYPES))

def _is_string(thing):
    """Check that **thing** is a string. The definition of the latter depends
    upon the Python version.

    :param thing: The thing to check if it's a string.
    :rtype: bool
    :returns: ``True`` if **thing** is string (or unicode in Python2).
    """
    if (_py3k and isinstance(thing, str)):
        return True
    if (not _py3k and isinstance(thing, basestring)):
        return True
    return False

def _is_bytes(thing):
    """Check that **thing** is bytes.

    :param thing: The thing to check if it's bytes.
    :rtype: bool
    :returns: ``True`` if **thing** is bytes or a bytearray.
    """
    if isinstance(thing, (bytes, bytearray)):
        return True
    return False

def _is_list_or_tuple(instance):
    """Check that ``instance`` is a list or tuple.

    :param instance: The object to type check.
    :rtype: bool
    :returns: True if ``instance`` is a list or tuple, False otherwise.
    """
    return isinstance(instance, (list, tuple,))

def _is_gpg1(version):
    """Returns True if using GnuPG version 1.x.

    :param tuple version: A tuple of three integers indication major, minor,
        and micro version numbers.
    """
    (major, minor, micro) = _match_version_string(version)
    if major == 1:
        return True
    return False

def _is_gpg2(version):
    """Returns True if using GnuPG version 2.x.

    :param tuple version: A tuple of three integers indication major, minor,
        and micro version numbers.
    """
    (major, minor, micro) = _match_version_string(version)
    if major == 2:
        return True
    return False

def _make_binary_stream(thing, encoding=None, armor=True):
    """Encode **thing**, then make it stream/file-like.

    :param thing: The thing to turn into a encoded stream.
    :rtype: ``io.BytesIO`` or ``io.StringIO``.
    :returns: The encoded **thing**, wrapped in an ``io.BytesIO`` (if
        available), otherwise wrapped in a ``io.StringIO``.
    """
    if _py3k:
        if isinstance(thing, str):
            thing = thing.encode(encoding)
    else:
        if type(thing) is not str:
            thing = thing.encode(encoding)

    try:
        rv = BytesIO(thing)
    except NameError:
        rv = StringIO(thing)

    return rv

def _make_passphrase(length=None, save=False, file=None):
    """Create a passphrase and write it to a file that only the user can read.

    This is not very secure, and should not be relied upon for actual key
    passphrases.

    :param int length: The length in bytes of the string to generate.

    :param file file: The file to save the generated passphrase in. If not
        given, defaults to 'passphrase-<the real user id>-<seconds since
        epoch>' in the top-level directory.
    """
    if not length:
        length = 40

    passphrase = _make_random_string(length)

    if save:
        ruid, euid, suid = os.getresuid()
        gid = os.getgid()
        now = mktime(localtime())

        if not file:
            filename = str('passphrase-%s-%s' % uid, now)
            file = os.path.join(_repo, filename)

        with open(file, 'a') as fh:
            fh.write(passphrase)
            fh.flush()
            fh.close()
            os.chmod(file, stat.S_IRUSR | stat.S_IWUSR)
            os.chown(file, ruid, gid)

        log.warn("Generated passphrase saved to %s" % file)
    return passphrase

def _make_random_string(length):
    """Returns a random lowercase, uppercase, alphanumerical string.

    :param int length: The length in bytes of the string to generate.
    """
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for x in range(length))

def _match_version_string(version):
    """Sort a binary version string into major, minor, and micro integers.

    :param str version: A version string in the form x.x.x
    :raises GnuPGVersionError: if the **version** string couldn't be parsed.
    :rtype: tuple

    :returns: A 3-tuple of integers, representing the (MAJOR, MINOR, MICRO)
        version numbers. For example::

            _match_version_string("2.1.3")

        would return ``(2, 1, 3)``.
    """
    matched = _VERSION_STRING_REGEX.match(version)
    g = matched.groups()
    major, minor, micro = g[0], g[2], g[4]

    # If, for whatever reason, the binary didn't tell us its version, then
    # these might be (None, None, None), and so we should avoid typecasting
    # them when that is the case.
    if major and minor and micro:
        major, minor, micro = int(major), int(minor), int(micro)
    else:
        raise GnuPGVersionError("Could not parse GnuPG version from: %r" %
                                version)

    return (major, minor, micro)

def _next_year():
    """Get the date of today plus one year.

    :rtype: str
    :returns: The date of this day next year, in the format '%Y-%m-%d'.
    """
    now = datetime.now().__str__()
    date = now.split(' ', 1)[0]
    year, month, day = date.split('-', 2)
    next_year = str(int(year)+1)
    return '-'.join((next_year, month, day))

def _now():
    """Get a timestamp for right now, formatted according to ISO 8601."""
    return datetime.isoformat(datetime.now())

def _separate_keyword(line):
    """Split the line, and return (first_word, the_rest)."""
    try:
        first, rest = line.split(None, 1)
    except ValueError:
        first = line.strip()
        rest = ''
    return first, rest

def _threaded_copy_data(instream, outstream):
    """Copy data from one stream to another in a separate thread.

    Wraps ``_copy_data()`` in a :class:`threading.Thread`.

    :type instream: :class:`io.BytesIO` or :class:`io.StringIO`
    :param instream: A byte stream to read from.
    :param file outstream: The file descriptor of a tmpfile to write to.
    """
    copy_thread = threading.Thread(target=_copy_data,
                                   args=(instream, outstream))
    copy_thread.setDaemon(True)
    log.debug('%r, %r, %r', copy_thread, instream, outstream)
    copy_thread.start()
    return copy_thread

def _utc_epoch():
    """Get the seconds since epoch."""
    return int(mktime(localtime()))

def _which(executable, flags=os.X_OK, abspath_only=False, disallow_symlinks=False):
    """Borrowed from Twisted's :mod:twisted.python.proutils .

    Search PATH for executable files with the given name.

    On newer versions of MS-Windows, the PATHEXT environment variable will be
    set to the list of file extensions for files considered executable. This
    will normally include things like ".EXE". This fuction will also find files
    with the given name ending with any of these extensions.

    On MS-Windows the only flag that has any meaning is os.F_OK. Any other
    flags will be ignored.

    Note: This function does not help us prevent an attacker who can already
    manipulate the environment's PATH settings from placing malicious code
    higher in the PATH. It also does happily follows links.

    :param str name: The name for which to search.
    :param int flags: Arguments to L{os.access}.
    :rtype: list
    :returns: A list of the full paths to files found, in the order in which
              they were found.
    """
    def _can_allow(p):
        if not os.access(p, flags):
            return False
        if abspath_only and not os.path.abspath(p):
            log.warn('Ignoring %r (path is not absolute)', p)
            return False
        if disallow_symlinks and os.path.islink(p):
            log.warn('Ignoring %r (path is a symlink)', p)
            return False
        return True

    result = []
    exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
    path = os.environ.get('PATH', None)
    if path is None:
        return []
    for p in os.environ.get('PATH', '').split(os.pathsep):
        p = os.path.join(p, executable)
        if _can_allow(p):
            result.append(p)
        for e in exts:
            pext = p + e
            if _can_allow(pext):
                result.append(pext)
    return result

def _write_passphrase(stream, passphrase, encoding):
    """Write the passphrase from memory to the GnuPG process' stdin.

    :type stream: file, :class:`~io.BytesIO`, or :class:`~io.StringIO`
    :param stream: The input file descriptor to write the password to.
    :param str passphrase: The passphrase for the secret key material.
    :param str encoding: The data encoding expected by GnuPG. Usually, this
                         is ``sys.getfilesystemencoding()``.
    """
    passphrase = '%s\n' % passphrase
    passphrase = passphrase.encode(encoding)
    stream.write(passphrase)
    log.debug("Wrote passphrase on stdin.")


class InheritableProperty(object):
    """Based on the emulation of PyProperty_Type() in Objects/descrobject.c"""

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        if self.fget.__name__ == '<lambda>' or not self.fget.__name__:
            return self.fget(obj)
        else:
            return getattr(obj, self.fget.__name__)()

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        if self.fset.__name__ == '<lambda>' or not self.fset.__name__:
            self.fset(obj, value)
        else:
            getattr(obj, self.fset.__name__)(value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        if self.fdel.__name__ == '<lambda>' or not self.fdel.__name__:
            self.fdel(obj)
        else:
            getattr(obj, self.fdel.__name__)()


class Storage(dict):
    """A dictionary where keys are stored as class attributes.

    For example, ``obj.foo`` can be used in addition to ``obj['foo']``:

        >>> o = Storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        None
    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as k:
            return None

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k.args[0])

    def __repr__(self):
        return '<Storage ' + dict.__repr__(self) + '>'

    def __getstate__(self):
        return dict(self)

    def __setstate__(self, value):
        for (k, v) in value.items():
            self[k] = v
