# -*- coding: utf-8 -*-
import os
import pytest
import io
import random
import zipfile
import base64
import datetime

from base64 import b64decode
from io import StringIO
from io import BytesIO
from flask import url_for, escape, session, current_app, g
from mock import patch
from pyotp import TOTP
from sqlalchemy.sql.expression import func
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError

import crypto_util
import models
import journalist_app as journalist_app_module
from . import utils

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from sdconfig import SDConfig, config

from db import db
from models import (InvalidPasswordLength, Journalist, Reply, Source,
                    Submission)
from .utils.instrument import InstrumentedApp

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
                'inform your admin.', 'error')


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
                                       "Please inform your admin.",
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
                "admin.", "error")

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
                " Please inform your admin.",
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
            url_for('col.download_single_file',
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


def test_journalist_reply_view(journalist_app, test_source, test_journo):
    source, _ = utils.db_helper.init_source()
    journalist, _ = utils.db_helper.init_journalist()
    submissions = utils.db_helper.submit(source, 1)
    replies = utils.db_helper.reply(journalist, source, 1)

    subm_url = url_for('col.download_single_file',
                       filesystem_id=submissions[0].source.filesystem_id,
                       fn=submissions[0].filename)
    reply_url = url_for('col.download_single_file',
                        filesystem_id=replies[0].source.filesystem_id,
                        fn=replies[0].filename)

    with journalist_app.test_client() as app:
        resp = app.get(subm_url)
        assert resp.status_code == 302
        resp = app.get(reply_url)
        assert resp.status_code == 302


def test_too_long_user_password_change(journalist_app, test_journo):
    overly_long_password = VALID_PASSWORD + \
        'a' * (Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1)

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            app.post(url_for('account.new_password'),
                     data=dict(password=overly_long_password,
                               token=TOTP(test_journo['otp_secret']).now(),
                               current_password=test_journo['password']),
                     follow_redirects=True)

            ins.assert_message_flashed(
                'You submitted a bad password! Password not changed.', 'error')


def test_valid_user_password_change(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        resp = app.post(url_for('account.new_password'),
                        data=dict(password=VALID_PASSWORD_2,
                                  token=TOTP(test_journo['otp_secret']).now(),
                                  current_password=test_journo['password']),
                        follow_redirects=True)

        assert 'Password updated.' in resp.data.decode('utf-8')


def test_regenerate_totp(journalist_app, test_journo):
    old_secret = test_journo['otp_secret']

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for('account.reset_two_factor_totp'))

            new_secret = Journalist.query.get(test_journo['id']).otp_secret

            # check that totp is different
            assert new_secret != old_secret

            # should redirect to verification page
            ins.assert_redirects(resp, url_for('account.new_two_factor'))


def test_edit_hotp(journalist_app, test_journo):
    old_secret = test_journo['otp_secret']

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for('account.reset_two_factor_hotp'),
                            data=dict(otp_secret=123456))

            new_secret = Journalist.query.get(test_journo['id']).otp_secret

            # check that totp is different
            assert new_secret != old_secret

            # should redirect to verification page
            ins.assert_redirects(resp, url_for('account.new_two_factor'))


def test_delete_source_deletes_submissions(journalist_app,
                                           test_journo,
                                           test_source):
    """Verify that when a source is deleted, the submissions that
    correspond to them are also deleted."""

    with journalist_app.app_context():
        source = Source.query.get(test_source['id'])
        journo = Journalist.query.get(test_journo['id'])

        utils.db_helper.submit(source, 2)
        utils.db_helper.reply(journo, source, 2)

        journalist_app_module.utils.delete_collection(
            test_source['filesystem_id'])

        res = Source.query.filter_by(id=test_source['id']).one_or_none()
        assert res is None


def test_delete_collection_updates_db(journalist_app,
                                      test_journo,
                                      test_source):
    """Verify that when a source is deleted, their Source identity
    record, as well as Reply & Submission records associated with
    that record are purged from the database."""

    with journalist_app.app_context():
        source = Source.query.get(test_source['id'])
        journo = Journalist.query.get(test_journo['id'])

        utils.db_helper.submit(source, 2)
        utils.db_helper.reply(journo, source, 2)

        journalist_app_module.utils.delete_collection(
            test_source['filesystem_id'])
        res = Source.query.filter_by(id=test_source['id']).one_or_none()
        assert res is None

        res = Submission.query.filter_by(source_id=test_source['id']) \
            .one_or_none()
        assert res is None

        res = Reply.query.filter_by(source_id=test_source['id']) \
            .one_or_none()
        assert res is None


def test_delete_source_deletes_source_key(journalist_app,
                                          test_source,
                                          test_journo):
    """Verify that when a source is deleted, the PGP key that corresponds
    to them is also deleted."""

    with journalist_app.app_context():
        source = Source.query.get(test_source['id'])
        journo = Journalist.query.get(test_journo['id'])

        utils.db_helper.submit(source, 2)
        utils.db_helper.reply(journo, source, 2)

        # Source key exists
        source_key = current_app.crypto_util.getkey(
            test_source['filesystem_id'])
        assert source_key is not None

        journalist_app_module.utils.delete_collection(
            test_source['filesystem_id'])

        # Source key no longer exists
        source_key = current_app.crypto_util.getkey(
            test_source['filesystem_id'])
        assert source_key is None


def test_delete_source_deletes_docs_on_disk(journalist_app,
                                            test_source,
                                            test_journo,
                                            config):
    """Verify that when a source is deleted, the encrypted documents that
    exist on disk is also deleted."""

    with journalist_app.app_context():
        source = Source.query.get(test_source['id'])
        journo = Journalist.query.get(test_journo['id'])

        utils.db_helper.submit(source, 2)
        utils.db_helper.reply(journo, source, 2)

        # Encrypted documents exists
        dir_source_docs = os.path.join(config.STORE_DIR,
                                       test_source['filesystem_id'])
        assert os.path.exists(dir_source_docs)

        job = journalist_app_module.utils.delete_collection(
            test_source['filesystem_id'])

        # Wait up to 5s to wait for Redis worker `srm` operation to complete
        utils.async.wait_for_redis_worker(job)

        # Encrypted documents no longer exist
        assert not os.path.exists(dir_source_docs)


def test_login_with_invalid_password_doesnt_call_argon2(mocker, test_journo):
    mock_argon2 = mocker.patch('models.argon2.verify')
    invalid_pw = 'a'*(Journalist.MAX_PASSWORD_LEN + 1)

    with pytest.raises(InvalidPasswordLength):
        Journalist.login(test_journo['username'],
                         invalid_pw,
                         TOTP(test_journo['otp_secret']).now())
    assert not mock_argon2.called


def test_valid_login_calls_argon2(mocker, test_journo):
    mock_argon2 = mocker.patch('models.argon2.verify')
    Journalist.login(test_journo['username'],
                     test_journo['password'],
                     TOTP(test_journo['otp_secret']).now())
    assert mock_argon2.called


def test_render_locales(config, journalist_app, test_journo, test_source):
    """the locales.html template must collect both request.args (l=XX) and
       request.view_args (/<filesystem_id>) to build the URL to
       change the locale
    """

    # We use the `journalist_app` fixture to generate all our tables, but we
    # don't use it during the test because we need to inject the i18n settings
    # (which are only triggered during `create_app`
    config.SUPPORTED_LOCALES = ['en_US', 'fr_FR']
    app = journalist_app_module.create_app(config)
    app.config['SERVER_NAME'] = 'localhost'  # needed for url_for
    url = url_for('col.col', filesystem_id=test_source['filesystem_id'])

    # we need the relative URL, not the full url including proto / localhost
    url_end = url.replace('http://', '')
    url_end = url_end[url_end.index('/')+1:]

    with app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])
        resp = app.get(url + '?l=fr_FR')

    # check that links to i18n URLs are/aren't present
    text = resp.data.decode('utf-8')
    assert '?l=fr_FR' not in text, text
    assert url_end + '?l=en_US' in text, text


def test_render_xenial_positive(config, journalist_app, test_journo, mocker):
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    journalist_app.config.update(
        XENIAL_WARNING_DATE=yesterday,
        XENIAL_VER='16.04'
    )

    mocked_error_platform = mocker.patch('platform.linux_distribution')
    mocked_error_platform.return_value = ('Ubuntu', '14.04', 'trusty')

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        resp = app.get(url_for('main.index'))

    text = resp.data.decode('utf-8')
    assert "critical-skull" in text, text


def test_render_xenial_negative_version(config, journalist_app, test_journo, mocker):
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    journalist_app.config.update(
        XENIAL_WARNING_DATE=yesterday,
        XENIAL_VER='16.04'
    )

    mocked_error_platform = mocker.patch('platform.linux_distribution')
    mocked_error_platform.return_value = ('Ubuntu', '16.04', 'xenial')

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])
        resp = app.get('/')

    text = resp.data.decode('utf-8')
    assert "critical-skull" not in text, text


def test_render_xenial_negative_date(config, journalist_app, test_journo):
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    journalist_app.config.update(
        XENIAL_WARNING_DATE=tomorrow,
        XENIAL_VER='16.04'
    )

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])
        resp = app.get('/')

    text = resp.data.decode('utf-8')
    assert "critical-skull" not in text, text


def test_download_selected_submissions_from_source(journalist_app,
                                                   test_journo,
                                                   test_source):
    source = Source.query.get(test_source['id'])
    submissions = utils.db_helper.submit(source, 4)
    selected_submissions = random.sample(submissions, 2)
    selected_fnames = [submission.filename
                       for submission in selected_submissions]
    selected_fnames.sort()

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])
        resp = app.post(
            '/bulk', data=dict(action='download',
                               filesystem_id=test_source['filesystem_id'],
                               doc_names_selected=selected_fnames))

    # The download request was succesful, and the app returned a zipfile
    assert resp.status_code == 200
    assert resp.content_type == 'application/zip'
    assert zipfile.is_zipfile(StringIO(resp.data))

    # The submissions selected are in the zipfile
    for filename in selected_fnames:
        # Check that the expected filename is in the zip file
        zipinfo = zipfile.ZipFile(StringIO(resp.data)).getinfo(
            os.path.join(
                source.journalist_filename,
                "%s_%s" % (filename.split('-')[0],
                           source.last_updated.date()),
                filename
            ))
        assert zipinfo

    # The submissions not selected are absent from the zipfile
    not_selected_submissions = set(submissions).difference(
        selected_submissions)
    not_selected_fnames = [submission.filename
                           for submission in not_selected_submissions]

    for filename in not_selected_fnames:
        with pytest.raises(KeyError):
            zipfile.ZipFile(StringIO(resp.data)).getinfo(
                os.path.join(
                    source.journalist_filename,
                    source.journalist_designation,
                    "%s_%s" % (filename.split('-')[0],
                               source.last_updated.date()),
                    filename
                ))


def _bulk_download_setup(journo):
    """Create a couple sources, make some submissions on their behalf,
    mark some of them as downloaded"""

    source0, _ = utils.db_helper.init_source()
    source1, _ = utils.db_helper.init_source()

    submissions0 = utils.db_helper.submit(source0, 2)
    submissions1 = utils.db_helper.submit(source1, 3)

    downloaded0 = random.sample(submissions0, 1)
    utils.db_helper.mark_downloaded(*downloaded0)
    not_downloaded0 = set(submissions0).difference(downloaded0)

    downloaded1 = random.sample(submissions1, 2)
    utils.db_helper.mark_downloaded(*downloaded1)
    not_downloaded1 = set(submissions1).difference(downloaded1)

    return {
        'source0': source0,
        'source1': source1,
        'submissions0': submissions0,
        'submissions1': submissions1,
        'downloaded0': downloaded0,
        'downloaded1': downloaded1,
        'not_downloaded0': not_downloaded0,
        'not_downloaded1': not_downloaded1,
    }


def test_download_unread_all_sources(journalist_app, test_journo):
    bulk = _bulk_download_setup(Journalist.query.get(test_journo['id']))

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        # Download all unread messages from all sources
        resp = app.post(
            url_for('col.process'),
            data=dict(action='download-unread',
                      cols_selected=[bulk['source0'].filesystem_id,
                                     bulk['source1'].filesystem_id]))

    # The download request was succesful, and the app returned a zipfile
    assert resp.status_code == 200
    assert resp.content_type == 'application/zip'
    assert zipfile.is_zipfile(StringIO(resp.data))

    # All the not dowloaded submissions are in the zipfile
    for submission in bulk['not_downloaded0']:
        zipinfo = zipfile.ZipFile(StringIO(resp.data)).getinfo(
                os.path.join(
                    "unread",
                    bulk['source0'].journalist_designation,
                    "%s_%s" % (submission.filename.split('-')[0],
                               bulk['source0'].last_updated.date()),
                    submission.filename
                ))
        assert zipinfo

    for submission in bulk['not_downloaded1']:
        zipinfo = zipfile.ZipFile(StringIO(resp.data)).getinfo(
            os.path.join(
                "unread",
                bulk['source1'].journalist_designation,
                "%s_%s" % (submission.filename.split('-')[0],
                           bulk['source1'].last_updated.date()),
                submission.filename
            ))
        assert zipinfo

    # All the downloaded submissions are absent from the zipfile
    for submission in bulk['downloaded0']:
        with pytest.raises(KeyError):
            zipfile.ZipFile(StringIO(resp.data)).getinfo(
                os.path.join(
                    "unread",
                    bulk['source0'].journalist_designation,
                    "%s_%s" % (submission.filename.split('-')[0],
                               bulk['source0'].last_updated.date()),
                    submission.filename
                ))

    for submission in bulk['downloaded1']:
        with pytest.raises(KeyError):
            zipfile.ZipFile(StringIO(resp.data)).getinfo(
                os.path.join(
                    "unread",
                    bulk['source1'].journalist_designation,
                    "%s_%s" % (submission.filename.split('-')[0],
                               bulk['source1'].last_updated.date()),
                    submission.filename
                ))


def test_download_all_selected_sources(journalist_app, test_journo):
    bulk = _bulk_download_setup(Journalist.query.get(test_journo['id']))

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        # Dowload all messages from source1
        resp = app.post(
            url_for('col.process'),
            data=dict(action='download-all',
                      cols_selected=[bulk['source1'].filesystem_id]))

        resp = app.post(
            url_for('col.process'),
            data=dict(action='download-all',
                      cols_selected=[bulk['source1'].filesystem_id]))

    # The download request was succesful, and the app returned a zipfile
    assert resp.status_code == 200
    assert resp.content_type == 'application/zip'
    assert zipfile.is_zipfile(StringIO(resp.data))

    # All messages from source1 are in the zipfile
    for submission in bulk['submissions1']:
        zipinfo = zipfile.ZipFile(StringIO(resp.data)).getinfo(
            os.path.join(
                "all",
                bulk['source1'].journalist_designation,
                "%s_%s" % (submission.filename.split('-')[0],
                           bulk['source1'].last_updated.date()),
                submission.filename)
            )
        assert zipinfo

    # All messages from source0 are absent from the zipfile
    for submission in bulk['submissions0']:
        with pytest.raises(KeyError):
            zipfile.ZipFile(StringIO(resp.data)).getinfo(
                os.path.join(
                    "all",
                    bulk['source0'].journalist_designation,
                    "%s_%s" % (submission.filename.split('-')[0],
                               bulk['source0'].last_updated.date()),
                    submission.filename)
                )


def test_single_source_is_successfully_starred(journalist_app,
                                               test_journo,
                                               test_source):
    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for('col.add_star',
                            filesystem_id=test_source['filesystem_id']))

            ins.assert_redirects(resp, url_for('main.index'))

    source = Source.query.get(test_source['id'])
    assert source.star.starred


def test_single_source_is_successfully_unstarred(journalist_app,
                                                 test_journo,
                                                 test_source):
    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])
        # First star the source
        app.post(url_for('col.add_star',
                         filesystem_id=test_source['filesystem_id']))

        with InstrumentedApp(journalist_app) as ins:
            # Now unstar the source
            resp = app.post(
                url_for('col.remove_star',
                        filesystem_id=test_source['filesystem_id']))

            ins.assert_redirects(resp, url_for('main.index'))

        source = Source.query.get(test_source['id'])
        assert not source.star.starred


def test_journalist_session_expiration(config, journalist_app, test_journo):
    # set the expiration to ensure we trigger an expiration
    config.SESSION_EXPIRATION_MINUTES = -1
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            login_data = {
                'username': test_journo['username'],
                'password': test_journo['password'],
                'token': TOTP(test_journo['otp_secret']).now(),
            }
            resp = app.post(url_for('main.login'), data=login_data)
            ins.assert_redirects(resp, url_for('main.index'))
        assert 'uid' in session

        resp = app.get(url_for('account.edit'), follow_redirects=True)

        # check that the session was cleared (apart from 'expires'
        # which is always present and 'csrf_token' which leaks no info)
        session.pop('expires', None)
        session.pop('csrf_token', None)
        assert not session, session
        assert ('You have been logged out due to inactivity' in
                resp.data.decode('utf-8'))


def test_csrf_error_page(journalist_app):
    journalist_app.config['WTF_CSRF_ENABLED'] = True
    with journalist_app.test_client() as app:
        with InstrumentedApp(journalist_app) as ins:
            resp = app.post(url_for('main.login'))
            ins.assert_redirects(resp, url_for('main.login'))

        resp = app.post(url_for('main.login'), follow_redirects=True)

        text = resp.data.decode('utf-8')
        assert 'You have been logged out due to inactivity' in text


def test_col_process_aborts_with_bad_action(journalist_app, test_journo):
    """If the action is not a valid choice, a 500 should occur"""
    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        form_data = {'cols_selected': 'does not matter',
                     'action': 'this action does not exist'}

        resp = app.post(url_for('col.process'), data=form_data)
        assert resp.status_code == 500


def test_col_process_successfully_deletes_multiple_sources(journalist_app,
                                                           test_journo):
    # Create two sources with one submission each
    source_1, _ = utils.db_helper.init_source()
    utils.db_helper.submit(source_1, 1)
    source_2, _ = utils.db_helper.init_source()
    utils.db_helper.submit(source_2, 1)

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        form_data = {'cols_selected': [source_1.filesystem_id,
                                       source_2.filesystem_id],
                     'action': 'delete'}

        resp = app.post(url_for('col.process'), data=form_data,
                        follow_redirects=True)

        assert resp.status_code == 200

    # Verify there are no remaining sources
    remaining_sources = Source.query.all()
    assert not remaining_sources


def test_col_process_successfully_stars_sources(journalist_app,
                                                test_journo,
                                                test_source):
    utils.db_helper.submit(test_source['source'], 1)

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        form_data = {'cols_selected': [test_source['filesystem_id']],
                     'action': 'star'}

        resp = app.post(url_for('col.process'), data=form_data,
                        follow_redirects=True)
        assert resp.status_code == 200

    source = Source.query.get(test_source['id'])
    assert source.star.starred


def test_col_process_successfully_unstars_sources(journalist_app,
                                                  test_journo,
                                                  test_source):
    utils.db_helper.submit(test_source['source'], 1)

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])

        # First star the source
        form_data = {'cols_selected': [test_source['filesystem_id']],
                     'action': 'star'}
        app.post(url_for('col.process'), data=form_data,
                 follow_redirects=True)

        # Now unstar the source
        form_data = {'cols_selected': [test_source['filesystem_id']],
                     'action': 'un-star'}
        resp = app.post(url_for('col.process'), data=form_data,
                        follow_redirects=True)

    assert resp.status_code == 200

    source = Source.query.get(test_source['id'])
    assert not source.star.starred


def test_source_with_null_last_updated(journalist_app,
                                       test_journo,
                                       test_files):
    '''Regression test for issues #3862'''

    source = test_files['source']
    source.last_updated = None
    db.session.add(source)
    db.session.commit()

    with journalist_app.test_client() as app:
        _login_user(app, test_journo['username'], test_journo['password'],
                    test_journo['otp_secret'])
        resp = app.get(url_for('main.index'))
        assert resp.status_code == 200


def test_does_set_cookie_headers(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        response = app.get(url_for('main.login'))

        observed_headers = response.headers
        assert 'Set-Cookie' in list(observed_headers.keys())
        assert 'Cookie' in observed_headers['Vary']


def test_app_error_handlers_defined(journalist_app):
    for status_code in [400, 401, 403, 404, 500]:
        # This will raise KeyError if an app-wide error handler is not defined
        assert journalist_app.error_handler_spec[None][status_code]
