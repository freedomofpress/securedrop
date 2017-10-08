# -*- coding: utf-8 -*-
from cStringIO import StringIO
import os
import random
import unittest
import zipfile

from flask import url_for, escape, session
from flask_testing import TestCase
from mock import patch, ANY, MagicMock
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import config
import crypto_util
from db import (db_session, InvalidPasswordLength, Journalist, Reply, Source,
                Submission)
import db
import journalist
import utils

# Smugly seed the RNG for deterministic testing
random.seed('¯\_(ツ)_/¯')

VALID_PASSWORD = 'correct horse battery staple generic passphrase hooray'
VALID_PASSWORD_2 = 'another correct horse battery staple generic passphrase'


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

    @patch('crypto_util.genrandomid', side_effect=['bad', VALID_PASSWORD])
    def test_make_password(self, mocked_pw_gen):
        assert journalist._make_password() == VALID_PASSWORD

    @patch('journalist.app.logger.error')
    def test_reply_error_logging(self, mocked_error_logger):
        source, _ = utils.db_helper.init_source()
        filesystem_id = source.filesystem_id
        self._login_user()

        exception_class = StaleDataError
        exception_msg = 'Potentially sensitive content!'

        with patch('db.db_session.commit',
                   side_effect=exception_class(exception_msg)):
            self.client.post(url_for('reply'),
                             data={'filesystem_id': filesystem_id,
                             'message': '_'})

        # Notice the "potentially sensitive" exception_msg is not present in
        # the log event.
        mocked_error_logger.assert_called_once_with(
            "Reply from '{}' (ID {}) failed: {}!".format(self.user.username,
                                                         self.user.id,
                                                         exception_class))

    def test_reply_error_flashed_message(self):
        source, _ = utils.db_helper.init_source()
        filesystem_id = source.filesystem_id
        self._login_user()

        exception_class = StaleDataError

        with patch('db.db_session.commit', side_effect=exception_class()):
            self.client.post(url_for('reply'),
                             data={'filesystem_id': filesystem_id,
                             'message': '_'})

        self.assertMessageFlashed(
            'An unexpected error occurred! Please check '
            'the application logs or inform your adminstrator.', 'error')

    def test_empty_replies_are_rejected(self):
        source, _ = utils.db_helper.init_source()
        filesystem_id = source.filesystem_id
        self._login_user()

        resp = self.client.post(url_for('reply'),
                                data={'filesystem_id': filesystem_id,
                                      'message': ''},
                                follow_redirects=True)

        self.assertIn("You cannot send an empty reply.", resp.data)

    def test_nonempty_replies_are_accepted(self):
        source, _ = utils.db_helper.init_source()
        filesystem_id = source.filesystem_id
        self._login_user()

        resp = self.client.post(url_for('reply'),
                                data={'filesystem_id': filesystem_id,
                                      'message': '_'},
                                follow_redirects=True)

        self.assertNotIn("You cannot send an empty reply.", resp.data)

    def test_unauthorized_access_redirects_to_login(self):
        resp = self.client.get(url_for('index'))
        self.assertRedirects(resp, url_for('login'))

    def test_login_throttle(self):
        db.LOGIN_HARDENING = True
        try:
            for _ in range(Journalist._MAX_LOGIN_ATTEMPTS_PER_PERIOD):
                resp = self.client.post(url_for('login'),
                                        data=dict(username=self.user.username,
                                                  password='invalid',
                                                  token='mocked'))
                self.assert200(resp)
                self.assertIn("Login failed", resp.data)

            resp = self.client.post(url_for('login'),
                                    data=dict(username=self.user.username,
                                              password='invalid',
                                              token='mocked'))
            self.assert200(resp)
            self.assertIn("Please wait at least {} seconds".format(
                Journalist._LOGIN_ATTEMPT_PERIOD), resp.data)
        finally:
            db.LOGIN_HARDENING = False

    def test_login_invalid_credentials(self):
        resp = self.client.post(url_for('login'),
                                data=dict(username=self.user.username,
                                          password='invalid',
                                          token='mocked'))
        self.assert200(resp)
        self.assertIn("Login failed", resp.data)

    def test_login_valid_credentials(self):
        resp = self.client.post(url_for('login'),
                                data=dict(username=self.user.username,
                                          password=self.user_pw,
                                          token='mocked'),
                                follow_redirects=True)
        self.assert200(resp)  # successful login redirects to index
        self.assertIn("Sources", resp.data)
        self.assertIn("No documents have been submitted!", resp.data)

    def test_admin_login_redirects_to_index(self):
        resp = self.client.post(url_for('login'),
                                data=dict(username=self.admin.username,
                                          password=self.admin_pw,
                                          token='mocked'))
        self.assertRedirects(resp, url_for('index'))

    def test_user_login_redirects_to_index(self):
        resp = self.client.post(url_for('login'),
                                data=dict(username=self.user.username,
                                          password=self.user_pw,
                                          token='mocked'))
        self.assertRedirects(resp, url_for('index'))

    def test_admin_has_link_to_edit_account_page_in_index_page(self):
        resp = self.client.post(url_for('login'),
                                data=dict(username=self.admin.username,
                                          password=self.admin_pw,
                                          token='mocked'),
                                follow_redirects=True)
        edit_account_link = '<a href="{}" id="link-edit-account">'.format(
            url_for('edit_account'))
        self.assertIn(edit_account_link, resp.data)

    def test_user_has_link_to_edit_account_page_in_index_page(self):
        resp = self.client.post(url_for('login'),
                                data=dict(username=self.user.username,
                                          password=self.user_pw,
                                          token='mocked'),
                                follow_redirects=True)
        edit_account_link = '<a href="{}" id="link-edit-account">'.format(
            url_for('edit_account'))
        self.assertIn(edit_account_link, resp.data)

    def test_admin_has_link_to_admin_index_page_in_index_page(self):
        resp = self.client.post(url_for('login'),
                                data=dict(username=self.admin.username,
                                          password=self.admin_pw,
                                          token='mocked'),
                                follow_redirects=True)
        admin_link = '<a href="{}" id="link-admin-index">'.format(
            url_for('admin_index'))
        self.assertIn(admin_link, resp.data)

    def test_user_lacks_link_to_admin_index_page_in_index_page(self):
        resp = self.client.post(url_for('login'),
                                data=dict(username=self.user.username,
                                          password=self.user_pw,
                                          token='mocked'),
                                follow_redirects=True)
        admin_link = '<a href="{}" id="link-admin-index">'.format(
            url_for('admin_index'))
        self.assertNotIn(admin_link, resp.data)

    # WARNING: we are purposely doing something that would not work in
    # production in the _login_user and _login_admin methods. This is done as a
    # reminder to the test developer that the flask_testing.TestCase only uses
    # one request context per method (see
    # https://github.com/freedomofpress/securedrop/issues/1444). By explicitly
    # making a point of this, we hope to avoid the introduction of new tests,
    # that do not truly prove their result because of this disconnect between
    # request context in Flask Testing and production.
    #
    # TODO: either ditch Flask Testing or subclass it as discussed in the
    # aforementioned issue to fix the described problem.
    def _login_admin(self):
        self._ctx.g.user = self.admin

    def _login_user(self):
        self._ctx.g.user = self.user

    def test_admin_logout_redirects_to_index(self):
        self._login_admin()
        resp = self.client.get(url_for('logout'))
        self.assertRedirects(resp, url_for('index'))

    def test_user_logout_redirects_to_index(self):
        self._login_user()
        resp = self.client.get(url_for('logout'))
        self.assertRedirects(resp, url_for('index'))

    def test_admin_index(self):
        self._login_admin()
        resp = self.client.get(url_for('admin_index'))
        self.assert200(resp)
        self.assertIn("Admin Interface", resp.data)

    def test_admin_delete_user(self):
        # Verify journalist is in the database
        self.assertNotEqual(Journalist.query.get(self.user.id), None)

        self._login_admin()
        resp = self.client.post(url_for('admin_delete_user',
                                        user_id=self.user.id),
                                follow_redirects=True)

        # Assert correct interface behavior
        self.assert200(resp)
        self.assertIn(escape("Deleted user '{}'".format(self.user.username)),
                      resp.data)
        # Verify journalist is no longer in the database
        self.assertEqual(Journalist.query.get(self.user.id), None)

    def test_admin_deletes_invalid_user_404(self):
        self._login_admin()
        invalid_user_pk = max([user.id for user in Journalist.query.all()]) + 1
        resp = self.client.post(url_for('admin_delete_user',
                                        user_id=invalid_user_pk))
        self.assert404(resp)

    def test_admin_edits_user_password_success_response(self):
        self._login_admin()

        resp = self.client.post(
            url_for('admin_new_password', user_id=self.user.id),
            data=dict(password=VALID_PASSWORD_2),
            follow_redirects=True)

        text = resp.data.decode('utf-8')
        assert 'Password updated.' in text
        assert VALID_PASSWORD_2 in text

    def test_admin_edits_user_password_error_response(self):
        self._login_admin()

        with patch('db.db_session.commit', side_effect=Exception()):
            resp = self.client.post(
                url_for('admin_new_password', user_id=self.user.id),
                data=dict(password=VALID_PASSWORD_2),
                follow_redirects=True)

        assert ('There was an error, and the new password might not have '
                'been saved correctly.') in resp.data.decode('utf-8')

    def test_user_edits_password_success_reponse(self):
        self._login_user()
        resp = self.client.post(
            url_for('new_password'),
            data=dict(password=VALID_PASSWORD_2),
            follow_redirects=True)

        text = resp.data.decode('utf-8')
        assert "Password updated." in text
        assert VALID_PASSWORD_2 in text

    def test_user_edits_password_error_reponse(self):
        self._login_user()

        with patch('db.db_session.commit', side_effect=Exception()):
            resp = self.client.post(
                url_for('new_password'),
                data=dict(password=VALID_PASSWORD_2),
                follow_redirects=True)

        assert ('There was an error, and the new password might not have '
                'been saved correctly.') in resp.data.decode('utf-8')

    def test_admin_add_user_when_username_already_in_use(self):
        self._login_admin()
        resp = self.client.post(url_for('admin_add_user'),
                                data=dict(username=self.admin.username,
                                          password=VALID_PASSWORD,
                                          is_admin=None))
        self.assertIn('That username is already in use', resp.data)

    def test_max_password_length(self):
        """Creating a Journalist with a password that is greater than the
        maximum password length should raise an exception"""
        overly_long_password = VALID_PASSWORD + \
            'a' * (Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1)
        with self.assertRaises(InvalidPasswordLength):
            Journalist(username="My Password is Too Big!",
                       password=overly_long_password)

    def test_min_password_length(self):
        """Creating a Journalist with a password that is smaller than the
           minimum password length should raise an exception. This uses the
           magic number 7 below to get around the "diceware-like" requirement
           that may cause a failure before the length check.
        """
        password = ('a ' * 7)[0:(Journalist.MIN_PASSWORD_LEN - 1)]
        with self.assertRaises(InvalidPasswordLength):
            Journalist(username="My Password is Too Small!",
                       password=password)

    def test_admin_edits_user_password_too_long_warning(self):
        self._login_admin()
        overly_long_password = VALID_PASSWORD + \
            'a' * (Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1)

        self.client.post(
            url_for('admin_new_password', user_id=self.user.id),
            data=dict(username=self.user.username, is_admin=None,
                      password=overly_long_password),
            follow_redirects=True)

        self.assertMessageFlashed('You submitted a bad password! '
                                  'Password not changed.', 'error')

    def test_user_edits_password_too_long_warning(self):
        self._login_user()
        overly_long_password = VALID_PASSWORD + \
            'a' * (Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1)

        self.client.post(url_for('new_password'),
                         data=dict(password=overly_long_password),
                         follow_redirects=True)

        self.assertMessageFlashed('You submitted a bad password! '
                                  'Password not changed.', 'error')

    def test_admin_add_user_password_too_long_warning(self):
        self._login_admin()

        overly_long_password = VALID_PASSWORD + \
            'a' * (Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1)
        self.client.post(
            url_for('admin_add_user'),
            data=dict(username='dellsberg',
                      password=overly_long_password,
                      is_admin=None))

        self.assertMessageFlashed('There was an error with the autogenerated '
                                  'password. User not created. '
                                  'Please try again.', 'error')

    def test_admin_edits_user_invalid_username(self):
        """Test expected error message when admin attempts to change a user's
        username to a username that is taken by another user."""
        self._login_admin()
        new_username = self.admin.username

        self.client.post(
            url_for('admin_edit_user', user_id=self.user.id),
            data=dict(username=new_username, is_admin=None))

        self.assertMessageFlashed('Username "{}" already taken.'.format(
            new_username), 'error')

    def test_admin_resets_user_hotp(self):
        self._login_admin()
        old_hotp = self.user.hotp

        resp = self.client.post(url_for('admin_reset_two_factor_hotp'),
                                data=dict(uid=self.user.id, otp_secret=123456))
        new_hotp = self.user.hotp

        # check that hotp is different
        self.assertNotEqual(old_hotp.secret, new_hotp.secret)
        # Redirect to admin 2FA view
        self.assertRedirects(
            resp,
            url_for('admin_new_user_two_factor', uid=self.user.id))

    def test_admin_resets_user_hotp_format_non_hexa(self):
        self._login_admin()
        old_hotp = self.user.hotp.secret

        self.client.post(url_for('admin_reset_two_factor_hotp'),
                         data=dict(uid=self.user.id, otp_secret='ZZ'))
        new_hotp = self.user.hotp.secret

        self.assertEqual(old_hotp, new_hotp)
        self.assertMessageFlashed(
            "Invalid secret format: "
            "please only submit letters A-F and numbers 0-9.", "error")

    def test_admin_resets_user_hotp_format_odd(self):
        self._login_admin()
        old_hotp = self.user.hotp.secret

        self.client.post(url_for('admin_reset_two_factor_hotp'),
                         data=dict(uid=self.user.id, otp_secret='Z'))
        new_hotp = self.user.hotp.secret

        self.assertEqual(old_hotp, new_hotp)
        self.assertMessageFlashed(
            "Invalid secret format: "
            "odd-length secret. Did you mistype the secret?", "error")

    @patch('db.Journalist.set_hotp_secret')
    @patch('journalist.app.logger.error')
    def test_admin_resets_user_hotp_error(self,
                                          mocked_error_logger,
                                          mock_set_hotp_secret):
        self._login_admin()
        old_hotp = self.user.hotp.secret

        error_message = 'SOMETHING WRONG!'
        mock_set_hotp_secret.side_effect = TypeError(error_message)

        otp_secret = '1234'
        self.client.post(url_for('admin_reset_two_factor_hotp'),
                         data=dict(uid=self.user.id, otp_secret=otp_secret))
        new_hotp = self.user.hotp.secret

        self.assertEqual(old_hotp, new_hotp)
        self.assertMessageFlashed("An unexpected error occurred! "
                                  "Please check the application "
                                  "logs or inform your adminstrator.", "error")
        mocked_error_logger.assert_called_once_with(
            "set_hotp_secret '{}' (id {}) failed: {}".format(
                otp_secret, self.user.id, error_message))

    def test_user_resets_hotp(self):
        self._login_user()
        old_hotp = self.user.hotp

        resp = self.client.post(url_for('account_reset_two_factor_hotp'),
                                data=dict(otp_secret=123456))
        new_hotp = self.user.hotp

        # check that hotp is different
        self.assertNotEqual(old_hotp.secret, new_hotp.secret)
        # should redirect to verification page
        self.assertRedirects(resp, url_for('account_new_two_factor'))

    def test_admin_resets_user_totp(self):
        self._login_admin()
        old_totp = self.user.totp

        resp = self.client.post(
            url_for('admin_reset_two_factor_totp'),
            data=dict(uid=self.user.id))
        new_totp = self.user.totp

        self.assertNotEqual(old_totp.secret, new_totp.secret)

        self.assertRedirects(
            resp,
            url_for('admin_new_user_two_factor', uid=self.user.id))

    def test_user_resets_totp(self):
        self._login_user()
        old_totp = self.user.totp

        resp = self.client.post(url_for('account_reset_two_factor_totp'))
        new_totp = self.user.totp

        # check that totp is different
        self.assertNotEqual(old_totp.secret, new_totp.secret)

        # should redirect to verification page
        self.assertRedirects(resp, url_for('account_new_two_factor'))

    def test_admin_resets_hotp_with_missing_otp_secret_key(self):
        self._login_admin()
        resp = self.client.post(url_for('admin_reset_two_factor_hotp'),
                                data=dict(uid=self.user.id))

        self.assertIn('Change Secret', resp.data)

    def test_admin_new_user_2fa_redirect(self):
        self._login_admin()
        resp = self.client.post(
            url_for('admin_new_user_two_factor', uid=self.user.id),
            data=dict(token='mocked'))
        self.assertRedirects(resp, url_for('admin_index'))

    def test_http_get_on_admin_new_user_two_factor_page(self):
        self._login_admin()
        resp = self.client.get(url_for('admin_new_user_two_factor',
                                       uid=self.user.id))
        # any GET req should take a user to the admin_new_user_two_factor page
        self.assertIn('Authenticator', resp.data)

    def test_http_get_on_admin_add_user_page(self):
        self._login_admin()
        resp = self.client.get(url_for('admin_add_user'))
        # any GET req should take a user to the admin_add_user page
        self.assertIn('ADD USER', resp.data)

    def test_admin_add_user(self):
        self._login_admin()
        max_journalist_pk = max([user.id for user in Journalist.query.all()])

        resp = self.client.post(url_for('admin_add_user'),
                                data=dict(username='dellsberg',
                                          password=VALID_PASSWORD,
                                          is_admin=None))

        self.assertRedirects(resp, url_for('admin_new_user_two_factor',
                                           uid=max_journalist_pk+1))

    def test_admin_add_user_without_username(self):
        self._login_admin()
        resp = self.client.post(url_for('admin_add_user'),
                                data=dict(username='',
                                          password=VALID_PASSWORD,
                                          is_admin=None))
        self.assertIn('Invalid username', resp.data)

    def test_admin_add_user_too_short_username(self):
        self._login_admin()
        username = 'a' * (Journalist.MIN_USERNAME_LEN - 1)
        resp = self.client.post(url_for('admin_add_user'),
                                data=dict(username=username,
                                          password='pentagonpapers',
                                          password_again='pentagonpapers',
                                          is_admin=None))
        self.assertIn('Invalid username', resp.data)

    def test_admin_sets_user_to_admin(self):
        self._login_admin()
        new_user = 'admin-set-user-to-admin-test'
        resp = self.client.post(url_for('admin_add_user'),
                                data=dict(username=new_user,
                                          password=VALID_PASSWORD,
                                          is_admin=None))
        assert resp.status_code in (200, 302)
        journo = Journalist.query.filter(Journalist.username == new_user).one()
        assert not journo.is_admin

        resp = self.client.post(url_for('admin_edit_user', user_id=journo.id),
                                data=dict(is_admin=True))
        assert resp.status_code in (200, 302), resp.data.decode('utf-8')

        # there are better ways to do this, but flake8 complains
        journo = Journalist.query.filter(Journalist.username == new_user).one()
        assert journo.is_admin is True

    def test_admin_renames_user(self):
        self._login_admin()
        new_user = 'admin-renames-user-test'
        resp = self.client.post(url_for('admin_add_user'),
                                data=dict(username=new_user,
                                          password=VALID_PASSWORD,
                                          is_admin=None))
        assert resp.status_code in (200, 302)
        journo = Journalist.query.filter(Journalist.username == new_user).one()

        new_user = new_user + 'a'
        resp = self.client.post(url_for('admin_edit_user', user_id=journo.id),
                                data=dict(username=new_user))
        assert resp.status_code in (200, 302), resp.data.decode('utf-8')

        # the following will throw an exception if new_user is not found
        # therefore asserting it has been created
        Journalist.query.filter(Journalist.username == new_user).one()

    @patch('journalist.app.logger.error')
    @patch('journalist.Journalist',
           side_effect=IntegrityError('STATEMENT', 'PARAMETERS', None))
    def test_admin_add_user_integrity_error(self,
                                            mock_journalist,
                                            mocked_error_logger):
        self._login_admin()

        self.client.post(url_for('admin_add_user'),
                         data=dict(username='username',
                                   password=VALID_PASSWORD,
                                   is_admin=None))

        mocked_error_logger.assert_called_once_with(
            "Adding user 'username' failed: (__builtin__.NoneType) "
            "None [SQL: 'STATEMENT'] [parameters: 'PARAMETERS']")
        self.assertMessageFlashed(
            "An error occurred saving this user to the database."
            " Please check the application logs.",
            "error")

    def test_admin_page_restriction_http_gets(self):
        admin_urls = [url_for('admin_index'), url_for('admin_add_user'),
                      url_for('admin_edit_user', user_id=self.user.id)]

        self._login_user()
        for admin_url in admin_urls:
            resp = self.client.get(admin_url)
            self.assertStatus(resp, 302)

    def test_admin_page_restriction_http_posts(self):
        admin_urls = [url_for('admin_reset_two_factor_totp'),
                      url_for('admin_reset_two_factor_hotp'),
                      url_for('admin_add_user', user_id=self.user.id),
                      url_for('admin_new_user_two_factor'),
                      url_for('admin_reset_two_factor_totp'),
                      url_for('admin_reset_two_factor_hotp'),
                      url_for('admin_edit_user', user_id=self.user.id),
                      url_for('admin_delete_user', user_id=self.user.id)]
        self._login_user()
        for admin_url in admin_urls:
            resp = self.client.post(admin_url)
            self.assertStatus(resp, 302)

    def test_user_authorization_for_gets(self):
        urls = [url_for('index'), url_for('col', filesystem_id='1'),
                url_for('download_single_submission',
                        filesystem_id='1', fn='1'),
                url_for('edit_account')]

        for url in urls:
            resp = self.client.get(url)
            self.assertStatus(resp, 302)

    def test_user_authorization_for_posts(self):
        urls = [url_for('add_star', filesystem_id='1'),
                url_for('remove_star', filesystem_id='1'),
                url_for('col_process'),
                url_for('col_delete_single', filesystem_id='1'),
                url_for('reply'), url_for('generate_code'), url_for('bulk'),
                url_for('account_new_two_factor'),
                url_for('account_reset_two_factor_totp'),
                url_for('account_reset_two_factor_hotp')]
        for url in urls:
            res = self.client.post(url)
            self.assertStatus(res, 302)

    def test_invalid_user_password_change(self):
        self._login_user()
        res = self.client.post(url_for('new_password'),
                               data=dict(password='badpw'))
        self.assertRedirects(res, url_for('edit_account'))

    def test_too_long_user_password_change(self):
        self._login_user()

        overly_long_password = VALID_PASSWORD + \
            'a' * (Journalist.MAX_PASSWORD_LEN - len(VALID_PASSWORD) + 1)

        self.client.post(url_for('new_password'),
                         data=dict(password=overly_long_password),
                         follow_redirects=True)

        self.assertMessageFlashed('You submitted a bad password! Password not '
                                  'changed.', 'error')

    def test_valid_user_password_change(self):
        self._login_user()
        resp = self.client.post(
            url_for('new_password'),
            data=dict(password=VALID_PASSWORD_2),
            follow_redirects=True)

        assert 'Password updated.' in \
            resp.data.decode('utf-8')

    def test_regenerate_totp(self):
        self._login_user()
        old_totp = self.user.totp

        res = self.client.post(url_for('account_reset_two_factor_totp'))
        new_totp = self.user.totp

        # check that totp is different
        self.assertNotEqual(old_totp.secret, new_totp.secret)

        # should redirect to verification page
        self.assertRedirects(res, url_for('account_new_two_factor'))

    def test_edit_hotp(self):
        self._login_user()
        old_hotp = self.user.hotp

        res = self.client.post(
            url_for('account_reset_two_factor_hotp'),
            data=dict(otp_secret=123456)
            )
        new_hotp = self.user.hotp

        # check that hotp is different
        self.assertNotEqual(old_hotp.secret, new_hotp.secret)

        # should redirect to verification page
        self.assertRedirects(res, url_for('account_new_two_factor'))

    def test_delete_source_deletes_submissions(self):
        """Verify that when a source is deleted, the submissions that
        correspond to them are also deleted."""

        self._delete_collection_setup()
        journalist.delete_collection(self.source.filesystem_id)

        # Source should be gone
        results = db_session.query(Source).filter(
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
        journalist.delete_collection(self.source.filesystem_id)
        results = Source.query.filter(Source.id == self.source.id).all()
        self.assertEqual(results, [])
        results = db_session.query(
            Submission.source_id == self.source.id).all()
        self.assertEqual(results, [])
        results = db_session.query(Reply.source_id == self.source.id).all()
        self.assertEqual(results, [])

    def test_delete_source_deletes_source_key(self):
        """Verify that when a source is deleted, the PGP key that corresponds
        to them is also deleted."""
        self._delete_collection_setup()

        # Source key exists
        source_key = crypto_util.getkey(self.source.filesystem_id)
        self.assertNotEqual(source_key, None)

        journalist.delete_collection(self.source.filesystem_id)

        # Source key no longer exists
        source_key = crypto_util.getkey(self.source.filesystem_id)
        self.assertEqual(source_key, None)

    def test_delete_source_deletes_docs_on_disk(self):
        """Verify that when a source is deleted, the encrypted documents that
        exist on disk is also deleted."""
        self._delete_collection_setup()

        # Encrypted documents exists
        dir_source_docs = os.path.join(config.STORE_DIR,
                                       self.source.filesystem_id)
        self.assertTrue(os.path.exists(dir_source_docs))

        job = journalist.delete_collection(self.source.filesystem_id)

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
            '/col/process',
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
            '/col/process',
            data=dict(action='download-all',
                      cols_selected=[self.source1.filesystem_id]))

        resp = self.client.post(
            '/col/process',
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

    def test_add_star_redirects_to_index(self):
        source, _ = utils.db_helper.init_source()
        self._login_user()
        resp = self.client.post(url_for('add_star',
                                        filesystem_id=source.filesystem_id))
        self.assertRedirects(resp, url_for('index'))

    def test_journalist_session_expiration(self):
        try:
            old_expiration = config.SESSION_EXPIRATION_MINUTES
            has_session_expiration = True
        except AttributeError:
            has_session_expiration = False

        try:
            with self.client as client:
                # do a real login to get a real session
                # (none of the mocking `g` hacks)
                resp = self.client.post(url_for('login'),
                                        data=dict(username=self.user.username,
                                                  password=VALID_PASSWORD,
                                                  token='mocked'))
                assert resp.status_code == 200

                # set the expiration to ensure we trigger an expiration
                config.SESSION_EXPIRATION_MINUTES = -1

                resp = client.get(url_for('edit_account'),
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


class TestJournalistAppTwo(unittest.TestCase):

    def setUp(self):
        journalist.logged_in = MagicMock()
        journalist.request = MagicMock()
        journalist.url_for = MagicMock()
        journalist.redirect = MagicMock()
        journalist.abort = MagicMock()
        journalist.db_session = MagicMock()
        journalist.get_docs = MagicMock()
        journalist.get_or_else = MagicMock()

    def _set_up_request(self, cols_selected, action):
        journalist.request.form.__contains__.return_value = True
        journalist.request.form.getlist = MagicMock(return_value=cols_selected)
        journalist.request.form.__getitem__.return_value = action

    @patch("journalist.col_delete")
    def test_col_process_delegates_to_col_delete(self, col_delete):
        cols_selected = ['source_id']
        self._set_up_request(cols_selected, 'delete')

        journalist.col_process()

        col_delete.assert_called_with(cols_selected)

    @patch("journalist.col_star")
    def test_col_process_delegates_to_col_star(self, col_star):
        cols_selected = ['source_id']
        self._set_up_request(cols_selected, 'star')

        journalist.col_process()

        col_star.assert_called_with(cols_selected)

    @patch("journalist.col_un_star")
    def test_col_process_delegates_to_col_un_star(self, col_un_star):
        cols_selected = ['source_id']
        self._set_up_request(cols_selected, 'un-star')

        journalist.col_process()

        col_un_star.assert_called_with(cols_selected)

    @patch("journalist.abort")
    def test_col_process_returns_404_with_bad_action(self, abort):
        cols_selected = ['source_id']
        self._set_up_request(cols_selected, 'something-random')

        journalist.col_process()

        abort.assert_called_with(ANY)

    @patch("journalist.make_star_true")
    @patch("journalist.db_session")
    def test_col_star_call_db_(self, db_session, make_star_true):
        journalist.col_star(['filesystem_id'])

        make_star_true.assert_called_with('filesystem_id')

    @patch("journalist.db_session")
    def test_col_un_star_call_db(self, db_session):
        journalist.col_un_star([])

        db_session.commit.assert_called_with()

    @classmethod
    def tearDownClass(cls):
        # Reset the module variables that were changed to mocks so we don't
        # break other tests
        reload(journalist)


class TestJournalistLogin(unittest.TestCase):

    def setUp(self):
        utils.env.setup()

        # Patch the two-factor verification so it always succeeds
        utils.db_helper.mock_verify_token(self)

        self.user, self.user_pw = utils.db_helper.init_journalist()

    def tearDown(self):
        utils.env.teardown()
        # TODO: figure out why this is necessary here, but unnecessary in all
        # of the tests in `tests/test_unit_*.py`. Without this, the session
        # continues to return values even if the underlying database is deleted
        # (as in `shared_teardown`).
        db_session.remove()

    @patch('db.Journalist._scrypt_hash')
    @patch('db.Journalist.valid_password', return_value=True)
    def test_valid_login_calls_scrypt(self,
                                      mock_scrypt_hash,
                                      mock_valid_password):
        Journalist.login(self.user.username, self.user_pw, 'mocked')
        self.assertTrue(
            mock_scrypt_hash.called,
            "Failed to call _scrypt_hash for password w/ valid length")

    @patch('db.Journalist._scrypt_hash')
    def test_login_with_invalid_password_doesnt_call_scrypt(self,
                                                            mock_scrypt_hash):
        invalid_pw = 'a'*(Journalist.MAX_PASSWORD_LEN + 1)
        with self.assertRaises(InvalidPasswordLength):
            Journalist.login(self.user.username, invalid_pw, 'mocked')
        self.assertFalse(
            mock_scrypt_hash.called,
            "Called _scrypt_hash for password w/ invalid length")

    @classmethod
    def tearDownClass(cls):
        # Reset the module variables that were changed to mocks so we don't
        # break other tests
        reload(journalist)


class TestJournalist(unittest.TestCase):

    def setUp(self):
        journalist.logged_in = MagicMock()
        journalist.make_star_true = MagicMock()
        journalist.db_session = MagicMock()
        journalist.url_for = MagicMock()
        journalist.redirect = MagicMock()
        journalist.get_one_or_else = MagicMock()

    @patch('journalist.url_for')
    @patch('journalist.redirect')
    def test_add_star_renders_template(self, redirect, url_for):
        redirect_template = journalist.add_star('filesystem_id')

        self.assertEqual(redirect_template, redirect(url_for('index')))

    @patch('journalist.db_session')
    def test_add_star_makes_commits(self, db_session):
        journalist.add_star('filesystem_id')

        db_session.commit.assert_called_with()

    @patch('journalist.make_star_true')
    def test_single_delegates_to_make_star_true(self, make_star_true):
        filesystem_id = 'filesystem_id'

        journalist.add_star(filesystem_id)

        make_star_true.assert_called_with(filesystem_id)

    @patch('journalist.url_for')
    @patch('journalist.redirect')
    def test_remove_star_renders_template(self, redirect, url_for):
        redirect_template = journalist.remove_star('filesystem_id')

        self.assertEqual(redirect_template, redirect(url_for('index')))

    @patch('journalist.db_session')
    def test_remove_star_makes_commits(self, db_session):
        journalist.remove_star('filesystem_id')

        db_session.commit.assert_called_with()

    @patch('journalist.make_star_false')
    def test_remove_star_delegates_to_make_star_false(self, make_star_false):
        filesystem_id = 'filesystem_id'

        journalist.remove_star(filesystem_id)

        make_star_false.assert_called_with(filesystem_id)

    @classmethod
    def tearDownClass(cls):
        # Reset the module variables that were changed to mocks so we don't
        # break other tests
        reload(journalist)
