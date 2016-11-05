#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from cStringIO import StringIO
import unittest
import zipfile
import mock

from flask_testing import TestCase
from flask import url_for, escape, g

import crypto_util
import journalist
import common
from db import db_session, Source, Journalist, InvalidPasswordLength

# Set environment variable so config.py uses a test environment
os.environ['SECUREDROP_ENV'] = 'test'


class TestJournalist(TestCase):

    def create_app(self):
        return journalist.app

    def setUp(self):
        common.shared_setup()

        # Patch the two-factor verification to avoid intermittent errors
        patcher = mock.patch('db.Journalist.verify_token')
        self.addCleanup(patcher.stop)
        self.mock_journalist_verify_token = patcher.start()
        self.mock_journalist_verify_token.return_value = True

        # Set up test users
        self.user_pw = "bar"
        self.user = Journalist(username="foo",
                               password=self.user_pw)
        self.admin_user_pw = "admin"
        self.admin_user = Journalist(username="admin",
                                     password=self.admin_user_pw,
                                     is_admin=True)
        db_session.add(self.user)
        db_session.add(self.admin_user)
        db_session.commit()

    def tearDown(self):
        common.shared_teardown()

    def test_index_should_redirect_to_login(self):
        res = self.client.get(url_for('index'))
        self.assertRedirects(res, url_for('login'))

    def test_invalid_user_login_should_fail(self):
        res = self.client.post(url_for('login'), data=dict(
            username='invalid',
            password='invalid',
            token='mocked'))
        self.assert200(res)
        self.assertIn("Login failed", res.data)

    def test_valid_user_login_should_succeed(self):
        res = self.client.post(url_for('login'), data=dict(
            username=self.user.username,
            password=self.user_pw,
            token='mocked'),
            follow_redirects=True)

        self.assert200(res)  # successful login redirects to index
        self.assertIn("Sources", res.data)
        self.assertIn("No documents have been submitted!", res.data)

    def test_normal_and_admin_user_login_should_redirect_to_index(self):
        """Normal users and admin users should both redirect to the index page after logging in successfully"""
        res = self.client.post(url_for('login'), data=dict(
            username=self.user.username,
            password=self.user_pw,
            token='mocked'))
        self.assertRedirects(res, url_for('index'))

        res = self.client.post(url_for('login'), data=dict(
            username=self.admin_user.username,
            password=self.admin_user_pw,
            token='mocked'))
        self.assertRedirects(res, url_for('index'))

    def test_admin_user_has_admin_link_in_index(self):
        res = self.client.post(url_for('login'), data=dict(
            username=self.admin_user.username,
            password=self.admin_user_pw,
            token='mocked'),
            follow_redirects=True)
        admin_link = '<a href="{}">{}</a>'.format(
            url_for('admin_index'),
            "Admin")
        self.assertIn(admin_link, res.data)

    def test_user_has_edit_account_link_in_index(self):
        res = self.client.post(url_for('login'), data=dict(
            username=self.user.username,
            password=self.user_pw,
            token='mocked'),
            follow_redirects=True)
        edit_account_link = '<a href="{}">{}</a>'.format(
            url_for('edit_account'),
            "Edit Account")
        self.assertIn(edit_account_link, res.data)

    def _login_user(self):
        self.client.post(url_for('login'), data=dict(
            username=self.user.username,
            password=self.user_pw,
            token='mocked'),
            follow_redirects=True)

    def _login_admin(self):
        self.client.post(url_for('login'), data=dict(
            username=self.admin_user.username,
            password=self.admin_user_pw,
            token='mocked'),
            follow_redirects=True)

    def test_user_logout(self):
        self._login_user()
        res = self.client.get(url_for('logout'))
        self.assertRedirects(res, url_for('index'))

    def test_admin_logout(self):
        self._login_admin()
        res = self.client.get(url_for('logout'))
        self.assertRedirects(res, url_for('index'))

    def test_admin_index(self):
        self._login_admin()
        res = self.client.get(url_for('admin_index'))
        self.assert200(res)
        self.assertIn("Admin Interface", res.data)

    def test_admin_delete_user(self):
        self._login_admin()

        res = self.client.post(
            url_for('admin_delete_user', user_id=self.user.id),
            follow_redirects=True)
        self.assert200(res)
        self.assertIn(escape("Deleted user '{}'".format(self.user.username)),
                      res.data)

        # verify journalist foo is no longer in the database
        user = Journalist.query.get(self.user.id)
        self.assertEqual(user, None)

    def test_admin_delete_invalid_user(self):
        self._login_admin()

        invalid_user_pk = max([user.id for user in Journalist.query.all()]) + 1
        res = self.client.post(url_for('admin_delete_user',
                                       user_id=invalid_user_pk))
        self.assert404(res)

    def test_admin_edits_user_password_valid(self):
        self._login_admin()

        res = self.client.post(
            url_for('admin_edit_user', user_id=self.user.id),
            data=dict(username='foo', is_admin=False,
                      password='valid', password_again='valid'))

        self.assertIn('Password successfully changed', res.data)

    def test_admin_edits_user_password_dont_match(self):
        self._login_admin()

        res = self.client.post(
            url_for('admin_edit_user', user_id=self.user.id),
            data=dict(username='foo', is_admin=False, password='not',
                      password_again='thesame'),
            follow_redirects=True)

        self.assertIn(escape("Passwords didn't match"), res.data)

    def test_admin_edits_user_password_too_long(self):
        self._login_admin()
        overly_long_password = 'a' * (Journalist.MAX_PASSWORD_LEN + 1)

        res = self.client.post(
            url_for('admin_edit_user', user_id=self.user.id),
            data=dict(username='foo', is_admin=False,
                      password=overly_long_password,
                      password_again=overly_long_password),
            follow_redirects=True)

        self.assertIn('Your password is too long', res.data)

    def test_admin_edits_user_invalid_username(self):
        """Test expected error message when admin attempts to change a user's
        username to a username that is taken by another user."""
        self._login_admin()

        new_username = self.admin_user.username
        res = self.client.post(
            url_for('admin_edit_user', user_id=self.user.id),
            data=dict(username=new_username, is_admin=False,
                      password='', password_again='')
            )

        self.assertIn('Username {} is already taken'.format(new_username),
                      res.data)

    def test_admin_reset_hotp_success(self):
        self._login_admin()
        old_hotp = self.user.hotp.secret

        res = self.client.post(
            url_for('admin_reset_two_factor_hotp'),
            data=dict(uid=self.user.id, otp_secret=123456)
            )

        new_hotp = self.user.hotp.secret

        self.assertNotEqual(old_hotp, new_hotp)

        self.assertRedirects(res,
            url_for('admin_new_user_two_factor', uid=self.user.id))

    def test_admin_reset_hotp_empty(self):
        self._login_admin()
        res = self.client.post(
            url_for('admin_reset_two_factor_hotp'),
            data=dict(uid=self.user.id)
            )

        self.assertIn('Change Secret', res.data)

    def test_admin_reset_totp_success(self):
        self._login_admin()
        old_totp = self.user.totp

        res = self.client.post(
            url_for('admin_reset_two_factor_totp'),
            data=dict(uid=self.user.id)
            )
        new_totp = self.user.totp

        self.assertNotEqual(old_totp, new_totp)

        self.assertRedirects(res,
            url_for('admin_new_user_two_factor', uid=self.user.id))

    def test_admin_new_user_2fa_success(self):
        self._login_admin()

        res = self.client.post(
            url_for('admin_new_user_two_factor', uid=self.user.id),
            data=dict(token='mocked')
            )

        self.assertRedirects(res, url_for('admin_index'))

    def test_admin_new_user_2fa_get_req(self):
        self._login_admin()

        res = self.client.get(
            url_for('admin_new_user_two_factor', uid=self.user.id)
            )

        # any GET req should take a user to the admin_new_user_two_factor page
        self.assertIn('Authenticator', res.data)

    def test_admin_add_user_get_req(self):
        self._login_admin()

        res = self.client.get(url_for('admin_add_user'))

        # any GET req should take a user to the admin_add_user page
        self.assertIn('Add user', res.data)

    def test_admin_add_user_success(self):
        self._login_admin()

        res = self.client.post(
            url_for('admin_add_user'),
            data=dict(username='dellsberg',
                      password='pentagonpapers',
                      password_again='pentagonpapers',
                      is_admin=False)
            )

        self.assertRedirects(res, url_for('admin_new_user_two_factor', uid=3))

    def test_admin_add_user_failure_no_username(self):
        self._login_admin()

        res = self.client.post(
            url_for('admin_add_user'),
            data=dict(username='', password='pentagonpapers',
                      password_again='pentagonpapers', is_admin=False))

        self.assertIn('Missing username', res.data)

    def test_admin_add_user_failure_passwords_dont_match(self):
        self._login_admin()

        res = self.client.post(
            url_for('admin_add_user'),
            data=dict(username='dellsberg', password='not',
                      password_again='thesame', is_admin=False))

        self.assertIn('Passwords didn', res.data)

    def test_admin_add_user_failure_password_too_long(self):
        self._login_admin()

        overly_long_password = 'a' * (Journalist.MAX_PASSWORD_LEN + 1)
        res = self.client.post(
            url_for('admin_add_user'),
            data=dict(username='dellsberg', password=overly_long_password,
                      password_again=overly_long_password, is_admin=False))

        self.assertIn('password is too long', res.data)

    def test_admin_authorization_for_gets(self):
        admin_urls = [url_for('admin_index'), url_for('admin_add_user'),
            url_for('admin_edit_user', user_id=self.user.id)]

        self._login_user()
        for admin_url in admin_urls:
            res = self.client.get(admin_url)
            self.assertStatus(res, 302)

    def test_admin_authorization_for_posts(self):
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
            res = self.client.post(admin_url)
            self.assertStatus(res, 302)

    def test_user_authorization_for_gets(self):
        urls = [url_for('index'), url_for('col', sid='1'),
                url_for('doc', sid='1', fn='1'), url_for('edit_account')]

        for url in urls:
            res = self.client.get(url)
            self.assertStatus(res, 302)

    def test_user_authorization_for_posts(self):
        urls = [url_for('add_star', sid='1'), url_for('remove_star', sid='1'),
                url_for('col_process'), url_for('col_delete_single', sid='1'),
                url_for('reply'), url_for('generate_code'), url_for('bulk'),
                url_for('account_new_two_factor'),
                url_for('account_reset_two_factor_totp'),
                url_for('account_reset_two_factor_hotp')]
        for url in urls:
            res = self.client.post(url)
            self.assertStatus(res, 302)

    def test_invalid_user_password_change(self):
        self._login_user()
        res = self.client.post(url_for('edit_account'), data=dict(
            password='not',
            password_again='thesame'))
        self.assertRedirects(res, url_for('edit_account'))

    def test_too_long_user_password_change(self):
        self._login_user()
        overly_long_password = 'a' * (Journalist.MAX_PASSWORD_LEN + 1)

        res = self.client.post(url_for('edit_account'), data=dict(
            password=overly_long_password,
            password_again=overly_long_password),
            follow_redirects=True)

        self.assertIn('Your password is too long', res.data)

    def test_valid_user_password_change(self):
        self._login_user()
        res = self.client.post(url_for('edit_account'), data=dict(
            password='valid',
            password_again='valid'))
        self.assertIn("Password successfully changed", res.data)

    def test_regenerate_totp(self):
        self._login_user()
        oldTotp = self.user.totp

        res = self.client.post(url_for('account_reset_two_factor_totp'))
        newTotp = self.user.totp

        # check that totp is different
        self.assertNotEqual(oldTotp, newTotp)

        # should redirect to verification page
        self.assertRedirects(res, url_for('account_new_two_factor'))

    def test_edit_hotp(self):
        self._login_user()
        oldHotp = self.user.hotp

        res = self.client.post(
            url_for('account_reset_two_factor_hotp'),
            data=dict(otp_secret=123456)
            )
        newHotp = self.user.hotp

        # check that hotp is different
        self.assertNotEqual(oldHotp, newHotp)

        # should redirect to verification page
        self.assertRedirects(res, url_for('account_new_two_factor'))

    def test_selected_bulk_download(self):
        sid = 'EQZGCJBRGISGOTC2NZVWG6LILJBHEV3CINNEWSCLLFTUWZJPKJFECLS2NZ4G4U3QOZCFKTTPNZMVIWDCJBBHMUDBGFHXCQ3R'
        source = Source(sid, crypto_util.display_id())
        db_session.add(source)
        db_session.commit()
        files = ['1-abc1-msg.gpg', '2-abc2-msg.gpg', '3-abc3-msg.gpg', '4-abc4-msg.gpg']
        selected_files = files[:2]
        unselected_files = files[2:]
        filenames = common.setup_test_docs(sid, files)

        self._login_user()
        rv = self.client.post('/bulk', data=dict(
            action='download',
            sid=sid,
            doc_names_selected=selected_files
        ))

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.content_type, 'application/zip')
        self.assertTrue(zipfile.is_zipfile(StringIO(rv.data)))

        for file in selected_files:
            self.assertTrue(zipfile.ZipFile(StringIO(rv.data)).getinfo(
                 os.path.join(source.journalist_filename, file)
            ))

        for file in unselected_files:
            try:
                zipfile.ZipFile(StringIO(rv.data)).getinfo(
                    os.path.join(source.journalist_filename, file))
            except KeyError:
                pass
            else:
                self.assertTrue(False)



    def test_download_all_bulk_download(self):
        sid = 'EQZGCJBRGISGOTC2NZVWG6LILJBHEV3CINNEWSCLLFTUWZJPKJFECLS2NZ4G4U3QOZCFKTTPNZMVIWDCJBBHMUDBGFHXCQ3R'
        source = Source(sid, crypto_util.display_id())
        db_session.add(source)
        db_session.commit()
        files = ['1-abc1-msg.gpg', '2-abc2-msg.gpg', '3-abc3-msg.gpg', '4-abc4-msg.gpg']
        filenames = common.setup_test_docs(sid, files)

        self._login_user()
        rv = self.client.post('/bulk', data=dict(
             action='download_all',
             sid=sid
        ))

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.content_type, 'application/zip')
        self.assertTrue(zipfile.is_zipfile(StringIO(rv.data)))
        for file in files:
            self.assertTrue(zipfile.ZipFile(StringIO(rv.data)).getinfo(
                 os.path.join(source.journalist_filename, file)
            ))


    def test_download_all(self):
        sid = 'EQZGCJBRGISGOTC2NZVWG6LILJBHEV3CINNEWSCLLFTUWZJPKJFECLS2NZ4G4U3QOZCFKTTPNZMVIWDCJBBHMUDBGFHXCQ3R'
        source = Source(sid, crypto_util.display_id())
        db_session.add(source)
        db_session.commit()
        files = ['1-abc1-msg.gpg', '2-abc2-msg.gpg', '3-abc3-msg.gpg', '4-abc4-msg.gpg']
        selected_files = files[::2]
        unselected_files = files[1::2]
        filenames = common.setup_test_docs(sid, files)

        self._login_user()
        rv = self.client.post('/bulk', data=dict(
                action='download',
                sid=sid,
                doc_names_selected=selected_files
        ))
        rv = self.client.get('/download_all_unread')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.content_type, 'application/zip')
        self.assertTrue(len(zipfile.ZipFile(StringIO(rv.data)).namelist()) == \
                        len(unselected_files))
        for file in unselected_files:
            self.assertTrue(zipfile.ZipFile(StringIO(rv.data)).getinfo(
                os.path.join('all_unread_'+g.user.username, file
            )))

    def test_max_password_length(self):
        """Creating a Journalist with a password that is greater than the
        maximum password length should raise an exception"""
        overly_long_password = 'a'*(Journalist.MAX_PASSWORD_LEN + 1)
        with self.assertRaises(InvalidPasswordLength):
            temp_journalist = Journalist(
                    username="My Password is Too Big!",
                    password=overly_long_password)

    def test_add_star(self):
        self._login_user()

        sid = 'EQZGCJBRGISGOTC2NZVWG6LILJBHEV3CINNEWSCLLFTUWZJPKJFECLS2NZ4G4U3QOZCFKTTPNZMVIWDCJBBHMUDBGFHXCQ3R'
        source = Source(sid, crypto_util.display_id())
        db_session.add(source)
        db_session.commit()

        res = self.client.post(url_for('add_star', sid=sid))
        self.assertRedirects(res, url_for('index'))


if __name__ == "__main__":
    unittest.main(verbosity=2)
