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

'''Meta and base classes for hiding internal functions, and controlling
attribute creation and handling.
'''

from __future__ import absolute_import

import atexit
import codecs
import encodings
## For AOS, the locale module will need to point to a wrapper around the
## java.util.Locale class.
## See https://code.patternsinthevoid.net/?p=android-locale-hack.git
import locale
import os
import platform
import re
import shlex
import subprocess
import sys
import threading

## Using psutil is recommended, but since the extension doesn't run with the
## PyPy interpreter, we'll run even if it's not present.
try:
    import psutil
except ImportError:
    psutil = None

from . import _parsers
from . import _util
from ._util import b
from ._util import s

from ._parsers import _check_preferences
from ._parsers import _sanitise_list
from ._util    import log

_VERSION_RE = re.compile('^\d+\.\d+\.\d+$')


class GPGMeta(type):
    """Metaclass for changing the :meth:GPG.__init__ initialiser.

    Detects running gpg-agent processes and the presence of a pinentry
    program, and disables pinentry so that python-gnupg can write the
    passphrase to the controlled GnuPG process without killing the agent.

    :attr _agent_proc: If a :program:`gpg-agent` process is currently running
                       for the effective userid, then **_agent_proc** will be
                       set to a ``psutil.Process`` for that process.
    """

    def __new__(cls, name, bases, attrs):
        """Construct the initialiser for GPG"""
        log.debug("Metaclass __new__ constructor called for %r" % cls)
        if cls._find_agent():
            ## call the normal GPG.__init__() initialiser:
            attrs['init'] = cls.__init__
            attrs['_remove_agent'] = True
        return super(GPGMeta, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def _find_agent(cls):
        """Discover if a gpg-agent process for the current euid is running.

        If there is a matching gpg-agent process, set a :class:`psutil.Process`
        instance containing the gpg-agent process' information to
        ``cls._agent_proc``.

        For Unix systems, we check that the effective UID of this
        ``python-gnupg`` process is also the owner of the gpg-agent
        process. For Windows, we check that the usernames of the owners are
        the same. (Sorry Windows users; maybe you should switch to anything
        else.)

        .. note: This function will only run if the psutil_ Python extension
            is installed. Because psutil won't run with the PyPy interpreter,
            use of it is optional (although highly recommended).

        .. _psutil: https://pypi.python.org/pypi/psutil

        :returns: True if there exists a gpg-agent process running under the
                  same effective user ID as that of this program. Otherwise,
                  returns False.
        """
        if not psutil:
            return False

        this_process = psutil.Process(os.getpid())
        ownership_match = False

        if _util._running_windows:
            identity = this_process.username()
        else:
            identity = this_process.uids

        for proc in psutil.process_iter():
            try:
                # In my system proc.name & proc.is_running are methods
                if (proc.name() == "gpg-agent") and proc.is_running():
                    log.debug("Found gpg-agent process with pid %d" % proc.pid)
                    if _util._running_windows:
                        if proc.username() == identity:
                            ownership_match = True
                    else:
                        # proc.uids & identity are methods to
                        if proc.uids() == identity():
                            ownership_match = True
            except psutil.Error as err:
                # Exception when getting proc info, possibly because the
                # process is zombie / process no longer exist. Just ignore it.
                log.warn("Error while attempting to find gpg-agent process: %s" % err)
            # Next code must be inside for operator.
            # Otherwise to _agent_proc will be saved not "gpg-agent" process buth an other.
            if ownership_match:
                log.debug("Effective UIDs of this process and gpg-agent match")
                setattr(cls, '_agent_proc', proc)
                return True

        return False


class GPGBase(object):
    """Base class for storing properties and controlling process initialisation.

    :const _result_map: A *dict* containing classes from
                        :mod:`~gnupg._parsers`, used for parsing results
                        obtained from GnuPG commands.
    :const _decode_errors: How to handle encoding errors.
    """
    __metaclass__  = GPGMeta
    _decode_errors = 'strict'
    _result_map    = { 'crypt':    _parsers.Crypt,
                       'delete':   _parsers.DeleteResult,
                       'generate': _parsers.GenKey,
                       'import':   _parsers.ImportResult,
                       'export':   _parsers.ExportResult,
                       'list':     _parsers.ListKeys,
                       'sign':     _parsers.Sign,
                       'verify':   _parsers.Verify,
                       'expire':   _parsers.KeyExpirationResult,
                       'signing':  _parsers.KeySigningResult,
                       'packets':  _parsers.ListPackets }

    def __init__(self, binary=None, home=None, keyring=None, secring=None,
                 use_agent=False, default_preference_list=None,
                 ignore_homedir_permissions=False, verbose=False, options=None):
        """Create a ``GPGBase``.

        This class is used to set up properties for controlling the behaviour
        of configuring various options for GnuPG, such as setting GnuPG's
        **homedir** , and the paths to its **binary** and **keyring** .

        :const binary: (:obj:`str`) The full path to the GnuPG binary.

        :ivar homedir: (:class:`~gnupg._util.InheritableProperty`) The full
                       path to the current setting for the GnuPG
                       ``--homedir``.

        :ivar _generated_keys: (:class:`~gnupg._util.InheritableProperty`)
                               Controls setting the directory for storing any
                               keys which are generated with
                               :meth:`~gnupg.GPG.gen_key`.

        :ivar str keyring: The filename in **homedir** to use as the keyring
                           file for public keys.
        :ivar str secring: The filename in **homedir** to use as the keyring
                           file for secret keys.
        """
        self.ignore_homedir_permissions = ignore_homedir_permissions
        self.binary  = _util._find_binary(binary)
        self.homedir = os.path.expanduser(home) if home else _util._conf
        pub = _parsers._fix_unsafe(keyring) if keyring else 'pubring.gpg'
        sec = _parsers._fix_unsafe(secring) if secring else 'secring.gpg'
        self.keyring = os.path.join(self._homedir, pub)
        self.secring = os.path.join(self._homedir, sec)
        self.options = list(_parsers._sanitise_list(options)) if options else None

        #: The version string of our GnuPG binary
        self.binary_version = '0.0.0'
        self.verbose = False

        if default_preference_list:
            self._prefs = _check_preferences(default_preference_list, 'all')
        else:
            self._prefs  = 'SHA512 SHA384 SHA256 AES256 CAMELLIA256 TWOFISH'
            self._prefs += ' AES192 ZLIB ZIP Uncompressed'

        encoding = locale.getpreferredencoding()
        if encoding is None: # This happens on Jython!
            encoding = sys.stdin.encoding
        self._encoding = encoding.lower().replace('-', '_')
        self._filesystemencoding = encodings.normalize_encoding(
            sys.getfilesystemencoding().lower())

        # Issue #49: https://github.com/isislovecruft/python-gnupg/issues/49
        #
        # During `line = stream.readline()` in `_read_response()`, the Python
        # codecs module will choke on Unicode data, so we globally monkeypatch
        # the "strict" error handler to use the builtin `replace_errors`
        # handler:
        codecs.register_error('strict', codecs.replace_errors)

        self._keyserver = 'hkp://wwwkeys.pgp.net'
        self.__generated_keys = os.path.join(self.homedir, 'generated-keys')

        try:
            assert self.binary, "Could not find binary %s" % binary
            if _util._py3k:
                assert isinstance(verbose, (bool, str, int)), \
                    "'verbose' must be boolean, string, or 0 <= n <= 9"
            else:
                assert isinstance(verbose, (bool, str, int, unicode)), \
                    "'verbose' must be boolean, string, unicode, or 0 <= n <= 9"
            assert isinstance(use_agent, bool), "'use_agent' must be boolean"
            if self.options is not None:
                assert isinstance(self.options, list), "options not list"
        except (AssertionError, AttributeError) as ae:
            log.error("GPGBase.__init__(): %s" % str(ae))
            raise RuntimeError(str(ae))
        else:
            self._set_verbose(verbose)
            self.use_agent = use_agent

        if hasattr(self, '_agent_proc') \
                and getattr(self, '_remove_agent', None) is True:
            if hasattr(self, '__remove_path__'):
                self.__remove_path__('pinentry')

        # Assign our self.binary_version attribute:
        self._check_sane_and_get_gpg_version()

    def __remove_path__(self, prog=None, at_exit=True):
        """Remove the directories containing a program from the system's
        ``$PATH``. If ``GPGBase.binary`` is in a directory being removed, it
        is linked to :file:'./gpg' in the current directory.

        :param str prog: The program to remove from ``$PATH``.
        :param bool at_exit: Add the program back into the ``$PATH`` when the
                             Python interpreter exits, and delete any symlinks
                             to ``GPGBase.binary`` which were created.
        """
        #: A list of ``$PATH`` entries which were removed to disable pinentry.
        self._removed_path_entries = []

        log.debug("Attempting to remove %s from system PATH" % str(prog))
        if (prog is None) or (not isinstance(prog, str)): return

        try:
            program = _util._which(prog)[0]
        except (OSError, IOError, IndexError) as err:
            log.err(str(err))
            log.err("Cannot find program '%s', not changing PATH." % prog)
            return

        ## __remove_path__ cannot be an @classmethod in GPGMeta, because
        ## the use_agent attribute must be set by the instance.
        if not self.use_agent:
            program_base = os.path.dirname(prog)
            gnupg_base = os.path.dirname(self.binary)

            ## symlink our gpg binary into $PWD if the path we are removing is
            ## the one which contains our gpg executable:
            new_gpg_location = os.path.join(os.getcwd(), 'gpg')
            if gnupg_base == program_base:
                os.symlink(self.binary, new_gpg_location)
                self.binary = new_gpg_location

            ## copy the original environment so that we can put it back later:
            env_copy = os.environ            ## this one should not be touched
            path_copy = os.environ.pop('PATH')
            log.debug("Created a copy of system PATH: %r" % path_copy)
            assert not os.environ.has_key('PATH'), "OS env kept $PATH anyway!"

            @staticmethod
            def remove_program_from_path(path, prog_base):
                """Remove all directories which contain a program from PATH.

                :param str path: The contents of the system environment's
                                 ``$PATH``.

                :param str prog_base: The directory portion of a program's
                                      location, without the trailing slash,
                                      and without the program name. For
                                      example, ``prog_base='/usr/bin'``.
                """
                paths = path.split(':')
                for directory in paths:
                    if directory == prog_base:
                        log.debug("Found directory with target program: %s"
                                  % directory)
                        path.remove(directory)
                        self._removed_path_entries.append(directory)
                log.debug("Deleted all found instance of %s." % directory)
                log.debug("PATH is now:%s%s" % (os.linesep, path))
                new_path = ':'.join([p for p in path])
                return new_path

            @staticmethod
            def update_path(environment, path):
                """Add paths to the string at ``os.environ['PATH']``.

                :param str environment: The environment mapping to update.
                :param list path: A list of strings to update the PATH with.
                """
                log.debug("Updating system path...")
                os.environ = environment
                new_path = ':'.join([p for p in path])
                old = ''
                if 'PATH' in os.environ:
                    new_path = ':'.join([os.environ['PATH'], new_path])
                os.environ.update({'PATH': new_path})
                log.debug("System $PATH: %s" % os.environ['PATH'])

            modified_path = remove_program_from_path(path_copy, program_base)
            update_path(env_copy, modified_path)

            ## register an _exithandler with the python interpreter:
            atexit.register(update_path, env_copy, path_copy)

            def remove_symlinked_binary(symlink):
                if os.path.islink(symlink):
                    os.unlink(symlink)
                    log.debug("Removed binary symlink '%s'" % symlink)
            atexit.register(remove_symlinked_binary, new_gpg_location)

    @property
    def default_preference_list(self):
        """Get the default preference list."""
        return self._prefs

    @default_preference_list.setter
    def default_preference_list(self, prefs):
        """Set the default preference list.

        :param str prefs: A string containing the default preferences for
                          ciphers, digests, and compression algorithms.
        """
        prefs = _check_preferences(prefs)
        if prefs is not None:
            self._prefs = prefs

    @default_preference_list.deleter
    def default_preference_list(self):
        """Reset the default preference list to its original state.

        Note that "original state" does not mean the default preference
        list for whichever version of GnuPG is being used. It means the
        default preference list defined by :attr:`GPGBase._prefs`.

        Using BZIP2 is avoided due to not interacting well with some versions
        of GnuPG>=2.0.0.
        """
        self._prefs = 'SHA512 SHA384 SHA256 AES256 CAMELLIA256 TWOFISH ZLIB ZIP'

    @property
    def keyserver(self):
        """Get the current keyserver setting."""
        return self._keyserver

    @keyserver.setter
    def keyserver(self, location):
        """Set the default keyserver to use for sending and receiving keys.

        The ``location`` is sent to :func:`_parsers._check_keyserver` when
        option are parsed in :meth:`gnupg.GPG._make_options`.

        :param str location: A string containing the default keyserver. This
                             should contain the desired keyserver protocol
                             which is supported by the keyserver, for example,
                             ``'hkps://keys.mayfirst.org'``. The default
                             keyserver is ``'hkp://wwwkeys.pgp.net'``.
        """
        self._keyserver = location

    @keyserver.deleter
    def keyserver(self):
        """Reset the keyserver to the default setting."""
        self._keyserver = 'hkp://wwwkeys.pgp.net'

    def _homedir_getter(self):
        """Get the directory currently being used as GnuPG's homedir.

        If unspecified, use :file:`~/.config/python-gnupg/`

        :rtype: str
        :returns: The absolute path to the current GnuPG homedir.
        """
        return self._homedir

    def _homedir_setter(self, directory):
        """Set the directory to use as GnuPG's homedir.

        If unspecified, use $HOME/.config/python-gnupg. If specified, ensure
        that the ``directory`` does not contain various shell escape
        characters. If ``directory`` is not found, it will be automatically
        created. Lastly, the ``direcory`` will be checked that the EUID has
        read and write permissions for it.

        :param str directory: A relative or absolute path to the directory to
                            use for storing/accessing GnuPG's files, including
                            keyrings and the trustdb.
        :raises: :exc:`~exceptions.RuntimeError` if unable to find a suitable
                 directory to use.
        """
        if not directory:
            log.debug("GPGBase._homedir_setter(): Using default homedir: '%s'"
                      % _util._conf)
            directory = _util._conf

        hd = _parsers._fix_unsafe(directory)
        log.debug("GPGBase._homedir_setter(): got directory '%s'" % hd)

        if hd:
            log.debug("GPGBase._homedir_setter(): Check existence of '%s'" % hd)
            _util._create_if_necessary(hd)

        if self.ignore_homedir_permissions:
            self._homedir = hd
        else:
            try:
                log.debug("GPGBase._homedir_setter(): checking permissions")
                assert _util._has_readwrite(hd), \
                    "Homedir '%s' needs read/write permissions" % hd
            except AssertionError as ae:
                msg = ("Unable to set '%s' as GnuPG homedir" % directory)
                log.debug("GPGBase.homedir.setter(): %s" % msg)
                log.debug(str(ae))
                raise RuntimeError(str(ae))
            else:
                log.info("Setting homedir to '%s'" % hd)
                self._homedir = hd

    homedir = _util.InheritableProperty(_homedir_getter, _homedir_setter)

    def _generated_keys_getter(self):
        """Get the ``homedir`` subdirectory for storing generated keys.

        :rtype: str
        :returns: The absolute path to the current GnuPG homedir.
        """
        return self.__generated_keys

    def _generated_keys_setter(self, directory):
        """Set the directory for storing generated keys.

        If unspecified, use
        :meth:`~gnupg._meta.GPGBase.homedir`/generated-keys. If specified,
        ensure that the ``directory`` does not contain various shell escape
        characters. If ``directory`` isn't found, it will be automatically
        created. Lastly, the ``directory`` will be checked to ensure that the
        current EUID has read and write permissions for it.

        :param str directory: A relative or absolute path to the directory to
             use for storing/accessing GnuPG's files, including keyrings and
             the trustdb.
        :raises: :exc:`~exceptions.RuntimeError` if unable to find a suitable
             directory to use.
        """
        if not directory:
            directory = os.path.join(self.homedir, 'generated-keys')
            log.debug("GPGBase._generated_keys_setter(): Using '%s'"
                      % directory)

        hd = _parsers._fix_unsafe(directory)
        log.debug("GPGBase._generated_keys_setter(): got directory '%s'" % hd)

        if hd:
            log.debug("GPGBase._generated_keys_setter(): Check exists '%s'"
                      % hd)
            _util._create_if_necessary(hd)

        try:
            log.debug("GPGBase._generated_keys_setter(): check permissions")
            assert _util._has_readwrite(hd), \
                "Keys dir '%s' needs read/write permissions" % hd
        except AssertionError as ae:
            msg = ("Unable to set '%s' as generated keys dir" % directory)
            log.debug("GPGBase._generated_keys_setter(): %s" % msg)
            log.debug(str(ae))
            raise RuntimeError(str(ae))
        else:
            log.info("Setting homedir to '%s'" % hd)
            self.__generated_keys = hd

    _generated_keys = _util.InheritableProperty(_generated_keys_getter,
                                                _generated_keys_setter)

    def _check_sane_and_get_gpg_version(self):
        """Check that everything runs alright, and grab the gpg binary's
        version number while we're at it, storing it as :data:`binary_version`.

        :raises RuntimeError: if we cannot invoke the gpg binary.
        """
        proc = self._open_subprocess(["--list-config", "--with-colons"])
        result = self._result_map['list'](self)
        self._read_data(proc.stdout, result)
        if proc.returncode:
            raise RuntimeError("Error invoking gpg: %s" % result.data)
        else:
            try:
                proc.terminate()
            except OSError:
                log.error(("Could neither invoke nor terminate a gpg process... "
                           "Are you sure you specified the corrent (and full) "
                           "path to the gpg binary?"))

        version_line = result.data.partition(b':version:')[2].decode()
        if not version_line:
            raise RuntimeError("Got invalid version line from gpg: %s\n" % result.data)
        self.binary_version = version_line.split('\n')[0]
        if not _VERSION_RE.match(self.binary_version):
            raise RuntimeError("Got invalid version line from gpg: %s\n" % self.binary_version)
        log.debug("Using GnuPG version %s" % self.binary_version)

    def _make_args(self, args, passphrase=False):
        """Make a list of command line elements for GPG.

        The value of ``args`` will be appended only if it passes the checks in
        :func:`gnupg._parsers._sanitise`. The ``passphrase`` argument needs to
        be True if a passphrase will be sent to GnuPG, else False.

        :param list args: A list of strings of options and flags to pass to
                          ``GPG.binary``. This is input safe, meaning that
                          these values go through strict checks (see
                          ``parsers._sanitise_list``) before being passed to to
                          the input file descriptor for the GnuPG process.
                          Each string should be given exactly as it would be on
                          the commandline interface to GnuPG,
                          e.g. ["--cipher-algo AES256", "--default-key
                          A3ADB67A2CDB8B35"].

        :param bool passphrase: If True, the passphrase will be sent to the
                                stdin file descriptor for the attached GnuPG
                                process.
        """
        ## see TODO file, tag :io:makeargs:
        cmd = [self.binary,
               '--no-options --no-emit-version --no-tty --status-fd 2']

        if self.homedir: cmd.append('--homedir "%s"' % self.homedir)

        if self.keyring:
            cmd.append('--no-default-keyring --keyring %s' % self.keyring)
        if self.secring:
            cmd.append('--secret-keyring %s' % self.secring)

        if passphrase: cmd.append('--batch --passphrase-fd 0')

        if self.use_agent is True: cmd.append('--use-agent')
        elif self.use_agent is False: cmd.append('--no-use-agent')

        # The arguments for debugging and verbosity should be placed into the
        # cmd list before the options/args in order to resolve Issue #76:
        # https://github.com/isislovecruft/python-gnupg/issues/76
        if self.verbose:
            cmd.append('--debug-all')

            if (isinstance(self.verbose, str) or
                (isinstance(self.verbose, int) and (self.verbose >= 1))):
                # GnuPG<=1.4.18 parses the `--debug-level` command in a way
                # that is incompatible with all other GnuPG versions. :'(
                if self.binary_version and (self.binary_version <= '1.4.18'):
                    cmd.append('--debug-level=%s' % self.verbose)
                else:
                    cmd.append('--debug-level %s' % self.verbose)

        if self.options:
            [cmd.append(opt) for opt in iter(_sanitise_list(self.options))]
        if args:
            [cmd.append(arg) for arg in iter(_sanitise_list(args))]

        return cmd

    def _open_subprocess(self, args=None, passphrase=False):
        """Open a pipe to a GPG subprocess and return the file objects for
        communicating with it.

        :param list args: A list of strings of options and flags to pass to
                          ``GPG.binary``. This is input safe, meaning that
                          these values go through strict checks (see
                          ``parsers._sanitise_list``) before being passed to to
                          the input file descriptor for the GnuPG process.
                          Each string should be given exactly as it would be on
                          the commandline interface to GnuPG,
                          e.g. ["--cipher-algo AES256", "--default-key
                          A3ADB67A2CDB8B35"].

        :param bool passphrase: If True, the passphrase will be sent to the
                                stdin file descriptor for the attached GnuPG
                                process.
        """
        ## see http://docs.python.org/2/library/subprocess.html#converting-an\
        ##    -argument-sequence-to-a-string-on-windows
        cmd = shlex.split(' '.join(self._make_args(args, passphrase)))
        log.debug("Sending command to GnuPG process:%s%s" % (os.linesep, cmd))

        if platform.system() == "Windows":
            # TODO figure out what the hell is going on there.
            expand_shell = True
        else:
            expand_shell = False

        environment = {
            'LANGUAGE': os.environ.get('LANGUAGE') or 'en',
            'GPG_TTY': os.environ.get('GPG_TTY') or '',
            'DISPLAY': os.environ.get('DISPLAY') or '',
            'GPG_AGENT_INFO': os.environ.get('GPG_AGENT_INFO') or '',
            'GPG_TTY': os.environ.get('GPG_TTY') or '',
            'GPG_PINENTRY_PATH': os.environ.get('GPG_PINENTRY_PATH') or '',
        }

        return subprocess.Popen(cmd, shell=expand_shell, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=environment)

    def _read_response(self, stream, result):
        """Reads all the stderr output from GPG, taking notice only of lines
        that begin with the magic [GNUPG:] prefix.

        Calls methods on the response object for each valid token found, with
        the arg being the remainder of the status line.

        :param stream: A byte-stream, file handle, or a
                       :data:`subprocess.PIPE` for parsing the status codes
                       from the GnuPG process.

        :param result: The result parser class from :mod:`~gnupg._parsers` ―
                       the ``handle_status()`` method of that class will be
                       called in order to parse the output of ``stream``.
        """
        # All of the userland messages (i.e. not status-fd lines) we're not
        # interested in passing to our logger
        userland_messages_to_ignore = []

        if self.ignore_homedir_permissions:
            userland_messages_to_ignore.append('unsafe ownership on homedir')

        lines = []

        while True:
            line = stream.readline()
            if len(line) == 0:
                break
            lines.append(line)
            line = line.rstrip()

            if line.startswith('[GNUPG:]'):
                line = _util._deprefix(line, '[GNUPG:] ', log.status)
                keyword, value = _util._separate_keyword(line)
                result._handle_status(keyword, value)
            elif line.startswith('gpg:'):
                line = _util._deprefix(line, 'gpg: ')
                keyword, value = _util._separate_keyword(line)

                # Silence warnings from gpg we're supposed to ignore
                ignore = any(msg in value for msg in userland_messages_to_ignore)

                if not ignore:
                    # Log gpg's userland messages at our own levels:
                    if keyword.upper().startswith("WARNING"):
                        log.warn("%s" % value)
                    elif keyword.upper().startswith("FATAL"):
                        log.critical("%s" % value)
                        # Handle the gpg2 error where a missing trustdb.gpg is,
                        # for some stupid reason, considered fatal:
                        if value.find("trustdb.gpg") and value.find("No such file"):
                            result._handle_status('NEED_TRUSTDB', '')
            else:
                if self.verbose:
                    log.info("%s" % line)
                else:
                    log.debug("%s" % line)
        result.stderr = ''.join(lines)

    def _read_data(self, stream, result):
        """Incrementally read from ``stream`` and store read data.

        All data gathered from calling ``stream.read()`` will be concatenated
        and stored as ``result.data``.

        :param stream: An open file-like object to read() from.
        :param result: An instance of one of the :ref:`result parsing classes
            <parsers>` from :const:`~gnupg._meta.GPGBase._result_map`.
        """
        chunks = []
        log.debug("Reading data from stream %r..." % stream.__repr__())

        while True:
            data = stream.read(1024)
            if len(data) == 0:
                break
            chunks.append(data)
            log.debug("Read %4d bytes" % len(data))

        # Join using b'' or '', as appropriate
        result.data = type(data)().join(chunks)
        log.debug("Finishing reading from stream %r..." % stream.__repr__())
        log.debug("Read %4d bytes total" % len(result.data))

    def _set_verbose(self, verbose):
        """Check and set our :data:`verbose` attribute.
        The debug-level must be a string or an integer. If it is one of
        the allowed strings, GnuPG will translate it internally to it's
        corresponding integer level:

        basic     = 1-2
        advanced  = 3-5
        expert    = 6-8
        guru      = 9+

        If it's not one of the recognised string levels, then then
        entire argument is ignored by GnuPG. :(

        To fix that stupid behaviour, if they wanted debugging but typo'd
        the string level (or specified ``verbose=True``), we'll default to
        'basic' logging.
        """
        string_levels = ('basic', 'advanced', 'expert', 'guru')

        if verbose is True:
            # The caller wants logging, but we need a valid --debug-level
            # for gpg. Default to "basic", and warn about the ambiguity.
            verbose = 'basic'

        if (isinstance(verbose, str) and not (verbose in string_levels)):
            verbose = 'basic'

        self.verbose = verbose

    def _collect_output(self, process, result, writer=None, stdin=None):
        """Drain the subprocesses output streams, writing the collected output
        to the result. If a writer thread (writing to the subprocess) is given,
        make sure it's joined before returning. If a stdin stream is given,
        close it before returning.
        """
        stderr = codecs.getreader(self._encoding)(process.stderr)
        rr = threading.Thread(target=self._read_response,
                              args=(stderr, result))
        rr.setDaemon(True)
        log.debug('stderr reader: %r', rr)
        rr.start()

        stdout = process.stdout
        dr = threading.Thread(target=self._read_data, args=(stdout, result))
        dr.setDaemon(True)
        log.debug('stdout reader: %r', dr)
        dr.start()

        dr.join()
        rr.join()
        if writer is not None:
            writer.join()
        process.wait()
        if stdin is not None:
            try:
                stdin.close()
            except IOError:
                pass
        stderr.close()
        stdout.close()

    def _handle_io(self, args, file, result, passphrase=False, binary=False):
        """Handle a call to GPG - pass input data, collect output data."""
        p = self._open_subprocess(args, passphrase)
        if not binary:
            stdin = codecs.getwriter(self._encoding)(p.stdin)
        else:
            stdin = p.stdin
        if passphrase:
            _util._write_passphrase(stdin, passphrase, self._encoding)
        writer = _util._threaded_copy_data(file, stdin)
        self._collect_output(p, result, writer, stdin)
        return result

    def _recv_keys(self, keyids, keyserver=None):
        """Import keys from a keyserver.

        :param str keyids: A space-delimited string containing the keyids to
                           request.
        :param str keyserver: The keyserver to request the ``keyids`` from;
                              defaults to `gnupg.GPG.keyserver`.
        """
        if not keyserver:
            keyserver = self.keyserver

        args = ['--keyserver {0}'.format(keyserver),
                '--recv-keys {0}'.format(keyids)]
        log.info('Requesting keys from %s: %s' % (keyserver, keyids))

        result = self._result_map['import'](self)
        proc = self._open_subprocess(args)
        self._collect_output(proc, result)
        log.debug('recv_keys result: %r', result.__dict__)
        return result

    def _sign_file(self, file, default_key=None, passphrase=None,
                   clearsign=True, detach=False, binary=False,
                   digest_algo='SHA512'):
        """Create a signature for a file.

        :param file: The file stream (i.e. it's already been open()'d) to sign.
        :param str default_key: The key to sign with.
        :param str passphrase: The passphrase to pipe to stdin.
        :param bool clearsign: If True, create a cleartext signature.
        :param bool detach: If True, create a detached signature.
        :param bool binary: If True, do not ascii armour the output.
        :param str digest_algo: The hash digest to use. Again, to see which
                                hashes your GnuPG is capable of using, do:
                                ``$ gpg --with-colons --list-config
                                digestname``. The default, if unspecified, is
                                ``'SHA512'``.
        """
        log.debug("_sign_file():")
        if binary:
            log.info("Creating binary signature for file %s" % file)
            args = ['--sign']
        else:
            log.info("Creating ascii-armoured signature for file %s" % file)
            args = ['--sign --armor']

        if clearsign:
            args.append("--clearsign")
            if detach:
                log.warn("Cannot use both --clearsign and --detach-sign.")
                log.warn("Using default GPG behaviour: --clearsign only.")
        elif detach and not clearsign:
            args.append("--detach-sign")

        if default_key:
            args.append(str("--default-key %s" % default_key))

        args.append(str("--digest-algo %s" % digest_algo))

        ## We could use _handle_io here except for the fact that if the
        ## passphrase is bad, gpg bails and you can't write the message.
        result = self._result_map['sign'](self)

        ## If the passphrase is an empty string, the message up to and
        ## including its first newline will be cut off before making it to the
        ## GnuPG process. Therefore, if the passphrase='' or passphrase=b'',
        ## we set passphrase=None.  See Issue #82:
        ## https://github.com/isislovecruft/python-gnupg/issues/82
        if _util._is_string(passphrase):
            passphrase = passphrase if len(passphrase) > 0 else None
        elif _util._is_bytes(passphrase):
            passphrase = s(passphrase) if len(passphrase) > 0 else None
        else:
            passphrase = None

        proc = self._open_subprocess(args, passphrase is not None)
        try:
            if passphrase:
                _util._write_passphrase(proc.stdin, passphrase, self._encoding)
            writer = _util._threaded_copy_data(file, proc.stdin)
        except IOError as ioe:
            log.exception("Error writing message: %s" % str(ioe))
            writer = None
        self._collect_output(proc, result, writer, proc.stdin)
        return result

    def _encrypt(self, data, recipients,
                 default_key=None,
                 passphrase=None,
                 armor=True,
                 encrypt=True,
                 symmetric=False,
                 always_trust=True,
                 output=None,
                 throw_keyids=False,
                 hidden_recipients=None,
                 cipher_algo='AES256',
                 digest_algo='SHA512',
                 compress_algo='ZLIB'):
        """Encrypt the message read from the file-like object **data**.

        :param str data: The file or bytestream to encrypt.

        :param str recipients: The recipients to encrypt to. Recipients must
                               be specified keyID/fingerprint.

        .. warning:: Care should be taken in Python2 to make sure that the
                     given fingerprints for **recipients** are in fact strings
                     and not unicode objects.

        :param str default_key: The keyID/fingerprint of the key to use for
                                signing. If given, **data** will be encrypted
                                *and* signed.

        :param str passphrase: If given, and **default_key** is also given,
                               use this passphrase to unlock the secret
                               portion of the **default_key** to sign the
                               encrypted **data**.  Otherwise, if
                               **default_key** is not given, but **symmetric**
                               is ``True``, then use this passphrase as the
                               passphrase for symmetric encryption. Signing
                               and symmetric encryption should *not* be
                               combined when sending the **data** to other
                               recipients, else the passphrase to the secret
                               key would be shared with them.

        :param bool armor: If True, ascii armor the output; otherwise, the
                           output will be in binary format. (Default: True)

        :param bool encrypt: If True, encrypt the **data** using the
                             **recipients** public keys. (Default: True)

        :param bool symmetric: If True, encrypt the **data** to **recipients**
                               using a symmetric key. See the **passphrase**
                               parameter. Symmetric encryption and public key
                               encryption can be used simultaneously, and will
                               result in a ciphertext which is decryptable
                               with either the symmetric **passphrase** or one
                               of the corresponding private keys.

        :param bool always_trust: If True, ignore trust warnings on
                                  **recipients** keys. If False, display trust
                                  warnings. (default: True)

        :type output: str or file-like object
        :param output: The output file to write to. If not specified, the
                       encrypted output is returned, and thus should be stored
                       as an object in Python. For example:

        >>> import shutil
        >>> import gnupg
        >>> if os.path.exists("doctests"):
        ...     shutil.rmtree("doctests")
        >>> gpg = gnupg.GPG(homedir="doctests")
        >>> key_settings = gpg.gen_key_input(key_type='RSA',
        ...                                  key_length=1024,
        ...                                  key_usage='ESCA',
        ...                                  passphrase='foo')
        >>> key = gpg.gen_key(key_settings)
        >>> message = "The crow flies at midnight."
        >>> encrypted = str(gpg.encrypt(message, key.fingerprint))
        >>> assert encrypted != message
        >>> assert not encrypted.isspace()
        >>> decrypted = str(gpg.decrypt(encrypted, passphrase='foo'))
        >>> assert not decrypted.isspace()
        >>> decrypted
        'The crow flies at midnight.'


        :param bool throw_keyids: If True, make all **recipients** keyids be
            zero'd out in packet information. This is the same as using
            **hidden_recipients** for all **recipients**. (Default: False).

        :param list hidden_recipients: A list of recipients that should have
            their keyids zero'd out in packet information.

        :param str cipher_algo: The cipher algorithm to use. To see available
                                algorithms with your version of GnuPG, do:
                                :command:`$ gpg --with-colons --list-config
                                ciphername`. The default **cipher_algo**, if
                                unspecified, is ``'AES256'``.

        :param str digest_algo: The hash digest to use. Again, to see which
                                hashes your GnuPG is capable of using, do:
                                :command:`$ gpg --with-colons --list-config
                                digestname`.  The default, if unspecified, is
                                ``'SHA512'``.

        :param str compress_algo: The compression algorithm to use. Can be one
                                  of ``'ZLIB'``, ``'BZIP2'``, ``'ZIP'``, or
                                  ``'Uncompressed'``.
        """
        args = []

        ## FIXME: GnuPG appears to ignore the --output directive when being
        ## programmatically driven. We'll handle the IO ourselves to fix this
        ## for now.
        output_filename = None
        if output:
            if getattr(output, 'fileno', None) is not None:
                ## avoid overwrite confirmation message
                if getattr(output, 'name', None) is not None:
                    output_filename = output.name
                    if os.path.exists(output.name):
                        os.remove(output.name)
                    #args.append('--output %s' % output.name)
            else:
                output_filename = output
                if os.path.exists(output):
                    os.remove(output)
                #args.append('--output %s' % output)

        if armor: args.append('--armor')
        if always_trust: args.append('--always-trust')
        if cipher_algo: args.append('--cipher-algo %s' % cipher_algo)
        if compress_algo: args.append('--compress-algo %s' % compress_algo)

        if default_key:
            args.append('--sign')
            args.append('--default-key %s' % default_key)
            if digest_algo:
                args.append('--digest-algo %s' % digest_algo)

        ## both can be used at the same time for an encrypted file which
        ## is decryptable with a passphrase or secretkey.
        if symmetric: args.append('--symmetric')
        if encrypt: args.append('--encrypt')
        if throw_keyids: args.append('--throw-keyids')

        if len(recipients) >= 1:
            log.debug("GPG.encrypt() called for recipients '%s' with type '%s'"
                      % (recipients, type(recipients)))

            if isinstance(recipients, (list, tuple)):
                for recp in recipients:
                    if not _util._py3k:
                        if isinstance(recp, unicode):
                            try:
                                assert _parsers._is_hex(str(recp))
                            except AssertionError:
                                log.info("Can't accept recipient string: %s"
                                         % recp)
                            else:
                                self._add_recipient_string(args, hidden_recipients, str(recp))
                                continue
                            ## will give unicode in 2.x as '\uXXXX\uXXXX'
                            if isinstance(hidden_recipients, (list, tuple)):
                                if [s for s in hidden_recipients if recp in str(s)]:
                                    args.append('--hidden-recipient %r' % recp)
                                else:
                                    args.append('--recipient %r' % recp)
                            else:
                                args.append('--recipient %r' % recp)
                            continue
                    if isinstance(recp, str):
                        self._add_recipient_string(args, hidden_recipients, recp)

            elif (not _util._py3k) and isinstance(recp, basestring):
                for recp in recipients.split('\x20'):
                    self._add_recipient_string(args, hidden_recipients, recp)

            elif _util._py3k and isinstance(recp, str):
                for recp in recipients.split(' '):
                    self._add_recipient_string(args, hidden_recipients, recp)
                    ## ...and now that we've proven py3k is better...
            else:
                log.debug("Don't know what to do with recipients: %r"
                          % recipients)

        result = self._result_map['crypt'](self)
        log.debug("Got data '%s' with type '%s'." % (data, type(data)))
        self._handle_io(args, data, result, passphrase=passphrase, binary=True)
        # Avoid writing raw encrypted bytes to terminal loggers and breaking
        # them in that adorable way where they spew hieroglyphics until reset:
        if armor:
            log.debug("\n%s" % result.data)

        if output_filename:
            log.info("Writing encrypted output to file: %s" % output_filename)
            with open(output_filename, 'wb') as fh:
                fh.write(result.data)
                fh.flush()
                log.info("Encrypted output written successfully.")

        return result

    def _add_recipient_string(self, args, hidden_recipients, recipient):
        if isinstance(hidden_recipients, (list, tuple)):
            if [s for s in hidden_recipients if recipient in str(s)]:
                args.append('--hidden-recipient %s' % recipient)
            else:
                args.append('--recipient %s' % recipient)
        else:
            args.append('--recipient %s' % recipient)
