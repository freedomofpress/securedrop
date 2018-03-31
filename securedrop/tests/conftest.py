# -*- coding: utf-8 -*-

import gnupg
import logging
import os
import io
import psutil
import pytest
import shutil
import signal
import subprocess

from ConfigParser import SafeConfigParser

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from sdconfig import SDConfig, config as original_config

from os import path

from db import db
from journalist_app import create_app as create_journalist_app
from source_app import create_app as create_source_app
import utils

# TODO: the PID file for the redis worker is hard-coded below.
# Ideally this constant would be provided by a test harness.
# It has been intentionally omitted from `config.py.example`
# in order to isolate the test vars from prod vars.
TEST_WORKER_PIDFILE = '/tmp/securedrop_test_worker.pid'

# Quiet down gnupg output. (See Issue #2595)
gnupg_logger = logging.getLogger(gnupg.__name__)
gnupg_logger.setLevel(logging.ERROR)
valid_levels = {'INFO': logging.INFO, 'DEBUG': logging.DEBUG}
gnupg_logger.setLevel(
   valid_levels.get(os.environ.get('GNUPG_LOG_LEVEL', ""), logging.ERROR)
)


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

    gpg = gnupg.GPG(homedir=str(keys))
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

    return cnf


@pytest.fixture(scope='function')
def alembic_config(config):
    base_dir = path.join(path.dirname(__file__), '..')
    migrations_dir = path.join(base_dir, 'alembic')
    ini = SafeConfigParser()
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
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture(scope='function')
def journalist_app(config):
    app = create_journalist_app(config)
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
                'id': user.id}


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
        filesystem_id = source.filesystem_id
        return {'source': source,
                'codename': codename,
                'filesystem_id': filesystem_id}


def _start_test_rqworker(config):
    if not psutil.pid_exists(_get_pid_from_file(TEST_WORKER_PIDFILE)):
        tmp_logfile = io.open('/tmp/test_rqworker.log', 'w')
        subprocess.Popen(['rqworker', 'test',
                          '-P', config.SECUREDROP_ROOT,
                          '--pid', TEST_WORKER_PIDFILE],
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
        return None


def _cleanup_test_securedrop_dataroot(config):
    # Keyboard interrupts or dropping to pdb after a test failure sometimes
    # result in the temporary test SecureDrop data root not being deleted.
    try:
        shutil.rmtree(config.SECUREDROP_DATA_ROOT)
    except OSError:
        pass
