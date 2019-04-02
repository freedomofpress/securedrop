# -*- coding: utf-8 -*-
import os
import pytest
import time

from contextlib import contextmanager
from datetime import datetime, timedelta
from flask import url_for
from pyotp import TOTP

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from models import Journalist, BadTokenException
from .utils import login_user
from .utils.instrument import InstrumentedApp


@contextmanager
def totp_window():
    '''To ensure we have enough time during a single TOTP window to do the
       whole test, optionally sleep.
    '''

    now = datetime.now()
    # `or 30` to ensure we don't have a zero-length window
    seconds_left_in_window = ((30 - now.second) % 30) or 30

    window_end = now.replace(microsecond=0) + \
        timedelta(seconds=seconds_left_in_window)
    window_end_delta = window_end - now

    # if we have less than 5 seconds left in this window, sleep to wait for
    # the next window
    if window_end_delta < timedelta(seconds=5):
        timeout = window_end_delta.seconds + \
            window_end_delta.microseconds / 1000000.0
        time.sleep(timeout)
        window_end = window_end + timedelta(seconds=30)

    yield

    # This check ensures that the token was used during the same window
    # in the event that the app's logic only checks for token reuse if the
    # token was valid.
    now = datetime.now()
    assert now < window_end


def test_totp_reuse_protections(journalist_app, test_journo, hardening):
    """Ensure that logging in twice with the same TOTP token fails."""
    with totp_window():
        token = TOTP(test_journo['otp_secret']).now()

        with journalist_app.test_client() as app:
            login_user(app, test_journo)
            resp = app.get(url_for('main.logout'), follow_redirects=True)
            assert resp.status_code == 200

        with journalist_app.test_client() as app:
            resp = app.post(url_for('main.login'),
                            data=dict(username=test_journo['username'],
                                      password=test_journo['password'],
                                      token=token))
            assert resp.status_code == 200
            text = resp.data.decode('utf-8')
            assert "Login failed" in text


def test_totp_reuse_protections2(journalist_app, test_journo, hardening):
    """More granular than the preceeding test, we want to make sure the right
       exception is being raised in the right place.
    """

    with totp_window():
        token = TOTP(test_journo['otp_secret']).now()

        with journalist_app.app_context():
            Journalist.login(test_journo['username'],
                             test_journo['password'],
                             token)
            with pytest.raises(BadTokenException):
                Journalist.login(test_journo['username'],
                                 test_journo['password'],
                                 token)


def test_bad_token_fails_to_verify_on_admin_new_user_two_factor_page(
        journalist_app, test_admin, hardening):
    '''Regression test for
       https://github.com/freedomofpress/securedrop/pull/1692
    '''

    invalid_token = '000000'

    with totp_window():
        with journalist_app.test_client() as app:
            login_user(app, test_admin)
            # Submit the token once
            with InstrumentedApp(journalist_app) as ins:
                resp = app.post(url_for('admin.new_user_two_factor',
                                        uid=test_admin['id']),
                                data=dict(token=invalid_token))

                assert resp.status_code == 200
                ins.assert_message_flashed(
                    'Could not verify token in two-factor authentication.',
                    'error')

        # last_token should be set to the token we just tried to use
        with journalist_app.app_context():
            admin = Journalist.query.get(test_admin['id'])
            assert admin.last_token == invalid_token

        with journalist_app.test_client() as app:
            login_user(app, test_admin)
            # Submit the same invalid token again
            with InstrumentedApp(journalist_app) as ins:
                resp = app.post(url_for('admin.new_user_two_factor',
                                        uid=test_admin['id']),
                                data=dict(token=invalid_token))
                ins.assert_message_flashed(
                    'Could not verify token in two-factor authentication.',
                    'error')


def test_bad_token_fails_to_verify_on_new_user_two_factor_page(
        journalist_app, test_journo, hardening):
    '''Regression test for
       https://github.com/freedomofpress/securedrop/pull/1692
    '''
    invalid_token = '000000'

    with totp_window():
        with journalist_app.test_client() as app:
            login_user(app, test_journo)
            # Submit the token once
            with InstrumentedApp(journalist_app) as ins:
                resp = app.post(url_for('account.new_two_factor'),
                                data=dict(token=invalid_token))

                assert resp.status_code == 200
                ins.assert_message_flashed(
                    'Could not verify token in two-factor authentication.',
                    'error')

        # last_token should be set to the token we just tried to use
        with journalist_app.app_context():
            journo = Journalist.query.get(test_journo['id'])
            assert journo.last_token == invalid_token

        with journalist_app.test_client() as app:
            login_user(app, test_journo)

            # Submit the same invalid token again
            with InstrumentedApp(journalist_app) as ins:
                resp = app.post(url_for('account.new_two_factor'),
                                data=dict(token=invalid_token))
                ins.assert_message_flashed(
                    'Could not verify token in two-factor authentication.',
                    'error')
