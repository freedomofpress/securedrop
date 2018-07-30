# -*- coding: utf-8 -*-
import os
import pytest
import io
import random
import unittest
import zipfile
import base64

from base64 import b64decode
from cStringIO import StringIO
from io import BytesIO
from flask import url_for, escape, session, current_app, g
from flask_testing import TestCase
from mock import patch
from pyotp import TOTP
from sqlalchemy.sql.expression import func
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError

import crypto_util
import models
import journalist
import journalist_app as journalist_app_module
import utils

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from sdconfig import SDConfig, config

from db import db
from models import (InvalidPasswordLength, Journalist, Reply, Source,
                    Submission)
from utils.instrument import InstrumentedApp

# Smugly seed the RNG for deterministic testing
random.seed('¯\_(ツ)_/¯')

VALID_PASSWORD = 'correct horse battery staple generic passphrase hooray'
VALID_PASSWORD_2 = 'another correct horse battery staple generic passphrase'

# These are factored out of the tests because some test have a
# postive/negative case under varying conditions, and we don't want
# false postives after modifying a string in the application.
EMPTY_REPLY_TEXT = "You cannot send an empty reply."
ADMIN_LINK = '<a href="/admin/" id="link-admin-index">'


def _login_user(app, username, password, otp_secret):
    resp = app.post(url_for('main.login'),
                    data={'username': username,
                          'password': password,
                          'token': TOTP(otp_secret).now()},
                    follow_redirects=True)
    assert resp.status_code == 200
    assert hasattr(g, 'user')  # ensure logged in


def test_user_with_whitespace_in_username_can_login(journalist_app):
    # Create a user with whitespace at the end of the username
    with journalist_app.app_context():
        username_with_whitespace = 'journalist '
        user, password = utils.db_helper.init_journalist(is_admin=False)
        otp_secret = user.otp_secret
        user.username = username_with_whitespace
        db.session.add(user)
        db.session.commit()

    # Verify that user is able to login successfully
    with journalist_app.test_client() as app:
        _login_user(app, username_with_whitespace, password,
                    otp_secret)


def test_make_password(journalist_app):
    with patch.object(crypto_util.CryptoUtil, 'genrandomid',
                      side_effect=['bad', VALID_PASSWORD]):
        fake_config = SDConfig()
        with journalist_app.test_request_context('/'):
            password = journalist_app_module.utils.make_password(fake_config)
            assert password == VALID_PASSWORD


def test_reply_error_logging(journalist_app, test_journo, test_source):
    exception_class = StaleDataError
    exception_msg = 'Potentially sensitive content!'

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'],
                    test_journo['password'], test_journo['otp_secret'])
        with patch.object(journalist_app.logger, 'error') \
                as mocked_error_logger:
            with patch.object(db.session, 'commit',
                              side_effect=exception_class(exception_msg)):
                resp = app.post(
                    url_for('main.reply'),
                    data={'filesystem_id': test_source['filesystem_id'],
                          'message': '_'},
                    follow_redirects=True)
                assert resp.status_code == 200

    # Notice the "potentially sensitive" exception_msg is not present in
    # the log event.
    mocked_error_logger.assert_called_once_with(
        "Reply from '{}' (ID {}) failed: {}!".format(
            test_journo['username'],
            test_journo['id'],
            exception_class))


def test_reply_error_flashed_message(journalist_app, test_journo, test_source):
    exception_class = StaleDataError

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'],
                    test_journo['password'], test_journo['otp_secret'])

        with InstrumentedApp(app) as ins:
            with patch.object(db.session, 'commit',
                              side_effect=exception_class()):
                app.post(url_for('main.reply'),
                         data={'filesystem_id': test_source['filesystem_id'],
                               'message': '_'})

            ins.assert_message_flashed(
                'An unexpected error occurred! Please '
                'inform your administrator.', 'error')


def test_empty_replies_are_rejected(journalist_app, test_journo, test_source):
    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'],
                    test_journo['password'], test_journo['otp_secret'])
        resp = app.post(url_for('main.reply'),
                        data={'filesystem_id': test_source['filesystem_id'],
                              'message': ''},
                        follow_redirects=True)

        text = resp.data.decode('utf-8')
        assert EMPTY_REPLY_TEXT in text


def test_nonempty_replies_are_accepted(journalist_app, test_journo,
                                       test_source):
    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'],
                    test_journo['password'], test_journo['otp_secret'])
        resp = app.post(url_for('main.reply'),
                        data={'filesystem_id': test_source['filesystem_id'],
                              'message': '_'},
                        follow_redirects=True)

        text = resp.data.decode('utf-8')
        assert EMPTY_REPLY_TEXT not in text


def test_unauthorized_access_redirects_to_login(journalist_app):
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            resp = app.get(url_for('main.index'))
            ins.assert_redirects(resp, url_for('main.login'))


def test_login_throttle(journalist_app, test_journo):
    # Overwrite the default value used during testing
    models.LOGIN_HARDENING = True
    try:
        with journalist_app.test_client() as app:
            for _ in range(Journalist._MAX_LOGIN_ATTEMPTS_PER_PERIOD):
                resp = app.post(
                    url_for('main.login'),
                    data=dict(username=test_journo['username'],
                              password='invalid',
                              token='invalid'))
                assert resp.status_code == 200
                text = resp.data.decode('utf-8')
                assert "Login failed" in text

            resp = app.post(
                url_for('main.login'),
                data=dict(username=test_journo['username'],
                          password='invalid',
                          token='invalid'))
            assert resp.status_code == 200
            text = resp.data.decode('utf-8')
            assert ("Please wait at least {} seconds".format(
                Journalist._LOGIN_ATTEMPT_PERIOD) in text)
    finally:
        models.LOGIN_HARDENING = False


def test_login_throttle_is_not_global(journalist_app, test_journo, test_admin):
    """The login throttling should be per-user, not global. Global login
    throttling can prevent all users logging into the application."""

    # Overwrite the default value used during testing
    # Note that this may break other tests if doing parallel testing
    models.LOGIN_HARDENING = True
    try:
        with journalist_app.test_client() as app:
            for _ in range(Journalist._MAX_LOGIN_ATTEMPTS_PER_PERIOD):
                resp = app.post(
                    url_for('main.login'),
                    data=dict(username=test_journo['username'],
                              password='invalid',
                              token='invalid'))
                assert resp.status_code == 200
                text = resp.data.decode('utf-8')
                assert "Login failed" in text

            resp = app.post(
                url_for('main.login'),
                data=dict(username=test_journo['username'],
                          password='invalid',
                          token='invalid'))
            assert resp.status_code == 200
            text = resp.data.decode('utf-8')
            assert ("Please wait at least {} seconds".format(
                Journalist._LOGIN_ATTEMPT_PERIOD) in text)

            # A different user should be able to login
            resp = app.post(
                url_for('main.login'),
                data=dict(username=test_admin['username'],
                          password=test_admin['password'],
                          token=TOTP(test_admin['otp_secret']).now()),
                follow_redirects=True)
            assert resp.status_code == 200
            text = resp.data.decode('utf-8')
            assert "Sources" in text
    finally:
        models.LOGIN_HARDENING = False


def test_login_invalid_credentials(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        resp = app.post(url_for('main.login'),
                        data=dict(username=test_journo['username'],
                                  password='invalid',
                                  token='mocked'))
    assert resp.status_code == 200
    text = resp.data.decode('utf-8')
    assert "Login failed" in text


def test_validate_redirect(journalist_app):
    with journalist_app.test_client() as app:
        resp = app.post(url_for('main.index'), follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Login to access" in text


def test_login_valid_credentials(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        resp = app.post(
            url_for('main.login'),
            data=dict(username=test_journo['username'],
                      password=test_journo['password'],
                      token=TOTP(test_journo['otp_secret']).now()),
            follow_redirects=True)
    assert resp.status_code == 200  # successful login redirects to index
    text = resp.data.decode('utf-8')
    assert "Sources" in text
    assert "No documents have been submitted!" in text


def test_admin_login_redirects_to_index(journalist_app, test_admin):
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for('main.login'),
                data=dict(username=test_admin['username'],
                          password=test_admin['password'],
                          token=TOTP(test_admin['otp_secret']).now()),
                follow_redirects=False)
            ins.assert_redirects(resp, url_for('main.index'))


def test_user_login_redirects_to_index(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for('main.login'),
                data=dict(username=test_journo['username'],
                          password=test_journo['password'],
                          token=TOTP(test_journo['otp_secret']).now()),
                follow_redirects=False)
            ins.assert_redirects(resp, url_for('main.index'))


def test_admin_has_link_to_edit_account_page_in_index_page(journalist_app,
                                                           test_admin):
    with journalist_app.test_client() as app:
        resp = app.post(
            url_for('main.login'),
            data=dict(username=test_admin['username'],
                      password=test_admin['password'],
                      token=TOTP(test_admin['otp_secret']).now()),
            follow_redirects=True)
    edit_account_link = ('<a href="/account/account" '
                         'id="link-edit-account">')
    text = resp.data.decode('utf-8')
    assert edit_account_link in text


def test_user_has_link_to_edit_account_page_in_index_page(journalist_app,
                                                          test_journo):
    with journalist_app.test_client() as app:
        resp = app.post(
            url_for('main.login'),
            data=dict(username=test_journo['username'],
                      password=test_journo['password'],
                      token=TOTP(test_journo['otp_secret']).now()),
            follow_redirects=True)
    edit_account_link = ('<a href="/account/account" '
                         'id="link-edit-account">')
    text = resp.data.decode('utf-8')
    assert edit_account_link in text


def test_admin_has_link_to_admin_index_page_in_index_page(journalist_app,
                                                          test_admin):
    with journalist_app.test_client() as app:
        resp = app.post(
            url_for('main.login'),
            data=dict(username=test_admin['username'],
                      password=test_admin['password'],
                      token=TOTP(test_admin['otp_secret']).now()),
            follow_redirects=True)
    text = resp.data.decode('utf-8')
    assert ADMIN_LINK in text


def test_user_lacks_link_to_admin_index_page_in_index_page(journalist_app,
                                                           test_journo):
    with journalist_app.test_client() as app:
        resp = app.post(
            url_for('main.login'),
            data=dict(username=test_journo['username'],
                      password=test_journo['password'],
                      token=TOTP(test_journo['otp_secret']).now()),
            follow_redirects=True)
    text = resp.data.decode('utf-8')
    assert ADMIN_LINK not in text


def test_admin_logout_redirects_to_index(journalist_app, test_admin):
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            _login_user(app, test_admin['username'],
                        test_admin['password'],
                        test_admin['otp_secret'])
            resp = app.get(url_for('main.logout'))
            ins.assert_redirects(resp, url_for('main.index'))


def test_user_logout_redirects_to_index(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            _login_user(app, test_journo['username'],
                        test_journo['password'],
                        test_journo['otp_secret'])
            resp = app.get(url_for('main.logout'))
            ins.assert_redirects(resp, url_for('main.index'))


def test_admin_index(journalist_app, test_admin):
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])
        resp = app.get(url_for('admin.index'))
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Admin Interface" in text


def test_admin_delete_user(journalist_app, test_admin, test_journo):
    # Verify journalist is in the database
    with journalist_app.app_context():
        assert Journalist.query.get(test_journo['id']) is not None

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])
        resp = app.post(url_for('admin.delete_user',
                                user_id=test_journo['id']),
                        follow_redirects=True)

        # Assert correct interface behavior
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert escape("Deleted user '{}'".format(test_journo['username'])) \
            in text

    # Verify journalist is no longer in the database
    with journalist_app.app_context():
        assert Journalist.query.get(test_journo['id']) is None


def test_admin_cannot_delete_self(journalist_app, test_admin, test_journo):
    # Verify journalist is in the database
    with journalist_app.app_context():
        assert Journalist.query.get(test_journo['id']) is not None

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])
        resp = app.post(url_for('admin.delete_user',
                                user_id=test_admin['id']),
                        follow_redirects=True)

        # Assert correct interface behavior
        assert resp.status_code == 403

        resp = app.get(url_for('admin.index'), follow_redirects=True)
        assert resp.status_code == 200
        text = resp.data.decode('utf-8')
        assert "Admin Interface" in text

        # The user can be edited and deleted
        assert escape("Edit user {}".format(test_journo['username'])) in text
        assert escape("Delete user {}".format(test_journo['username'])) in text
        # The admin can be edited but cannot deleted
        assert escape("Edit user {}".format(test_admin['username'])) in text
        assert escape("Delete user {}".format(test_admin['username'])) \
            not in text


def test_admin_edits_user_password_success_response(journalist_app,
                                                    test_admin):
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        resp = app.post(url_for('admin.new_password',
                                user_id=test_admin['id']),
                        data=dict(password=VALID_PASSWORD_2),
                        follow_redirects=True)
        assert resp.status_code == 200

        text = resp.data.decode('utf-8')
        assert 'Password updated.' in text
        assert VALID_PASSWORD_2 in text


def test_admin_deletes_invalid_user_404(journalist_app, test_admin):
    with journalist_app.app_context():
        invalid_id = db.session.query(func.max(Journalist.id)).scalar() + 1

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])
        resp = app.post(url_for('admin.delete_user', user_id=invalid_id))
        assert resp.status_code == 404


def test_admin_edits_user_password_error_response(journalist_app,
                                                  test_admin,
                                                  test_journo):
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        with patch('sqlalchemy.orm.scoping.scoped_session.commit',
                   side_effect=Exception()):
            resp = app.post(url_for('admin.new_password',
                                    user_id=test_journo['id']),
                            data=dict(password=VALID_PASSWORD_2),
                            follow_redirects=True)

        text = resp.data.decode('utf-8')
        assert ('There was an error, and the new password might not have '
                'been saved correctly.') in text


def test_user_edits_password_success_response(journalist_app, test_journo):
    original_hardening = models.LOGIN_HARDENING
    try:
        # Set this to false because we login then immedialtey reuse the same
        # token when authenticating to change the password. This triggers login
        # hardening measures.
        models.LOGIN_HARDENING = False

        with journalist_app.test_client() as app:
            _login_user(app, test_journo['username'], test_journo['password'],
                        test_journo['otp_secret'])
            token = TOTP(test_journo['otp_secret']).now()
            resp = app.post(url_for('account.new_password'),
                            data=dict(current_password=test_journo['password'],
                                      token=token,
                                      password=VALID_PASSWORD_2),
                            follow_redirects=True)

            text = resp.data.decode('utf-8')
            assert "Password updated." in text
            assert VALID_PASSWORD_2 in text
    finally:
        models.LOGIN_HARDENING = original_hardening


def test_user_edits_password_expires_session(journalist_app, test_journo):
    original_hardening = models.LOGIN_HARDENING
    try:
        # Set this to false because we login then immedialtey reuse the same
        # token when authenticating to change the password. This triggers login
        # hardening measures.
        models.LOGIN_HARDENING = False
        with journalist_app.test_client() as app:
            _login_user(app, test_journo['username'], test_journo['password'],
                        test_journo['otp_secret'])
            assert 'uid' in session

            with InstrumentedApp(journalist_app) as ins:
                token = TOTP(test_journo['otp_secret']).now()
                resp = app.post(url_for('account.new_password'),
                                data=dict(
                                    current_password=test_journo['password'],
                                    token=token,
                                    password=VALID_PASSWORD_2))

                ins.assert_redirects(resp, url_for('main.login'))

            # verify the session was expired after the password was changed
            assert 'uid' not in session
    finally:
        models.LOGIN_HARDENING = original_hardening


def test_user_edits_password_error_reponse(journalist_app, test_journo):
    original_hardening = models.LOGIN_HARDENING
    try:
        # Set this to false because we login then immedialtey reuse the same
        # token when authenticating to change the password. This triggers login
        # hardening measures.
        models.LOGIN_HARDENING = False

        with journalist_app.test_client() as app:
            _login_user(app, test_journo['username'], test_journo['password'],
                        test_journo['otp_secret'])

            # patch token verification because there are multiple commits
            # to the database and this isolates the one we want to fail
            with patch.object(Journalist, 'verify_token', return_value=True):
                with patch.object(db.session, 'commit',
                                  side_effect=Exception()):
                    resp = app.post(
                        url_for('account.new_password'),
                        data=dict(current_password=test_journo['password'],
                                  token='mocked',
                                  password=VALID_PASSWORD_2),
                        follow_redirects=True)

            text = resp.data.decode('utf-8')
            assert ('There was an error, and the new password might not have '
                    'been saved correctly.') in text
    finally:
        models.LOGIN_HARDENING = original_hardening


def test_admin_add_user_when_username_already_taken(journalist_app,
                                                    test_admin):
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])
        resp = app.post(url_for('admin.add_user'),
                        data=dict(username=test_admin['username'],
                                  password=VALID_PASSWORD,
                                  is_admin=None))
        text = resp.data.decode('utf-8')
        assert 'already taken' in text


def test_max_password_length():
    """Creating a Journalist with a password that is greater than the
    maximum password length should raise an exception"""
    overly_long_password = VALID_PASSWORD + \
        'a' * (Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1)
    with pytest.raises(InvalidPasswordLength):
        Journalist(username="My Password is Too Big!",
                   password=overly_long_password)


def test_min_password_length():
    """Creating a Journalist with a password that is smaller than the
       minimum password length should raise an exception. This uses the
       magic number 7 below to get around the "diceware-like" requirement
       that may cause a failure before the length check.
    """
    password = ('a ' * 7)[0:(Journalist.MIN_PASSWORD_LEN - 1)]
    with pytest.raises(InvalidPasswordLength):
        Journalist(username="My Password is Too Small!",
                   password=password)


def test_admin_edits_user_password_too_long_warning(journalist_app,
                                                    test_admin,
                                                    test_journo):
    # append a bunch of a's to a diceware password to keep it "diceware-like"
    overly_long_password = VALID_PASSWORD + \
        'a' * (Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1)

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])
        with InstrumentedApp(journalist_app) as ins:
            app.post(
                url_for('admin.new_password', user_id=test_journo['id']),
                data=dict(username=test_journo['username'],
                          is_admin=None,
                          password=overly_long_password),
                follow_redirects=True)

            ins.assert_message_flashed('You submitted a bad password! '
                                       'Password not changed.', 'error')


def test_user_edits_password_too_long_warning(journalist_app, test_journo):
    overly_long_password = VALID_PASSWORD + \
        'a' * (Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1)

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            app.post(
                url_for('account.new_password'),
                data=dict(username=test_journo['username'],
                          is_admin=None,
                          token=TOTP(test_journo['otp_secret']).now(),
                          current_password=test_journo['password'],
                          password=overly_long_password),
                follow_redirects=True)

            ins.assert_message_flashed('You submitted a bad password! '
                                       'Password not changed.', 'error')


def test_admin_add_user_password_too_long_warning(journalist_app, test_admin):
    overly_long_password = VALID_PASSWORD + \
        'a' * (Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1)
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            app.post(
                url_for('admin.add_user'),
                data=dict(username='dellsberg',
                          password=overly_long_password,
                          is_admin=None))

            ins.assert_message_flashed(
                'There was an error with the autogenerated password. User not '
                'created. Please try again.', 'error')


def test_admin_edits_user_invalid_username(
        journalist_app, test_admin, test_journo):
    """Test expected error message when admin attempts to change a user's
    username to a username that is taken by another user."""
    new_username = test_journo['username']
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            app.post(
                url_for('admin.edit_user', user_id=test_admin['id']),
                data=dict(username=new_username, is_admin=None))

            ins.assert_message_flashed(
                'Username "{}" already taken.'.format(new_username),
                'error')


def test_admin_resets_user_hotp_format_non_hexa(
        journalist_app, test_admin, test_journo):

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        journo = test_journo['journalist']
        # guard to ensure check below tests the correct condition
        assert journo.is_totp

        old_secret = journo.otp_secret

        with InstrumentedApp(journalist_app) as ins:
            app.post(url_for('admin.reset_two_factor_hotp'),
                     data=dict(uid=test_journo['id'], otp_secret='ZZ'))

            # fetch altered DB object
            journo = Journalist.query.get(journo.id)

            new_secret = journo.otp_secret
            assert old_secret == new_secret

            # ensure we didn't accidentally enable hotp
            assert journo.is_totp

            ins.assert_message_flashed(
                "Invalid secret format: please only submit letters A-F and "
                "numbers 0-9.", "error")


def test_admin_resets_user_hotp(journalist_app, test_admin, test_journo):
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        journo = test_journo['journalist']
        old_secret = journo.otp_secret

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for('admin.reset_two_factor_hotp'),
                            data=dict(uid=test_journo['id'],
                                      otp_secret=123456))

            # fetch altered DB object
            journo = Journalist.query.get(journo.id)

            new_secret = journo.otp_secret
            assert old_secret != new_secret
            assert not journo.is_totp

            # Redirect to admin 2FA view
            ins.assert_redirects(resp, url_for('admin.new_user_two_factor',
                                               uid=journo.id))


def test_admin_resets_user_hotp_format_odd(journalist_app,
                                           test_admin,
                                           test_journo):
    old_secret = test_journo['otp_secret']

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            app.post(url_for('admin.reset_two_factor_hotp'),
                     data=dict(uid=test_journo['id'], otp_secret='Z'))

            ins.assert_message_flashed(
                "Invalid secret format: "
                "odd-length secret. Did you mistype the secret?", "error")

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo['id'])
    new_secret = user.otp_secret

    assert old_secret == new_secret


def test_admin_resets_user_hotp_error(mocker,
                                      journalist_app,
                                      test_admin,
                                      test_journo):

    bad_secret = '1234'
    error_message = 'SOMETHING WRONG!'
    mocked_error_logger = mocker.patch('journalist.app.logger.error')
    old_secret = test_journo['otp_secret']

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        mocker.patch('models.Journalist.set_hotp_secret',
                     side_effect=TypeError(error_message))

        with InstrumentedApp(journalist_app) as ins:
            app.post(url_for('admin.reset_two_factor_hotp'),
                     data=dict(uid=test_journo['id'], otp_secret=bad_secret))
            ins.assert_message_flashed("An unexpected error occurred! "
                                       "Please inform your administrator.",
                                       "error")

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo['id'])
    new_secret = user.otp_secret

    assert new_secret == old_secret

    mocked_error_logger.assert_called_once_with(
        "set_hotp_secret '{}' (id {}) failed: {}".format(
            bad_secret, test_journo['id'], error_message))


def test_user_resets_hotp(journalist_app, test_journo):
    old_secret = test_journo['otp_secret']
    new_secret = 123456

    # Precondition
    assert new_secret != old_secret

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for('account.reset_two_factor_hotp'),
                            data=dict(otp_secret=new_secret))
            # should redirect to verification page
            ins.assert_redirects(resp, url_for('account.new_two_factor'))

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo['id'])
    new_secret = user.otp_secret

    assert old_secret != new_secret


def test_user_resets_user_hotp_format_odd(journalist_app, test_journo):
    old_secret = test_journo['otp_secret']

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            app.post(url_for('account.reset_two_factor_hotp'),
                     data=dict(otp_secret='123'))
            ins.assert_message_flashed(
                "Invalid secret format: "
                "odd-length secret. Did you mistype the secret?", "error")

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo['id'])
    new_secret = user.otp_secret

    assert old_secret == new_secret


def test_user_resets_user_hotp_format_non_hexa(journalist_app, test_journo):
    old_secret = test_journo['otp_secret']

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            app.post(url_for('account.reset_two_factor_hotp'),
                     data=dict(otp_secret='ZZ'))
            ins.assert_message_flashed(
                "Invalid secret format: "
                "please only submit letters A-F and numbers 0-9.", "error")

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo['id'])
    new_secret = user.otp_secret

    assert old_secret == new_secret


def test_user_resets_user_hotp_error(mocker,
                                     journalist_app,
                                     test_journo):
    bad_secret = '1234'
    old_secret = test_journo['otp_secret']
    error_message = 'SOMETHING WRONG!'
    mocked_error_logger = mocker.patch('journalist.app.logger.error')

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        mocker.patch('models.Journalist.set_hotp_secret',
                     side_effect=TypeError(error_message))

        with InstrumentedApp(journalist_app) as ins:
            app.post(url_for('account.reset_two_factor_hotp'),
                     data=dict(otp_secret=bad_secret))
            ins.assert_message_flashed(
                "An unexpected error occurred! Please inform your "
                "administrator.", "error")

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo['id'])
    new_secret = user.otp_secret

    assert old_secret == new_secret
    mocked_error_logger.assert_called_once_with(
        "set_hotp_secret '{}' (id {}) failed: {}".format(
            bad_secret, test_journo['id'], error_message))


def test_admin_resets_user_totp(journalist_app, test_admin, test_journo):
    old_secret = test_journo['otp_secret']

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for('admin.reset_two_factor_totp'),
                data=dict(uid=test_journo['id']))
            ins.assert_redirects(
                resp,
                url_for('admin.new_user_two_factor', uid=test_journo['id']))

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo['id'])
    new_secret = user.otp_secret

    assert new_secret != old_secret


def test_user_resets_totp(journalist_app, test_journo):
    old_secret = test_journo['otp_secret']

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for('account.reset_two_factor_totp'))
            # should redirect to verification page
            ins.assert_redirects(resp, url_for('account.new_two_factor'))

    # Re-fetch journalist to get fresh DB instance
    user = Journalist.query.get(test_journo['id'])
    new_secret = user.otp_secret

    assert new_secret != old_secret


def test_admin_resets_hotp_with_missing_otp_secret_key(journalist_app,
                                                       test_admin):
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])
        resp = app.post(url_for('admin.reset_two_factor_hotp'),
                        data=dict(uid=test_admin['id']))

    assert 'Change Secret' in resp.data.decode('utf-8')


def test_admin_new_user_2fa_redirect(journalist_app, test_admin, test_journo):
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(
                url_for('admin.new_user_two_factor', uid=test_journo['id']),
                data=dict(token=TOTP(test_journo['otp_secret']).now()))
            ins.assert_redirects(resp, url_for('admin.index'))


def test_http_get_on_admin_new_user_two_factor_page(
        journalist_app,
        test_admin,
        test_journo):
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])
        resp = app.get(
                url_for('admin.new_user_two_factor', uid=test_journo['id']))
    # any GET req should take a user to the admin.new_user_two_factor page
    assert 'FreeOTP' in resp.data.decode('utf-8')


def test_http_get_on_admin_add_user_page(journalist_app, test_admin):
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])
        resp = app.get(url_for('admin.add_user'))
        # any GET req should take a user to the admin_add_user page
        assert 'ADD USER' in resp.data.decode('utf-8')


def test_admin_add_user(journalist_app, test_admin):
    username = 'dellsberg'

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for('admin.add_user'),
                            data=dict(username=username,
                                      password=VALID_PASSWORD,
                                      is_admin=None))

            new_user = Journalist.query.filter_by(username=username).one()
            ins.assert_redirects(resp, url_for('admin.new_user_two_factor',
                                               uid=new_user.id))


def test_admin_add_user_without_username(journalist_app, test_admin):
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        resp = app.post(url_for('admin.add_user'),
                        data=dict(username='',
                                  password=VALID_PASSWORD,
                                  is_admin=None))

    assert 'This field is required.' in resp.data.decode('utf-8')


def test_admin_add_user_too_short_username(journalist_app, test_admin):
    username = 'a' * (Journalist.MIN_USERNAME_LEN - 1)

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        resp = app.post(url_for('admin.add_user'),
                        data=dict(username=username,
                                  password='pentagonpapers',
                                  password_again='pentagonpapers',
                                  is_admin=None))
        assert ('Field must be at least {} characters long'.format(
                      Journalist.MIN_USERNAME_LEN) in
                resp.data.decode('utf-8'))


def test_admin_add_user_yubikey_odd_length(journalist_app, test_admin):
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        resp = app.post(url_for('admin.add_user'),
                        data=dict(username='dellsberg',
                                  password=VALID_PASSWORD,
                                  password_again=VALID_PASSWORD,
                                  is_admin=None,
                                  is_hotp=True,
                                  otp_secret='123'))
        assert 'HOTP secrets are 40 characters' in resp.data.decode('utf-8')


def test_admin_add_user_yubikey_valid_length(journalist_app, test_admin):
    otp = '1234567890123456789012345678901234567890'

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        resp = app.post(url_for('admin.add_user'),
                        data=dict(username='dellsberg',
                                  password=VALID_PASSWORD,
                                  password_again=VALID_PASSWORD,
                                  is_admin=None,
                                  is_hotp=True,
                                  otp_secret=otp),
                        follow_redirects=True)

    # Should redirect to the token verification page
    assert 'Enable YubiKey (OATH-HOTP)' in resp.data.decode('utf-8')


def test_admin_add_user_yubikey_correct_length_with_whitespace(
        journalist_app,
        test_admin):
    otp = '12 34 56 78 90 12 34 56 78 90 12 34 56 78 90 12 34 56 78 90'

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        resp = app.post(url_for('admin.add_user'),
                        data=dict(username='dellsberg',
                                  password=VALID_PASSWORD,
                                  password_again=VALID_PASSWORD,
                                  is_admin=None,
                                  is_hotp=True,
                                  otp_secret=otp),
                        follow_redirects=True)

    # Should redirect to the token verification page
    assert 'Enable YubiKey (OATH-HOTP)' in resp.data.decode('utf-8')


def test_admin_sets_user_to_admin(journalist_app, test_admin):
    new_user = 'admin-set-user-to-admin-test'

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        resp = app.post(url_for('admin.add_user'),
                        data=dict(username=new_user,
                                  password=VALID_PASSWORD,
                                  is_admin=None))
        assert resp.status_code in (200, 302)

        journo = Journalist.query.filter_by(username=new_user).one()
        # precondition check
        assert journo.is_admin is False

        resp = app.post(url_for('admin.edit_user', user_id=journo.id),
                        data=dict(is_admin=True))
        assert resp.status_code in (200, 302)

        journo = Journalist.query.filter_by(username=new_user).one()
        assert journo.is_admin is True


def test_admin_renames_user(journalist_app, test_admin):
    new_user = 'admin-renames-user-test'

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        resp = app.post(url_for('admin.add_user'),
                        data=dict(username=new_user,
                                  password=VALID_PASSWORD,
                                  is_admin=None))
        assert resp.status_code in (200, 302)
        journo = Journalist.query.filter(Journalist.username == new_user).one()

        new_user = new_user + 'a'
        resp = app.post(url_for('admin.edit_user', user_id=journo.id),
                        data=dict(username=new_user))
    assert resp.status_code in (200, 302), resp.data.decode('utf-8')

    # the following will throw an exception if new_user is not found
    # therefore asserting it has been created
    Journalist.query.filter(Journalist.username == new_user).one()


def test_admin_add_user_integrity_error(journalist_app, test_admin, mocker):
    mocked_error_logger = mocker.patch(
            'journalist_app.admin.current_app.logger.error')
    mocker.patch('journalist_app.admin.Journalist',
                 side_effect=IntegrityError('STATEMENT', 'PARAMETERS', None))

    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            app.post(url_for('admin.add_user'),
                     data=dict(username='username',
                               password=VALID_PASSWORD,
                               is_admin=None))
            ins.assert_message_flashed(
                "An error occurred saving this user to the database."
                " Please inform your administrator.",
                "error")

    log_event = mocked_error_logger.call_args[0][0]
    assert ("Adding user 'username' failed: (__builtin__.NoneType) "
            "None [SQL: 'STATEMENT'] [parameters: 'PARAMETERS']") in log_event


def test_logo_upload_with_valid_image_succeeds(journalist_app, test_admin):
    # Save original logo to restore after test run
    logo_image_location = os.path.join(config.SECUREDROP_ROOT,
                                       "static/i/logo.png")
    with io.open(logo_image_location, 'rb') as logo_file:
        original_image = logo_file.read()

    try:
        with journalist_app.test_client() as app:
            _login_user(app, test_admin['username'], test_admin['password'],
                        test_admin['otp_secret'])
            # Create 1px * 1px 'white' PNG file from its base64 string
            form = journalist_app_module.forms.LogoForm(
                logo=(BytesIO(base64.decodestring
                      ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQ"
                       "VR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=")), 'test.png')
            )
            with InstrumentedApp(journalist_app) as ins:
                app.post(url_for('admin.manage_config'),
                         data=form.data,
                         follow_redirects=True)

                ins.assert_message_flashed("Image updated.", "logo-success")
    finally:
        # Restore original image to logo location for subsequent tests
        with io.open(logo_image_location, 'wb') as logo_file:
            logo_file.write(original_image)


def test_logo_upload_with_invalid_filetype_fails(journalist_app, test_admin):
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        form = journalist_app_module.forms.LogoForm(
            logo=(StringIO('filedata'), 'bad.exe')
        )
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for('admin.manage_config'),
                            data=form.data,
                            follow_redirects=True)
            ins.assert_message_flashed("You can only upload PNG image files.",
                                       "logo-error")
        text = resp.data.decode('utf-8')
        assert "You can only upload PNG image files." in text


def test_creation_of_ossec_test_log_event(journalist_app, test_admin, mocker):
    mocked_error_logger = mocker.patch('journalist.app.logger.error')
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])
        app.get(url_for('admin.ossec_test'))

    mocked_error_logger.assert_called_once_with(
        "This is a test OSSEC alert"
    )


def test_logo_upload_with_empty_input_field_fails(journalist_app, test_admin):
    with journalist_app.test_client() as app:
        _login_user(app, test_admin['username'], test_admin['password'],
                    test_admin['otp_secret'])

        form = journalist_app_module.forms.LogoForm(
            logo=(StringIO(''), '')
        )

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for('admin.manage_config'),
                            data=form.data,
                            follow_redirects=True)

            ins.assert_message_flashed("File required.", "logo-error")
    assert 'File required.' in resp.data.decode('utf-8')


def test_admin_page_restriction_http_gets(journalist_app, test_journo):
    admin_urls = [url_for('admin.index'), url_for('admin.add_user'),
                  url_for('admin.edit_user', user_id=test_journo['id'])]

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])
        for admin_url in admin_urls:
            resp = app.get(admin_url)
            assert resp.status_code == 302


def test_admin_page_restriction_http_posts(journalist_app, test_journo):
    admin_urls = [url_for('admin.reset_two_factor_totp'),
                  url_for('admin.reset_two_factor_hotp'),
                  url_for('admin.add_user', user_id=test_journo['id']),
                  url_for('admin.new_user_two_factor'),
                  url_for('admin.reset_two_factor_totp'),
                  url_for('admin.reset_two_factor_hotp'),
                  url_for('admin.edit_user', user_id=test_journo['id']),
                  url_for('admin.delete_user', user_id=test_journo['id'])]
    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])
        for admin_url in admin_urls:
            resp = app.post(admin_url)
            assert resp.status_code == 302


def test_user_authorization_for_gets(journalist_app):
    urls = [url_for('main.index'), url_for('col.col', filesystem_id='1'),
            url_for('col.download_single_submission',
                    filesystem_id='1', fn='1'),
            url_for('account.edit')]

    with journalist_app.test_client() as app:
        for url in urls:
            resp = app.get(url)
            assert resp.status_code == 302


def test_user_authorization_for_posts(journalist_app):
    urls = [url_for('col.add_star', filesystem_id='1'),
            url_for('col.remove_star', filesystem_id='1'),
            url_for('col.process'),
            url_for('col.delete_single', filesystem_id='1'),
            url_for('main.reply'),
            url_for('main.regenerate_code'),
            url_for('main.bulk'),
            url_for('account.new_two_factor'),
            url_for('account.reset_two_factor_totp'),
            url_for('account.reset_two_factor_hotp')]
    with journalist_app.test_client() as app:
        for url in urls:
            resp = app.post(url)
            assert resp.status_code == 302


def test_incorrect_current_password_change(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])
        resp = app.post(url_for('account.new_password'),
                        data=dict(password=VALID_PASSWORD,
                                  token='mocked',
                                  current_password='badpw'),
                        follow_redirects=True)

    text = resp.data.decode('utf-8')
    assert 'Incorrect password or two-factor code' in text


# need a journalist app for the app context
def test_passphrase_migration_on_verification(journalist_app):
    salt = b64decode('+mGOQmD5Nnb+mH9gwBoxKRhKZmmJ6BzpmD5YArPHZsY=')
    journalist = Journalist('test', VALID_PASSWORD)

    # manually set the params
    hash = journalist._scrypt_hash(VALID_PASSWORD, salt)
    journalist.passphrase_hash = None
    journalist.pw_salt = salt
    journalist.pw_hash = hash

    assert journalist.valid_password(VALID_PASSWORD)

    # check that the migration happened
    assert journalist.passphrase_hash is not None
    assert journalist.pw_salt is None
    assert journalist.pw_hash is None

    # check that that a verification post-migration works
    assert journalist.valid_password(VALID_PASSWORD)


# need a journalist app for the app context
def test_passphrase_migration_on_reset(journalist_app):
    salt = b64decode('+mGOQmD5Nnb+mH9gwBoxKRhKZmmJ6BzpmD5YArPHZsY=')
    journalist = Journalist('test', VALID_PASSWORD)

    # manually set the params
    hash = journalist._scrypt_hash(VALID_PASSWORD, salt)
    journalist.passphrase_hash = None
    journalist.pw_salt = salt
    journalist.pw_hash = hash

    journalist.set_password(VALID_PASSWORD)

    # check that the migration happened
    assert journalist.passphrase_hash is not None
    assert journalist.pw_salt is None
    assert journalist.pw_hash is None

    # check that that a verification post-migration works
    assert journalist.valid_password(VALID_PASSWORD)


class TestJournalistApp(TestCase):

    # A method required by flask_testing.TestCase
    def create_app(self):
        return journalist.app

    def setUp(self):
        utils.env.setup()

        # Patch the two-factor verification to avoid intermittent errors
        utils.db_helper.mock_verify_token(self)

        # Setup test users: user & admin
        self.user, self.user_pw = utils.db_helper.init_journalist()
        self.admin, self.admin_pw = utils.db_helper.init_journalist(
            is_admin=True)

    def tearDown(self):
        utils.env.teardown()

    # WARNING: we are purposely doing something that would not work in
    # production in the _login_user and _login_admin methods. This is done as a
    # reminder to the test developer that the flask_testing.TestCase only uses
    # one request context per method (see
    # https://github.com/freedomofpress/securedrop/issues/1444). By explicitly
    # making a point of this, we hope to avoid the introduction of new tests,
    # that do not truly prove their result because of this disconnect between
    # request context in Flask Testing and production.
    def _login_admin(self):
        self._ctx.g.user = self.admin

    def _login_user(self):
        self._ctx.g.user = self.user

    def test_too_long_user_password_change(self):
        self._login_user()

        overly_long_password = VALID_PASSWORD + \
            'a' * (Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1)

        self.client.post(url_for('account.new_password'),
                         data=dict(password=overly_long_password,
                                   token='mocked',
                                   current_password=self.user_pw),
                         follow_redirects=True)

        self.assertMessageFlashed('You submitted a bad password! Password not '
                                  'changed.', 'error')

    def test_valid_user_password_change(self):
        self._login_user()
        resp = self.client.post(
            url_for('account.new_password'),
            data=dict(password=VALID_PASSWORD_2,
                      token='mocked',
                      current_password=self.user_pw),
            follow_redirects=True)

        assert 'Password updated.' in \
            resp.data.decode('utf-8')

    def test_regenerate_totp(self):
        self._login_user()
        old_totp = self.user.totp

        res = self.client.post(url_for('account.reset_two_factor_totp'))
        new_totp = self.user.totp

        # check that totp is different
        self.assertNotEqual(old_totp.secret, new_totp.secret)

        # should redirect to verification page
        self.assertRedirects(res, url_for('account.new_two_factor'))

    def test_edit_hotp(self):
        self._login_user()
        old_hotp = self.user.otp_secret

        res = self.client.post(
            url_for('account.reset_two_factor_hotp'),
            data=dict(otp_secret=123456)
            )
        new_hotp = self.user.otp_secret

        # check that hotp is different
        self.assertNotEqual(old_hotp, new_hotp)

        # should redirect to verification page
        self.assertRedirects(res, url_for('account.new_two_factor'))

    def test_delete_source_deletes_submissions(self):
        """Verify that when a source is deleted, the submissions that
        correspond to them are also deleted."""

        self._delete_collection_setup()
        journalist_app_module.utils.delete_collection(
            self.source.filesystem_id)

        # Source should be gone
        results = db.session.query(Source).filter(
            Source.id == self.source.id).all()
        self.assertEqual(results, [])

    def _delete_collection_setup(self):
        self.source, _ = utils.db_helper.init_source()
        utils.db_helper.submit(self.source, 2)
        utils.db_helper.reply(self.user, self.source, 2)

    def test_delete_collection_updates_db(self):
        """Verify that when a source is deleted, their Source identity
        record, as well as Reply & Submission records associated with
        that record are purged from the database."""
        self._delete_collection_setup()
        journalist_app_module.utils.delete_collection(
            self.source.filesystem_id)
        results = Source.query.filter(Source.id == self.source.id).all()
        self.assertEqual(results, [])
        results = db.session.query(
            Submission.source_id == self.source.id).all()
        self.assertEqual(results, [])
        results = db.session.query(Reply.source_id == self.source.id).all()
        self.assertEqual(results, [])

    def test_delete_source_deletes_source_key(self):
        """Verify that when a source is deleted, the PGP key that corresponds
        to them is also deleted."""
        self._delete_collection_setup()

        # Source key exists
        source_key = current_app.crypto_util.getkey(self.source.filesystem_id)
        self.assertNotEqual(source_key, None)

        journalist_app_module.utils.delete_collection(
            self.source.filesystem_id)

        # Source key no longer exists
        source_key = current_app.crypto_util.getkey(self.source.filesystem_id)
        self.assertEqual(source_key, None)

    def test_delete_source_deletes_docs_on_disk(self):
        """Verify that when a source is deleted, the encrypted documents that
        exist on disk is also deleted."""
        self._delete_collection_setup()

        # Encrypted documents exists
        dir_source_docs = os.path.join(config.STORE_DIR,
                                       self.source.filesystem_id)
        self.assertTrue(os.path.exists(dir_source_docs))

        job = journalist_app_module.utils.delete_collection(
            self.source.filesystem_id)

        # Wait up to 5s to wait for Redis worker `srm` operation to complete
        utils.async.wait_for_redis_worker(job)

        # Encrypted documents no longer exist
        self.assertFalse(os.path.exists(dir_source_docs))

    def test_download_selected_submissions_from_source(self):
        source, _ = utils.db_helper.init_source()
        submissions = utils.db_helper.submit(source, 4)
        selected_submissions = random.sample(submissions, 2)
        selected_fnames = [submission.filename
                           for submission in selected_submissions]
        selected_fnames.sort()

        self._login_user()
        resp = self.client.post(
            '/bulk', data=dict(action='download',
                               filesystem_id=source.filesystem_id,
                               doc_names_selected=selected_fnames))

        # The download request was succesful, and the app returned a zipfile
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/zip')
        self.assertTrue(zipfile.is_zipfile(StringIO(resp.data)))

        # The submissions selected are in the zipfile
        for filename in selected_fnames:
            self.assertTrue(
                # Check that the expected filename is in the zip file
                zipfile.ZipFile(StringIO(resp.data)).getinfo(
                    os.path.join(
                        source.journalist_filename,
                        "%s_%s" % (filename.split('-')[0],
                                   source.last_updated.date()),
                        filename
                    ))
                )

        # The submissions not selected are absent from the zipfile
        not_selected_submissions = set(submissions).difference(
            selected_submissions)
        not_selected_fnames = [submission.filename
                               for submission in not_selected_submissions]

        for filename in not_selected_fnames:
            with self.assertRaises(KeyError):
                zipfile.ZipFile(StringIO(resp.data)).getinfo(
                    os.path.join(
                        source.journalist_filename,
                        source.journalist_designation,
                        "%s_%s" % (filename.split('-')[0],
                                   source.last_updated.date()),
                        filename
                    ))

    def _bulk_download_setup(self):
        """Create a couple sources, make some submissions on their behalf,
        mark some of them as downloaded, and then perform *action* on all
        sources."""
        self.source0, _ = utils.db_helper.init_source()
        self.source1, _ = utils.db_helper.init_source()
        self.journo0, _ = utils.db_helper.init_journalist()
        self.submissions0 = utils.db_helper.submit(self.source0, 2)
        self.submissions1 = utils.db_helper.submit(self.source1, 3)
        self.downloaded0 = random.sample(self.submissions0, 1)
        utils.db_helper.mark_downloaded(*self.downloaded0)
        self.not_downloaded0 = set(self.submissions0).difference(
            self.downloaded0)
        self.downloaded1 = random.sample(self.submissions1, 2)
        utils.db_helper.mark_downloaded(*self.downloaded1)
        self.not_downloaded1 = set(self.submissions1).difference(
            self.downloaded1)

    def test_download_unread_all_sources(self):
        self._bulk_download_setup()
        self._login_user()

        # Download all unread messages from all sources
        self.resp = self.client.post(
            url_for('col.process'),
            data=dict(action='download-unread',
                      cols_selected=[self.source0.filesystem_id,
                                     self.source1.filesystem_id]))

        # The download request was succesful, and the app returned a zipfile
        self.assertEqual(self.resp.status_code, 200)
        self.assertEqual(self.resp.content_type, 'application/zip')
        self.assertTrue(zipfile.is_zipfile(StringIO(self.resp.data)))

        # All the not dowloaded submissions are in the zipfile
        for submission in self.not_downloaded0:
            self.assertTrue(
                zipfile.ZipFile(StringIO(self.resp.data)).getinfo(
                    os.path.join(
                        "unread",
                        self.source0.journalist_designation,
                        "%s_%s" % (submission.filename.split('-')[0],
                                   self.source0.last_updated.date()),
                        submission.filename
                    ))
                )
        for submission in self.not_downloaded1:
            self.assertTrue(
                zipfile.ZipFile(StringIO(self.resp.data)).getinfo(
                    os.path.join(
                        "unread",
                        self.source1.journalist_designation,
                        "%s_%s" % (submission.filename.split('-')[0],
                                   self.source1.last_updated.date()),
                        submission.filename
                    ))
                )

        # All the downloaded submissions are absent from the zipfile
        for submission in self.downloaded0:
            with self.assertRaises(KeyError):
                zipfile.ZipFile(StringIO(self.resp.data)).getinfo(
                    os.path.join(
                        "unread",
                        self.source0.journalist_designation,
                        "%s_%s" % (submission.filename.split('-')[0],
                                   self.source0.last_updated.date()),
                        submission.filename
                    ))

        for submission in self.downloaded1:
            with self.assertRaises(KeyError):
                zipfile.ZipFile(StringIO(self.resp.data)).getinfo(
                    os.path.join(
                        "unread",
                        self.source1.journalist_designation,
                        "%s_%s" % (submission.filename.split('-')[0],
                                   self.source1.last_updated.date()),
                        submission.filename
                    ))

    def test_download_all_selected_sources(self):
        self._bulk_download_setup()
        self._login_user()

        # Dowload all messages from self.source1
        self.resp = self.client.post(
            url_for('col.process'),
            data=dict(action='download-all',
                      cols_selected=[self.source1.filesystem_id]))

        resp = self.client.post(
            url_for('col.process'),
            data=dict(action='download-all',
                      cols_selected=[self.source1.filesystem_id]))

        # The download request was succesful, and the app returned a zipfile
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/zip')
        self.assertTrue(zipfile.is_zipfile(StringIO(resp.data)))

        # All messages from self.source1 are in the zipfile
        for submission in self.submissions1:
            self.assertTrue(
                zipfile.ZipFile(StringIO(resp.data)).getinfo(
                    os.path.join(
                        "all",
                        self.source1.journalist_designation,
                        "%s_%s" % (submission.filename.split('-')[0],
                                   self.source1.last_updated.date()),
                        submission.filename)
                    )
                )

        # All messages from self.source0 are absent from the zipfile
        for submission in self.submissions0:
            with self.assertRaises(KeyError):
                zipfile.ZipFile(StringIO(resp.data)).getinfo(
                    os.path.join(
                        "all",
                        self.source0.journalist_designation,
                        "%s_%s" % (submission.filename.split('-')[0],
                                   self.source0.last_updated.date()),
                        submission.filename)
                    )

    def test_single_source_is_successfully_starred(self):
        source, _ = utils.db_helper.init_source()
        self._login_user()
        resp = self.client.post(url_for('col.add_star',
                                        filesystem_id=source.filesystem_id))

        self.assertRedirects(resp, url_for('main.index'))

        # Assert source is starred
        self.assertTrue(source.star.starred)

    def test_single_source_is_successfully_unstarred(self):
        source, _ = utils.db_helper.init_source()
        self._login_user()

        # First star the source
        self.client.post(url_for('col.add_star',
                                 filesystem_id=source.filesystem_id))

        # Now unstar the source
        resp = self.client.post(url_for('col.remove_star',
                                filesystem_id=source.filesystem_id))

        self.assertRedirects(resp, url_for('main.index'))

        # Assert source is not starred
        self.assertFalse(source.star.starred)

    def test_journalist_session_expiration(self):
        try:
            old_expiration = config.SESSION_EXPIRATION_MINUTES
            has_session_expiration = True
        except AttributeError:
            has_session_expiration = False

        try:
            with self.client as client:
                # set the expiration to ensure we trigger an expiration
                config.SESSION_EXPIRATION_MINUTES = -1

                # do a real login to get a real session
                # (none of the mocking `g` hacks)
                resp = client.post(url_for('main.login'),
                                   data=dict(username=self.user.username,
                                             password=self.user_pw,
                                             token='mocked'))
                self.assertRedirects(resp, url_for('main.index'))
                assert 'uid' in session

                resp = client.get(url_for('account.edit'),
                                  follow_redirects=True)

                # check that the session was cleared (apart from 'expires'
                # which is always present and 'csrf_token' which leaks no info)
                session.pop('expires', None)
                session.pop('csrf_token', None)
                assert not session, session
                assert ('You have been logged out due to inactivity' in
                        resp.data.decode('utf-8'))
        finally:
            if has_session_expiration:
                config.SESSION_EXPIRATION_MINUTES = old_expiration
            else:
                del config.SESSION_EXPIRATION_MINUTES

    def test_csrf_error_page(self):
        old_enabled = self.app.config['WTF_CSRF_ENABLED']
        self.app.config['WTF_CSRF_ENABLED'] = True

        try:
            with self.app.test_client() as app:
                resp = app.post(url_for('main.login'))
                self.assertRedirects(resp, url_for('main.login'))

                resp = app.post(url_for('main.login'), follow_redirects=True)
                self.assertIn('You have been logged out due to inactivity',
                              resp.data)
        finally:
            self.app.config['WTF_CSRF_ENABLED'] = old_enabled

    def test_col_process_aborts_with_bad_action(self):
        """If the action is not a valid choice, a 500 should occur"""
        self._login_user()

        form_data = {'cols_selected': 'does not matter',
                     'action': 'this action does not exist'}

        resp = self.client.post(url_for('col.process'), data=form_data)

        self.assert500(resp)

    def test_col_process_successfully_deletes_multiple_sources(self):
        # Create two sources with one submission each
        source_1, _ = utils.db_helper.init_source()
        utils.db_helper.submit(source_1, 1)
        source_2, _ = utils.db_helper.init_source()
        utils.db_helper.submit(source_2, 1)

        self._login_user()

        form_data = {'cols_selected': [source_1.filesystem_id,
                                       source_2.filesystem_id],
                     'action': 'delete'}

        resp = self.client.post(url_for('col.process'), data=form_data,
                                follow_redirects=True)

        self.assert200(resp)

        # Verify there are no remaining sources
        remaining_sources = db.session.query(models.Source).all()
        self.assertEqual(len(remaining_sources), 0)

    def test_col_process_successfully_stars_sources(self):
        source_1, _ = utils.db_helper.init_source()
        utils.db_helper.submit(source_1, 1)

        self._login_user()

        form_data = {'cols_selected': [source_1.filesystem_id],
                     'action': 'star'}

        resp = self.client.post(url_for('col.process'), data=form_data,
                                follow_redirects=True)

        self.assert200(resp)

        # Verify the source is starred
        self.assertTrue(source_1.star.starred)

    def test_col_process_successfully_unstars_sources(self):
        source_1, _ = utils.db_helper.init_source()
        utils.db_helper.submit(source_1, 1)

        self._login_user()

        # First star the source
        form_data = {'cols_selected': [source_1.filesystem_id],
                     'action': 'star'}
        self.client.post(url_for('col.process'), data=form_data,
                         follow_redirects=True)

        # Now unstar the source
        form_data = {'cols_selected': [source_1.filesystem_id],
                     'action': 'un-star'}
        resp = self.client.post(url_for('col.process'), data=form_data,
                                follow_redirects=True)

        self.assert200(resp)

        # Verify the source is not starred
        self.assertFalse(source_1.star.starred)


class TestJournalistLocale(TestCase):

    def setUp(self):
        utils.env.setup()

        # Patch the two-factor verification to avoid intermittent errors
        utils.db_helper.mock_verify_token(self)

        # Setup test user
        self.user, self.user_pw = utils.db_helper.init_journalist()

    def tearDown(self):
        utils.env.teardown()

    def get_fake_config(self):
        return SDConfig()

    # A method required by flask_testing.TestCase
    def create_app(self):
        fake_config = self.get_fake_config()
        fake_config.SUPPORTED_LOCALES = ['en_US', 'fr_FR']
        return journalist_app_module.create_app(fake_config)

    def test_render_locales(self):
        """the locales.html template must collect both request.args (l=XX) and
        request.view_args (/<filesystem_id>) to build the URL to
        change the locale

        """
        source, _ = utils.db_helper.init_source()
        self._ctx.g.user = self.user

        url = url_for('col.col', filesystem_id=source.filesystem_id)
        resp = self.client.get(url + '?l=fr_FR')
        self.assertNotIn('?l=fr_FR', resp.data)
        self.assertIn(url + '?l=en_US', resp.data)


class TestJournalistLogin(unittest.TestCase):

    def setUp(self):
        self.__context = journalist_app_module.create_app(config).app_context()
        self.__context.push()
        utils.env.setup()

        # Patch the two-factor verification so it always succeeds
        utils.db_helper.mock_verify_token(self)

        self.user, self.user_pw = utils.db_helper.init_journalist()

    def tearDown(self):
        utils.env.teardown()
        self.__context.pop()

    @patch('models.Journalist._scrypt_hash')
    @patch('models.Journalist.valid_password', return_value=True)
    def test_valid_login_calls_scrypt(self,
                                      mock_scrypt_hash,
                                      mock_valid_password):
        Journalist.login(self.user.username, self.user_pw, 'mocked')
        self.assertTrue(
            mock_scrypt_hash.called,
            "Failed to call _scrypt_hash for password w/ valid length")

    @patch('models.Journalist._scrypt_hash')
    def test_login_with_invalid_password_doesnt_call_scrypt(self,
                                                            mock_scrypt_hash):
        invalid_pw = 'a'*(Journalist.MAX_PASSWORD_LEN + 1)
        with self.assertRaises(InvalidPasswordLength):
            Journalist.login(self.user.username, invalid_pw, 'mocked')
        self.assertFalse(
            mock_scrypt_hash.called,
            "Called _scrypt_hash for password w/ invalid length")
