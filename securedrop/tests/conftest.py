# -*- coding: utf-8 -*-

import pretty_bad_protocol as gnupg
import logging
import os
import io
import json
import psutil
import pytest
import shutil
import signal
import subprocess

from ConfigParser import SafeConfigParser
from flask import url_for
from pyotp import TOTP

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from sdconfig import JournalistInterfaceConfig, SourceInterfaceConfig

from os import path

from db import db
from journalist_app import create_app as create_journalist_app
import models
from source_app import create_app as create_source_app
import utils

# The PID file for the redis worker is hard-coded below.
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
    default_config = JournalistInterfaceConfig()
    _start_test_rqworker(default_config)
    yield
    _stop_test_rqworker()
    _cleanup_test_securedrop_dataroot(default_config)


@pytest.fixture(scope='session')
def gpg_key_dir():
    '''
    Create one "master" keyring that we copy on a per-config basis. We do this
    because importing keys with GPG is *slow* and this massively speeds up
    tests.
    '''
    gpg_home = '/tmp/sd-test-gpg-home'
    if not path.exists(gpg_home):
        os.mkdir(gpg_home)

    # gpg 2.1+ requires gpg-agent, see #4013
    gpg_agent_config = path.join(gpg_home, 'gpg-agent.conf')
    with open(gpg_agent_config, 'w+') as f:
        f.write('allow-loopback-pinentry')

    gpg = gnupg.GPG('gpg2', homedir=gpg_home)
    for ext in ['sec', 'pub']:
        with io.open(path.join(path.dirname(__file__),
                               'files',
                               'test_journalist_key.{}'.format(ext))) as f:
            gpg.import_keys(f.read())

    return gpg_home


@pytest.fixture(scope='function')
def _config(tmpdir, gpg_key_dir):
    j_cnf = JournalistInterfaceConfig()
    s_cnf = SourceInterfaceConfig()

    data = tmpdir.mkdir('data')
    j_cnf.SECUREDROP_DATA_ROOT = str(data)
    s_cnf.SECUREDROP_DATA_ROOT = str(data)

    data.mkdir('store')  # for cnf.STORE_DIR
    data.mkdir('tmp')  # for cnf.TEMP_DIR

    keys = str(data.join('keys'))  # for cnf.GPG_KEY_DIR
    shutil.copytree(gpg_key_dir, keys)
    os.chmod(str(keys), 0o700)  # to pass app runtime checks

    # create the db file
    subprocess.check_call(['sqlite3', j_cnf.DATABASE_FILE, '.databases'])

    return (j_cnf, s_cnf)


@pytest.fixture(scope='function')
def journalist_config(_config):
    return _config[0]


@pytest.fixture(scope='function')
def source_config(_config):
    return _config[1]


@pytest.fixture(scope='function')
def alembic_config(journalist_config):
    base_dir = path.join(path.dirname(__file__), '..')
    migrations_dir = path.join(base_dir, 'alembic')
    ini = SafeConfigParser()
    ini.read(path.join(base_dir, 'alembic.ini'))

    ini.set('alembic', 'script_location', path.join(migrations_dir))
    ini.set('alembic', 'sqlalchemy.url',
            'sqlite:///' + journalist_config.DATABASE_FILE)

    alembic_path = path.join(journalist_config.SECUREDROP_DATA_ROOT,
                             'alembic.ini')
    journalist_config.TESTING_ALEMBIC_PATH = alembic_path

    with open(alembic_path, 'w') as f:
        ini.write(f)

    return alembic_path


@pytest.fixture(scope='function')
def source_app(source_config):
    app = create_source_app(source_config)
    app.config['SERVER_NAME'] = 'localhost'
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture(scope='function')
def journalist_app(journalist_config):
    app = create_journalist_app(journalist_config)
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
                'id': user.id,
                'uuid': user.uuid}


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
def test_files(journalist_app, test_journo, journalist_config):
    with journalist_app.app_context():
        source, codename = utils.db_helper.init_source()
        utils.db_helper.submit(source, 2)
        utils.db_helper.reply(test_journo['journalist'], source, 1,
                              journalist_config)
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
