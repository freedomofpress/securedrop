# -*- coding: utf-8 -*-

import errno
import gnupg
import logging
import os
import io
import json
import psutil
import pytest
import requests
import shutil
import signal
import socket
import subprocess
import time
import traceback

from ConfigParser import SafeConfigParser
from datetime import datetime
from flask import url_for
from multiprocessing import Process
from pyotp import TOTP
from requests.exceptions import ConnectionError
from selenium import webdriver as selenium_webdriver
from selenium.webdriver.firefox import firefox_binary

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from sdconfig import SDConfig, config as original_config

from os import path

from db import db
from journalist_app import create_app as create_journalist_app
from source_app import create_app as create_source_app
import utils

# The PID file for the redis worker is hard-coded below.
# Ideally this constant would be provided by a test harness.
# It has been intentionally omitted from `config.py.example`
# in order to isolate the test vars from prod vars.
TEST_WORKER_PIDFILE = '/tmp/securedrop_test_worker.pid'

LOG_DIR = path.join(path.dirname(__file__), 'log')

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

    # create the db file
    subprocess.check_call(['sqlite3', cnf.DATABASE_FILE, '.databases'])

    return cnf


@pytest.fixture(scope='function')
def pre_create_config(config):
    '''This is so the configs can be altered on a per-test basis for tests
       that use the live app fixutres. We need this "dependency injection"
       because Python multithreading won't let us manipulate config values
       of the `Process`'s while the apps are running.
    '''
    # In the default case we don't need to do anything.
    pass


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
    app.config['SERVER_NAME'] = 'localhost'
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture(scope='function')
def journalist_app(config):
    app = create_journalist_app(config)
    app.config['SERVER_NAME'] = 'localhost'
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
        observed_response = json.loads(response.data)
        return observed_response['token']


@pytest.fixture(scope='function')
def live_journalist_app(config, mocker, pre_create_config):
    app = create_journalist_app(config)
    with app.app_context():
        db.create_all()
    # patch to avoid intermittent errors
    mocker.patch('models.Journalist.verify_token', return_value=True)
    signal.signal(signal.SIGUSR1, lambda _, s: traceback.print_stack(s))
    port = _unused_port()
    location = 'http://localhost:{}'.format(port)
    proc = Process(target=lambda: run_live_app(app, port))
    proc.start()
    _wait_for_app_liveness(location)
    yield {'location': location,
           'process': proc,
           'app': app}
    proc.terminate()


@pytest.fixture(scope='function')
def live_source_app(config, mocker, pre_create_config):
    app = create_source_app(config)
    with app.app_context():
        db.create_all()
    # patch to avoid intermittent errors
    mocker.patch('source_app.main.get_entropy_estimate', return_value=8192)
    signal.signal(signal.SIGUSR1, lambda _, s: traceback.print_stack(s))
    port = _unused_port()
    location = 'http://localhost:{}'.format(port)
    proc = Process(target=lambda: run_live_app(app, port))
    proc.start()
    _wait_for_app_liveness(location)
    yield {'location': location,
           'process': proc,
           'app': app}
    proc.terminate()


@pytest.fixture(scope='module')
def driver_binary():
    with open(path.join(LOG_DIR, 'firefox.log'), 'a') as log_file:
        log_file.write('\n\n[{}] Running Functional Tests\n'
                       .format(datetime.now()))
        log_file.flush()
        yield firefox_binary.FirefoxBinary(log_file=log_file)


@pytest.fixture(scope='module')
def webdriver(driver_binary):
    # see https://review.openstack.org/#/c/375258/ and the
    # associated issues for background on why this is necessary
    connrefused_retry_count = 3
    connrefused_retry_interval = 5

    for i in range(connrefused_retry_count + 1):
        try:
            driver = selenium_webdriver.Firefox(firefox_binary=driver_binary,
                                                firefox_profile=None)
            if i > 0:
                # i==0 is normal behavior without connection refused.
                print('NOTE: Retried {} time(s) due to '
                      'connection refused.'.format(i))
            return driver
        except socket.error as socket_error:
            if (socket_error.errno == errno.ECONNREFUSED
                    and i < connrefused_retry_count):
                time.sleep(connrefused_retry_interval)
                continue
            raise


def _wait_for_app_liveness(location):
    for tick in range(30):
        try:
            requests.get(location)
        except ConnectionError:
            time.sleep(1)
        else:
            return
    raise Exception('Failed to reach live server at {} after 30 seconds.'
                    .format(location))


def run_live_app(app, port):
    app.run(
        port=port,
        debug=True,
        use_reloader=False,
        threaded=True,
    )


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


def _unused_port():
    s = socket.socket()
    s.bind(("localhost", 0))
    port = s.getsockname()[1]
    s.close()
    return port
