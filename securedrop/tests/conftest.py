# -*- coding: utf-8 -*-

import pretty_bad_protocol as gnupg
import logging
from hypothesis import settings
import os
import io
import json
import psutil
import pytest
import shutil
import signal
import subprocess

try:
    import configparser
except ImportError:
    from six.moves import configparser  # renamed in Python 3

from flask import url_for
from pyotp import TOTP

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from sdconfig import SDConfig, config as original_config

from os import path

from db import db
from journalist_app import create_app as create_journalist_app
import models
from source_app import create_app as create_source_app
from . import utils

# The PID file for the redis worker is hard-coded below.
# Ideally this constant would be provided by a test harness.
# It has been intentionally omitted from `config.py.example`
# in order to isolate the test vars from prod vars.
TEST_WORKER_PIDFILE = '/tmp/securedrop_test_worker.pid'

# Quiet down gnupg output. (See Issue #2595)
GNUPG_LOG_LEVEL = os.environ.get('GNUPG_LOG_LEVEL', "ERROR")
gnupg._util.log.setLevel(getattr(logging, GNUPG_LOG_LEVEL, logging.ERROR))

# `hypothesis` sets a default deadline of 200 milliseconds before failing tests,
# which doesn't work for integration tests. Turn off deadlines.
settings.register_profile("securedrop", deadline=None)
settings.load_profile("securedrop")


def pytest_addoption(parser):
    parser.addoption("--page-layout", action="store_true",
                     default=False, help="run page layout tests")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--page-layout"):
        return
    skip_page_layout = pytest.mark.skip(
        reason="need --page-layout option to run page layout tests"
    )
    for item in items:
        if "pagelayout" in item.keywords:
            item.add_marker(skip_page_layout)


@pytest.fixture
def hardening(request):
    hardening = models.LOGIN_HARDENING

    def finalizer():
        models.LOGIN_HARDENING = hardening
    request.addfinalizer(finalizer)
    models.LOGIN_HARDENING = True
    return None


@pytest.fixture(scope='session')
def setUpTearDown():
    _start_test_rqworker(original_config)
    yield
    _stop_test_rqworker()
    _cleanup_test_securedrop_dataroot(original_config)


@pytest.fixture(scope='function')
def config(tmpdir):
    '''Clone the module so we can modify it per test.'''

    cnf = SDConfig()

    data = tmpdir.mkdir('data')
    keys = data.mkdir('keys')
    os.chmod(str(keys), 0o700)
    store = data.mkdir('store')
    tmp = data.mkdir('tmp')
    sqlite = data.join('db.sqlite')

    # gpg 2.1+ requires gpg-agent, see #4013
    gpg_agent_config = str(keys.join('gpg-agent.conf'))
    with open(gpg_agent_config, 'w+') as f:
        f.write('allow-loopback-pinentry')

    gpg = gnupg.GPG('gpg2', homedir=str(keys))
    for ext in ['sec', 'pub']:
        with io.open(path.join(path.dirname(__file__),
                               'files',
                               'test_journalist_key.{}'.format(ext))) as f:
            gpg.import_keys(f.read())

    cnf.SECUREDROP_DATA_ROOT = str(data)
    cnf.GPG_KEY_DIR = str(keys)
    cnf.STORE_DIR = str(store)
    cnf.TEMP_DIR = str(tmp)
    cnf.DATABASE_FILE = str(sqlite)

    # create the db file
    subprocess.check_call(['sqlite3', cnf.DATABASE_FILE, '.databases'])

    return cnf


@pytest.fixture(scope='function')
def alembic_config(config):
    base_dir = path.join(path.dirname(__file__), '..')
    migrations_dir = path.join(base_dir, 'alembic')
    ini = configparser.SafeConfigParser()
    ini.read(path.join(base_dir, 'alembic.ini'))

    ini.set('alembic', 'script_location', path.join(migrations_dir))
    ini.set('alembic', 'sqlalchemy.url', 'sqlite:///' + config.DATABASE_FILE)

    alembic_path = path.join(config.SECUREDROP_DATA_ROOT, 'alembic.ini')
    config.TESTING_ALEMBIC_PATH = alembic_path

    with open(alembic_path, 'w') as f:
        ini.write(f)

    return alembic_path


@pytest.fixture(scope='function')
def source_app(config):
    app = create_source_app(config)
    app.config['SERVER_NAME'] = 'localhost.localdomain'
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture(scope='function')
def journalist_app(config):
    app = create_journalist_app(config)
    app.config['SERVER_NAME'] = 'localhost.localdomain'
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture(scope='function')
def test_journo(journalist_app):
    with journalist_app.app_context():
        user, password = utils.db_helper.init_journalist(is_admin=False)
        username = user.username
        otp_secret = user.otp_secret
        return {'journalist': user,
                'username': username,
                'password': password,
                'otp_secret': otp_secret,
                'id': user.id,
                'uuid': user.uuid,
                'first_name': user.first_name,
                'last_name': user.last_name}


@pytest.fixture(scope='function')
def test_admin(journalist_app):
    with journalist_app.app_context():
        user, password = utils.db_helper.init_journalist(is_admin=True)
        username = user.username
        otp_secret = user.otp_secret
        return {'admin': user,
                'username': username,
                'password': password,
                'otp_secret': otp_secret,
                'id': user.id}


@pytest.fixture(scope='function')
def test_source(journalist_app):
    with journalist_app.app_context():
        source, codename = utils.db_helper.init_source()
        return {'source': source,
                'codename': codename,
                'filesystem_id': source.filesystem_id,
                'uuid': source.uuid,
                'id': source.id}


@pytest.fixture(scope='function')
def test_submissions(journalist_app):
    with journalist_app.app_context():
        source, codename = utils.db_helper.init_source()
        utils.db_helper.submit(source, 2)
        return {'source': source,
                'codename': codename,
                'filesystem_id': source.filesystem_id,
                'uuid': source.uuid,
                'submissions': source.submissions}


@pytest.fixture(scope='function')
def test_files(journalist_app, test_journo):
    with journalist_app.app_context():
        source, codename = utils.db_helper.init_source()
        utils.db_helper.submit(source, 2)
        utils.db_helper.reply(test_journo['journalist'], source, 1)
        return {'source': source,
                'codename': codename,
                'filesystem_id': source.filesystem_id,
                'uuid': source.uuid,
                'submissions': source.submissions,
                'replies': source.replies}


@pytest.fixture(scope='function')
def journalist_api_token(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        valid_token = TOTP(test_journo['otp_secret']).now()
        response = app.post(url_for('api.get_token'),
                            data=json.dumps(
                                {'username': test_journo['username'],
                                 'passphrase': test_journo['password'],
                                 'one_time_code': valid_token}),
                            headers=utils.api_helper.get_api_headers())
        return response.json['token']


def _start_test_rqworker(config):
    if not psutil.pid_exists(_get_pid_from_file(TEST_WORKER_PIDFILE)):
        tmp_logfile = io.open('/tmp/test_rqworker.log', 'w')
        subprocess.Popen(['rqworker', config.RQ_WORKER_NAME,
                          '-P', config.SECUREDROP_ROOT,
                          '--pid', TEST_WORKER_PIDFILE,
                          '--logging_level', 'debug',
                          '-v'],
                         stdout=tmp_logfile,
                         stderr=subprocess.STDOUT)


def _stop_test_rqworker():
    rqworker_pid = _get_pid_from_file(TEST_WORKER_PIDFILE)
    if rqworker_pid:
        os.kill(rqworker_pid, signal.SIGTERM)
        try:
            os.remove(TEST_WORKER_PIDFILE)
        except OSError:
            pass


def _get_pid_from_file(pid_file_name):
    try:
        return int(io.open(pid_file_name).read())
    except IOError:
        return -1


def _cleanup_test_securedrop_dataroot(config):
    # Keyboard interrupts or dropping to pdb after a test failure sometimes
    # result in the temporary test SecureDrop data root not being deleted.
    try:
        shutil.rmtree(config.SECUREDROP_DATA_ROOT)
    except OSError:
        pass
