#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import doctest
import fnmatch
from getpass import getpass
import os
import shutil
import signal
import subprocess
import sys
import traceback

import psutil
import qrcode
from sqlalchemy.orm.exc import NoResultFound

from db import db_session, Journalist
from management import run

ABS_MODULE_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
# We need to import config in each function because we're running the tests
# directly, so it's important to set the environment correctly, depending on
# development or testing, before importing config.
os.environ['SECUREDROP_ENV'] = 'dev'

# TODO: the PID file for the redis worker is hard-coded below.
# Ideally this constant would be provided by a test harness.
# It has been intentionally omitted from `config.py.example`
# in order to isolate the test vars from prod vars.
# When refactoring the test suite, the TEST_WORKER_PIDFILE
# TEST_WORKER_PIDFILE is also hard-coded in `tests/common.py`.
TEST_WORKER_PIDFILE = '/tmp/securedrop_test_worker.pid'


def _get_pid_from_file(pid_file_name): # pragma: no cover
    try:
        return int(open(pid_file_name).read())
    except IOError as exc:
        if 'No such file or directory' not in exc:
            raise


def _start_test_rqworker(config): # pragma: no cover
    if not psutil.pid_exists(_get_pid_from_file(TEST_WORKER_PIDFILE)):
        tmp_logfile = open('/tmp/test_rqworker.log', 'w')
        subprocess.Popen(['rqworker', 'test',
                          '-P', config.SECUREDROP_ROOT,
                          '--pid', TEST_WORKER_PIDFILE],
                         stdout=tmp_logfile,
                         stderr=subprocess.STDOUT)


def _stop_test_rqworker(): # pragma: no cover
    rqworker_pid = _get_pid_from_file(TEST_WORKER_PIDFILE)
    if rqworker_pid:
        os.kill(rqworker_pid, signal.SIGTERM)
        try:
            os.remove(TEST_WORKER_PIDFILE)
        except OSError as exc:
            if 'No such file or directory' not in exc:
                raise


def _cleanup_test_securedrop_dataroot(config): # pragma: no cover
    # Keyboard interrupts or dropping to pdb after a test failure sometimes
    # result in the temporary test SecureDrop data root not being deleted.
    if os.environ['SECUREDROP_ENV'] == 'test':
        try:
            shutil.rmtree(config.SECUREDROP_DATA_ROOT)
        except OSError as exc:
            if 'No such file or directory' not in exc:
                raise


def _cleanup_test_environment(config): # pragma: no cover
    _stop_test_rqworker()
    _cleanup_test_securedrop_dataroot(config)


def _run_in_test_environment(cmd): # pragma: no cover
    """Handles setting up and tearing down the necessary environment to run
    tests."""
    os.environ['SECUREDROP_ENV'] = 'test'
    import config
    _start_test_rqworker(config)
    print('\nRunning command `{}` in the test environment.\n'.format(cmd))

    try:
        test_rc = int(subprocess.call(cmd, shell=True))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(repr(traceback.format_exception(exc_type, exc_value,
                                              exc_traceback)))
        return 1
    else:
        return test_rc
    finally:
        _cleanup_test_environment(config)


def run_pytest_command(args): # pragma: no cover
    cmd = 'pytest '
    cmd += ' '.join(args.pytest_args[1:]) + ' ' # Discard first arg, "--"
    return _run_in_test_environment(cmd)


def _get_test_module_dict(test_type):
    """A convenience function that allows a user to pass, e.g.,
    "journalist" instead of "tests/test_unit_journalist.py". Returns a
    :obj:`dict` mapping of module keywords to absolute module paths.
    
    :param str type: The type, either 'functional' or 'unit' of tests to
                     gather.
    """
    assert test_type in ('functional', 'unit')

    tests, test_paths = [], []

    if test_type == 'functional':
        # test_dir = os.path.join(ABS_MODULE_DIR_PATH, 'tests', 'functional')
        # prefix = 'test_'
        # TODO: currently the functional tests only pass when run in a specific
        # order. This is because the db module creates a connection to the
        # test database upon import, but that test database is destroyed and
        # re-created for each test. db, crypto_util, and/or the test suite
        # should rewritten s.t. this is no longer an issue.
        return {'admin_interface':
                os.path.join(
                    ABS_MODULE_DIR_PATH,
                    'tests/functional/test_admin_interface.py'),
                'submit_and_retrieve_file':
                os.path.join(
                    ABS_MODULE_DIR_PATH,
                    'tests/functional/test_submit_and_retrieve_file.py'),
                'submit_and_retrieve_message':
                os.path.join(
                    ABS_MODULE_DIR_PATH,
                    'tests/functional/test_submit_and_retrieve_message.py')}
    elif test_type == 'unit':
        test_dir = os.path.join(ABS_MODULE_DIR_PATH, 'tests')
        prefix = 'test_unit_'
        # Add irregularly named unit tests. TODO: consider combining journalist
        # unit tests and dropping 'unit' from all unit tests.
        tests += ['test_journalist', 'test_single_star']
        test_paths += [os.path.join(test_dir, test + '.py')
                       for test in tests]
        
    for file in os.listdir(test_dir):
        if fnmatch.fnmatch(file, prefix + '*.py'):
            tests.append(file[len(prefix):-len('.py')])
            test_paths.append(os.path.join(test_dir, file))

    return dict(zip(tests, test_paths))


def run_all_tests(): # pragma: no cover
    """Runs docstring, functional and unit tests."""
    # functional_and_unit_tests_rc = _run_in_test_environment('pytest --cov')
    # TODO: currently the functional tests only pass when run in a specific
    # order. This is because the db module creates a connection to the
    # test database upon import, but that test database is destroyed and
    # re-created for each test. db, crypto_util, and/or the test suite
    # should rewritten s.t. this is no longer an issue.
    functional_tests_rc = _run_in_test_environment(
        'pytest --cov -- {}'.format(' '.join(
            _get_test_module_dict('functional').values())))
    unit_tests_rc = _run_in_test_environment(
        'pytest --cov -- {}'.format(' '.join(
            _get_test_module_dict('unit').values())))
    doctring_tests_rc = run_docstring_tests()
    return int(any([functional_tests_rc, unit_tests_rc, doctring_tests_rc]))


def run_docstring_tests(): # pragma: no cover
    """Runs the docstring tests."""
    modules_with_doctests = ['crypto_util']
    module_paths = [os.path.join(ABS_MODULE_DIR_PATH, module) + '.py'
                   for module in modules_with_doctests]

    rc = 0
    for module_path in module_paths:
        try:
            doctest.testfile(module_path, module_relative=False)
        except:
            failure = 1

    return rc

def _get_pytest_cmd_from_args(args, test_type):
    """Takes a :class:`argparse.Namespace` and either returns a str that
    is the corresponding pytest command to be executed or exits with
    an error code if an invalid test name was passed.
    """
    assert test_type in ('functional', 'unit', 'pytest_cmd')

    cmd = 'pytest '
    # Any additional arguments to be passed through to pytest
    if getattr(args, 'pytest_args', False):
        cmd += ' '.join(args.pytest_args[1:]) + ' ' # Discard first arg, "--"

    # -a/--all
    if getattr(args, 'all', False):
        if '--cov' not in cmd:
            cmd += '--cov '
        cmd += '-- ' # end of pytest options
        cmd += ' '.join(_get_test_module_dict(test_type).values())

    # Run unittests related to a single module
    elif getattr(args, 'tests', False):
        cmd += '-- ' # end of pytest options
        for test in args.tests:
            try:
                module_path = _get_test_module_dict(test_type)[test]
            except KeyError:
                print('No {test_type} test "{test}" found. To list all {test_type} '
                      'tests run `./manage.py {test_type} -l`.'.format(**locals()))
                return 1
            else:
                cmd += module_path

    return cmd

def _run_or_list_functional_or_unit_tests(args, test_type): # pragma: no cover
    """Run or list functional or unit tests in the correct environment.
    """
    # -l/--list: list test modules by short names
    if getattr(args, 'list', False):
        print(list(_get_test_module_dict(test_type)))
        return 0

    # Run one or more tests, opt. passing custom args to pytest
    else:
        cmd_or_rc = _get_pytest_cmd_from_args(args, test_type)
        if isinstance(cmd_or_rc, int):
            return cmd_or_rc
        else:
            return _run_in_test_environment(cmd_or_rc)


def run_or_list_functional_tests(args): # pragma: no cover
    test_type = 'functional'
    return _run_or_list_functional_or_unit_tests(args, test_type)


def run_or_list_unit_tests(args): # pragma: no cover
    test_type = 'unit'
    return _run_or_list_functional_or_unit_tests(args, test_type)


def reset(): # pragma: no cover
    """Clears the SecureDrop development applications' state, restoring them to
    the way they were immediately after running `setup_dev.sh`. This command:
    1. Erases the development sqlite database file.
    2. Regenerates the database.
    3. Erases stored submissions and replies from the store dir.
    """
    import config
    import db

    # Erase the development db file
    assert hasattr(config, 'DATABASE_FILE'), ("TODO: ./manage.py doesn't know "
                                              'how to clear the db if the '
                                              'backend is not sqlite')
    try:
        os.remove(config.DATABASE_FILE)
    except OSError as exc:
        if 'No such file or directory' not in exc:
            raise

    # Regenerate the database
    db.init_db()

    # Clear submission/reply storage
    try:
        os.stat(config.STORE_DIR)
    except OSError as exc:
        if 'No such file or directory' not in exc:
            raise
    else:
        for source_dir in os.listdir(config.STORE_DIR):
            try:
                # Each entry in STORE_DIR is a directory corresponding to a source
                shutil.rmtree(os.path.join(config.STORE_DIR, source_dir))
            except OSError as exc:
                if 'No such file or directory' not in exc:
                    raise
    return 0


def add_admin(): # pragma: no cover
    return _add_user(is_admin=True)


def add_journalist(): # pragma: no cover
    return _add_user()


def _add_user(is_admin=False): # pragma: no cover
    while True:
        username = raw_input('Username: ')
        if Journalist.query.filter_by(username=username).first():
            print('Sorry, that username is already in use.')
        else:
            break

    while True:
        password = getpass('Password: ')
        password_again = getpass('Confirm Password: ')

        if len(password) > Journalist.MAX_PASSWORD_LEN:
            print('Your password is too long (maximum length {} characters). '
                  'Please pick a shorter '
                  'password.'.format(Journalist.MAX_PASSWORD_LEN))
            continue

        if password == password_again:
            break
        print("Passwords didn't match!")

    hotp_input = raw_input('Will this user be using a YubiKey [HOTP]? (y/N): ')
    otp_secret = None
    if hotp_input.lower() in ('y', 'yes'):
        while True:
            otp_secret = raw_input(
                'Please configure your YubiKey and enter the secret: ')
            if otp_secret:
                break

    try:
        user = Journalist(username=username,
                          password=password,
                          is_admin=is_admin,
                          otp_secret=otp_secret)
        db_session.add(user)
        db_session.commit()
    except Exception as exc:
        if 'username is not unique' in exc:
            print('ERROR: That username is already taken!')
        else:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print(repr(traceback.format_exception(exc_type, exc_value,
                                                  exc_traceback)))
        return 1
    else:
        print('User "{}" successfully added'.format(username))
        if not otp_secret:
            # Print the QR code for FreeOTP/ Google Authenticator
            print('\nScan the QR code below with FreeOTP or Google '
                  'Authenticator:\n')
            uri = user.totp.provisioning_uri(username,
                                             issuer_name='SecureDrop')
            qr = qrcode.QRCode()
            qr.add_data(uri)
            qr.print_ascii(tty=sys.stdout.isatty())
            print('\nIf the barcode does not render correctly, try changing '
                  "your terminal's font (Monospace for Linux, Menlo for OS "
                  'X). If you are using iTerm on Mac OS X, you will need to '
                  'change the "Non-ASCII Font", which is your profile\'s Text '
                  "settings.\n\nCan't scan the barcode? Enter following "
                  'shared secret '
                  'manually:\n{}\n'.format(user.formatted_otp_secret))
        return 0


def delete_user(): # pragma: no cover
    """Deletes a journalist or administrator from the application."""
    # Select user to delete
    username = raw_input('Username to delete: ')
    try:
        selected_user = Journalist.query.filter_by(username=username).one()
    except NoResultFound:
        print('ERROR: That user was not found!')
        return 0

    # Confirm deletion if user is found
    confirmation = raw_input('Are you sure you want to delete user '
                             '{} (y/n)?'.format(selected_user))
    if confirmation.lower() != 'y':
        print('Confirmation not received: user "{}" was NOT '
              'deleted'.format(username))
        return 0

    # Try to delete user from the database
    try:
        db_session.delete(selected_user)
        db_session.commit()
    except:
        # If the user was deleted between the user selection and confirmation,
        # (e.g., through the web app), we don't report any errors. If the user
        # is still there, but there was a error deleting them from the
        # database, we do report it.
        try:
            selected_user = Journalist.query.filter_by(username=username).one()
        except NoResultFound:
            pass
        else: 
            raise
        
    print('User "{}" successfully deleted'.format(username))
    return 0


def clean_tmp(): # pragma: no cover
    """Cleanup the SecureDrop temp directory. This is intended to be run
    as an automated cron job. We skip files that are currently in use to
    avoid deleting files that are currently being downloaded."""
    # Inspired by http://stackoverflow.com/a/11115521/1093000
    import config

    def file_in_use(fname):
        for proc in psutil.process_iter():
            try:
                open_files = proc.open_files()
                in_use = False or any([open_file.path == fname
                                        for open_file in open_files])
                # Early return for perf
                if in_use:
                    break
            except psutil.NoSuchProcess:
                # This catches a race condition where a process ends before we
                # can examine its files. Ignore this - if the process ended, it
                # can't be using fname, so this won't cause an error.
                pass

        return in_use

    def listdir_fullpath(d):
        # Thanks to http://stackoverflow.com/a/120948/1093000
        return [os.path.join(d, f) for f in os.listdir(d)]

    try:
        os.stat(config.TEMP_DIR)
    except OSError as exc:
        if 'No such file or directory' not in exc:
            raise
    else:
        for path in listdir_fullpath(config.TEMP_DIR):
            if not file_in_use(path):
                os.remove(path)

    return 0


def get_args():
    parser = argparse.ArgumentParser(prog=__file__, description='Management '
                                     'and testing utility for SecureDrop.')
    subps = parser.add_subparsers()
    # Run/list 1+ functional tests with pytest--pass options
    functional_subp = subps.add_parser('functional', help='Run 1+ functional '
                                       'tests (see subcommand help).')
    functional_subp.set_defaults(func=run_or_list_functional_tests)
    functional_excl = functional_subp.add_mutually_exclusive_group(
        required=True)
    functional_excl.add_argument('-a', '--all', action='store_true',
                           help='Run all functional tests with coverage '
                                 'report.')
    functional_excl.add_argument('-l', '--list', action='store_true',
                           help='List all functional tests.')
    functional_excl.add_argument('-t', '--tests', nargs='+',
                           help='Run 1+ functional tests (e.g., `./manage.py '
                                 'functional -t submit_and_retrieve_message '
                                 'admin_interface`). See -l to list unit test '
                                 'convenience names.')
    functional_subp.add_argument('pytest_args', nargs=argparse.REMAINDER,
                                 help='To pass args through to pytest end '
                                 'your command with "--" followed by the '
                                 'pytest args (e.g., --pdb, -x, --ff, etc.).')
    # Run/list 1+ unit tests with pytest--pass options
    unit_subp = subps.add_parser('unit', help='Run 1+ unit tests (see '
                                 'subcommand help).')
    unit_subp.set_defaults(func=run_or_list_unit_tests)
    unit_excl = unit_subp.add_mutually_exclusive_group(required=True)
    unit_excl.add_argument('-a', '--all', action='store_true',
                           help='Run all unit tests with coverage report.')
    unit_excl.add_argument('-l', '--list', action='store_true',
                           help='List all unit tests.')
    unit_excl.add_argument('-t', '--tests', nargs='+',
                           help='Run 1+ unit tests (e.g., `./manage.py '
                                 'functional -t crypt_util db`). See -l to '
                                 'list unit test convenience names.')
    unit_subp.add_argument('pytest_args', nargs=argparse.REMAINDER,
                           help='To pass args through to pytest end your '
                           'command with "--" followed by the pytest args '
                           '(e.g., --pdb, -x, --ff, etc.).')
    # Run/list the docstring tests
    doctest_subp = subps.add_parser('doctest', help='Run the docstring '
                                      'tests.')
    doctest_subp.set_defaults(func=run_docstring_tests)
    # Run the full test suite
    test_subp = subps.add_parser('test', help='Run all tests.')
    test_subp.set_defaults(func=run_all_tests)
    # Pass a command directly to pytest to be run in the test environment
    pytest_subp = subps.add_parser('pytest', help='Pass a command directly '
                                   'to pytest to be run in the test '
                                   'environment (see subcommand help).')
    pytest_subp.set_defaults(func=run_pytest_command)
    pytest_subp.add_argument('pytest_args', nargs=argparse.REMAINDER,
                            help='The first arg passed should be "--". '
                            'Any options that follow will be passed directly '
                            'pytest and executed in the test environment '
                             '(e.g. `./manage.py pytest -- '
                             'tests/test_unit_db.py::TestDatabase'
                             '::test_get_one_or_else_multiple_results '
                             '--pdb`).')
    # Run WSGI app
    run_subp = subps.add_parser('run', help='Run the Werkzeug source & '
                                'journalist WSGI apps (for development only, '
                                'not production).')
    run_subp.set_defaults(func=run)
    # Add/remove journalists + admins
    admin_subp = subps.add_parser('add-admin', help='Add an admin to the '
                                  'application.')
    admin_subp.set_defaults(func=add_admin)
    journalist_subp = subps.add_parser('add-journalist', help='Add a '
                                       'journalist to the application.')
    journalist_subp.set_defaults(func=add_journalist)
    delete_user_subp = subps.add_parser('delete-user', help='Delete a user '
                                        'from the application.')
    delete_user_subp.set_defaults(func=delete_user)

    # Reset application state
    reset_subp = subps.add_parser('reset', help='DANGER!!! Clears the '
                                  "SecureDrop application's state.")
    reset_subp.set_defaults(func=reset)
    # Cleanup the SD temp dir
    clean_tmp_subp = subps.add_parser('clean-tmp', help='Cleanup the '
                                      'SecureDrop temp directory.')
    clean_tmp_subp.set_defaults(func=clean_tmp)

    return parser


def _run_from_commandline(): # pragma: no cover
    try:
        args = get_args().parse_args()
        if len(args._get_kwargs()) > 1:
            rc = args.func(args)
        else:
            rc = args.func()
        sys.exit(rc)
    except KeyboardInterrupt:
        sys.exit(signal.SIGINT)
    finally: 
        _stop_test_rqworker()


if __name__ == '__main__': # pragma: no cover
    _run_from_commandline()
