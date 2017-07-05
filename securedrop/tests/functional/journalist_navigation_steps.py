import urllib2
import tempfile
import zipfile
import gzip
import datetime

from selenium.common.exceptions import NoSuchElementException

import tests.utils.db_helper as db_helper
from db import Journalist


class JournalistNavigationSteps():

    def _get_submission_content(self, file_url, raw_content):
        if not file_url.endswith(".gz.gpg"):
            return str(raw_content)

        with tempfile.TemporaryFile() as fp:
            fp.write(raw_content.data)
            fp.seek(0)

            gzf = gzip.GzipFile(mode='rb', fileobj=fp)
            content = gzf.read()

            return content

    def _login_user(self, username, password, token):
        self.driver.get(self.journalist_location + "/login")
        username_field = self.driver.find_element_by_css_selector(
            'input[name="username"]')
        username_field.send_keys(username)

        password_field = self.driver.find_element_by_css_selector(
            'input[name="password"]')
        password_field.send_keys(password)

        token_field = self.driver.find_element_by_css_selector(
            'input[name="token"]')
        token_field.send_keys(token)

        submit_button = self.driver.find_element_by_css_selector(
            'button[type=submit]')
        submit_button.click()

        # Successful login should redirect to the index
        self.assertEquals(self.driver.current_url,
                          self.journalist_location + '/')

    def _journalist_logs_in(self):
        # Create a test user for logging in
        self.user, self.user_pw = db_helper.init_journalist()
        self._login_user(self.user.username, self.user_pw, 'mocked')

        headline = self.driver.find_element_by_css_selector('span.headline')
        self.assertIn('Sources', headline.text)

    def _admin_logs_in(self):
        self.admin, self.admin_pw = db_helper.init_journalist(is_admin=True)
        self._login_user(self.admin.username, self.admin_pw, 'mocked')

        # Admin user should log in to the same interface as a normal user,
        # since there may be users who wish to be both journalists and admins.
        headline = self.driver.find_element_by_css_selector('span.headline')
        self.assertIn('Sources', headline.text)

        # Admin user should have a link that take them to the admin page
        links = self.driver.find_elements_by_tag_name('a')
        self.assertIn('Admin', [el.text for el in links])

    def _admin_visits_admin_interface(self):
        admin_interface_link = self.driver.find_element_by_link_text('Admin')
        admin_interface_link.click()

        h1s = self.driver.find_elements_by_tag_name('h1')
        self.assertIn("Admin Interface", [el.text for el in h1s])

    def _add_user(self, username, password, is_admin=False):
        username_field = self.driver.find_element_by_css_selector(
            'input[name="username"]')
        username_field.send_keys(username)

        password_field = self.driver.find_element_by_css_selector(
            'input[name="password"]')
        password_field.send_keys(password)

        password_again_field = self.driver.find_element_by_css_selector(
            'input[name="password_again"]')
        password_again_field.send_keys(password)

        if is_admin:
            # TODO implement (checkbox is unchecked by default)
            pass

        submit_button = self.driver.find_element_by_css_selector(
            'button[type=submit]')
        submit_button.click()

    def _admin_adds_a_user(self):
        add_user_btn = self.driver.find_element_by_css_selector(
            'button#add-user')
        add_user_btn.click()

        # The add user page has a form with an "ADD USER" button
        btns = self.driver.find_elements_by_tag_name('button')
        self.assertIn('ADD USER', [el.text for el in btns])

        self.new_user = dict(
            username='dellsberg',
            password='pentagonpapers')

        self._add_user(self.new_user['username'], self.new_user['password'])

        # Clicking submit on the add user form should redirect to the Google
        # Authenticator page
        h1s = self.driver.find_elements_by_tag_name('h1')
        self.assertIn("Enable Google Authenticator", [el.text for el in h1s])

        # Retrieve the saved user object from the db and keep it around for
        # further testing
        self.new_user['orm_obj'] = Journalist.query.filter(
            Journalist.username == self.new_user['username']).one()

        # Verify the two-factor authentication
        token_field = self.driver.find_element_by_css_selector(
            'input[name="token"]')
        token_field.send_keys('mocked')
        submit_button = self.driver.find_element_by_css_selector(
            'button[type=submit]')
        submit_button.click()

        # Successfully verifying the code should redirect to the admin
        # interface, and flash a message indicating success
        flashed_msgs = self.driver.find_elements_by_css_selector('.flash')
        self.assertIn(("Two-factor token successfully verified for user"
                       " {}!").format(self.new_user['username']),
                      [el.text for el in flashed_msgs])

    def _logout(self):
        # Click the logout link
        logout_link = self.driver.find_element_by_link_text('Logout')
        logout_link.click()

        # Logging out should redirect back to the login page
        self.wait_for(
            lambda: self.assertIn("Login to access the journalist interface",
                                  self.driver.page_source)
        )

    def _check_login_with_otp(self, otp):
        self._logout()
        self._login_user(self.new_user['username'],
                         self.new_user['password'], otp)
        # Test that the new user was logged in successfully
        self.assertIn('Sources', self.driver.page_source)

    def _new_user_can_log_in(self):
        # Log the admin user out
        self._logout()

        # Log the new user in
        self._login_user(self.new_user['username'],
                         self.new_user['password'],
                         'mocked')

        # Test that the new user was logged in successfully
        self.assertIn('Sources', self.driver.page_source)

        # The new user was not an admin, so they should not have the admin
        # interface link available
        self.assertRaises(NoSuchElementException,
                          self.driver.find_element_by_link_text,
                          'Admin')

    def _edit_account(self):
        edit_account_link = self.driver.find_element_by_link_text(
            'Edit Account')
        edit_account_link.click()

        # The header says "Edit your account"
        h1s = self.driver.find_elements_by_tag_name('h1')[0]
        self.assertEqual('Edit your account', h1s.text)
        # There's no link back to the admin interface.
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element_by_partial_link_text('Back to admin interface')
        # There's no field to change your username.
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element_by_css_selector('#username')
        # There's no checkbox to change the administrator status of your
        # account.
        with self.assertRaises(NoSuchElementException):
            username_field = self.driver.find_element_by_css_selector('#is_admin')
        # 2FA reset buttons at the bottom point to the user URLs for reset.
        totp_reset_button = self.driver.find_elements_by_css_selector(
            '#reset-two-factor-totp')[0]
        self.assertRegexpMatches(totp_reset_button.get_attribute('action'),
                                 '/account/reset-2fa-totp')
        hotp_reset_button = self.driver.find_elements_by_css_selector(
            '#reset-two-factor-hotp')[0]
        self.assertRegexpMatches(hotp_reset_button.get_attribute('action'),
                                 '/account/reset-2fa-hotp')

    def _edit_user(self, username):
        user = Journalist.query.filter_by(username=username).one()

        new_user_edit_links = filter(
            lambda el: el.get_attribute('data-username') == username,
            self.driver.find_elements_by_tag_name('a'))
        self.assertEquals(len(new_user_edit_links), 1)
        new_user_edit_links[0].click()
        # The header says "Edit user "username"".
        h1s = self.driver.find_elements_by_tag_name('h1')[0]
        self.assertEqual('Edit user "{}"'.format(username), h1s.text)
        # There's a convenient link back to the admin interface.
        admin_interface_link = self.driver.find_element_by_partial_link_text(
            'Back to admin interface')
        self.assertRegexpMatches(admin_interface_link.get_attribute('href'),
                                 '/admin$')
        # There's a field to change the user's username and it's already filled
        # out with the user's username.
        username_field = self.driver.find_element_by_css_selector('#username')
        self.assertEqual(username_field.get_attribute('placeholder'), username)
        # There's a checkbox to change the administrator status of the user and
        # it's already checked appropriately to reflect the current status of
        # our user.
        username_field = self.driver.find_element_by_css_selector('#is_admin')
        self.assertEqual(bool(username_field.get_attribute('checked')),
                         user.is_admin)
        # 2FA reset buttons at the bottom point to the admin URLs for
        # resettting 2FA and include the correct user id in the hidden uid.
        totp_reset_button = self.driver.find_elements_by_css_selector(
            '#reset-two-factor-totp')[0]
        self.assertRegexpMatches(totp_reset_button.get_attribute('action'),
                                 '/admin/reset-2fa-totp')
        totp_reset_uid = totp_reset_button.find_element_by_name('uid')
        self.assertEqual(int(totp_reset_uid.get_attribute('value')), user.id)
        self.assertFalse(totp_reset_uid.is_displayed())
        hotp_reset_button = self.driver.find_elements_by_css_selector(
            '#reset-two-factor-hotp')[0]
        self.assertRegexpMatches(hotp_reset_button.get_attribute('action'),
                                 '/admin/reset-2fa-hotp')
        hotp_reset_uid = hotp_reset_button.find_element_by_name('uid')
        self.assertEqual(int(hotp_reset_uid.get_attribute('value')), user.id)
        self.assertFalse(hotp_reset_uid.is_displayed())

    def _admin_can_edit_new_user(self):
        # Log the new user out
        self._logout()

        self._login_user(self.admin.username, self.admin_pw, 'mocked')

        # Go to the admin interface
        admin_interface_link = self.driver.find_element_by_link_text('Admin')
        admin_interface_link.click()

        # Click the "edit user" link for the new user
        # self._edit_user(self.new_user['username'])
        new_user_edit_links = filter(
            lambda el: el.get_attribute('data-username') == self.new_user['username'],
            self.driver.find_elements_by_tag_name('a'))
        self.assertEquals(len(new_user_edit_links), 1)
        new_user_edit_links[0].click()
        self.wait_for(
            lambda: self.assertIn('Edit user "{}"'.format(
                self.new_user['username']),
                self.driver.page_source)
        )

        new_username = self.new_user['username'] + "2"

        username_field = self.driver.find_element_by_css_selector(
            'input[name="username"]')
        username_field.send_keys(new_username)
        update_user_btn = self.driver.find_element_by_css_selector(
            'button[type=submit]')
        update_user_btn.click()

        self.wait_for(
            lambda: self.assertIn('Edit user "{}"'.format(new_username),
                                  self.driver.page_source)
        )

        # Update self.new_user with the new username for the future tests
        self.new_user['username'] = new_username

        # Log the new user in with their new username
        self._logout()
        self._login_user(self.new_user['username'],
                         self.new_user['password'],
                         'mocked')
        self.wait_for(
            lambda: self.assertIn('Sources', self.driver.page_source)
        )

        # Log the admin user back in
        self._logout()
        self._login_user(self.admin.username, self.admin_pw, 'mocked')

        # Go to the admin interface
        admin_interface_link = self.driver.find_element_by_link_text('Admin')
        admin_interface_link.click()
        # Edit the new user's password
        self._edit_user(self.new_user['username'])

        new_password = self.new_user['password'] + "2"
        password_field = self.driver.find_element_by_css_selector(
            'input[name="password"]')
        password_field.send_keys(new_password)
        password_again_field = self.driver.find_element_by_css_selector(
            'input[name="password_again"]')
        password_again_field.send_keys(new_password)
        update_user_btn = self.driver.find_element_by_css_selector(
            'button#update')
        update_user_btn.click()

        # Wait until page refreshes to avoid causing a broken pipe error (#623)
        self.wait_for(
            lambda: self.assertIn('Edit user "{}"'.format(new_username),
                                  self.driver.page_source)
        )

        # Update self.new_user with the new password
        # TODO dry
        self.new_user['password'] = new_password

        # Log the new user in with their new password
        self._logout()
        self._login_user(self.new_user['username'],
                         self.new_user['password'],
                         'mocked')
        self.wait_for(
            lambda: self.assertIn('Sources', self.driver.page_source)
        )

    def _journalist_checks_messages(self):
        self.driver.get(self.journalist_location)

        # There should be 1 collection in the list of collections
        code_names = self.driver.find_elements_by_class_name('code-name')
        self.assertEquals(1, len(code_names))

        # There should be a "1 unread" span in the sole collection entry
        unread_span = self.driver.find_element_by_css_selector('span.unread')
        self.assertIn("1 unread", unread_span.text)

    def _journalist_stars_and_unstars_single_message(self):
        # Message begins unstarred
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element_by_id('starred-source-link-1')

        # Journalist stars the message
        self.driver.find_element_by_class_name('button-star').click()
        starred = self.driver.find_elements_by_id('starred-source-link-1')
        self.assertEquals(1, len(starred))

        # Journalist unstars the message
        self.driver.find_element_by_class_name('button-star').click()
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element_by_id('starred-source-link-1')

    def _journalist_selects_all_sources_then_selects_none(self):
        self.driver.find_element_by_id('select_all').click()
        checkboxes = self.driver.find_elements_by_id('checkbox')
        for checkbox in checkboxes:
            self.assertTrue(checkbox.is_selected())

        self.driver.find_element_by_id('select_none').click()
        checkboxes = self.driver.find_elements_by_id('checkbox')
        for checkbox in checkboxes:
            self.assertFalse(checkbox.is_selected())

    def _journalist_downloads_message(self):
        self.driver.find_element_by_css_selector(
            '#un-starred-source-link-1').click()

        submissions = self.driver.find_elements_by_css_selector(
            '#submissions a')
        self.assertEqual(1, len(submissions))

        file_url = submissions[0].get_attribute('href')

        # Downloading files with Selenium is tricky because it cannot automate
        # the browser's file download dialog. We can directly request the file
        # using urllib2, but we need to pass the cookies for the logged in user
        # for Flask to allow this.
        def cookie_string_from_selenium_cookies(cookies):
            cookie_strs = []
            for cookie in cookies:
                cookie_str = "=".join([cookie['name'], cookie['value']]) + ';'
                cookie_strs.append(cookie_str)
            return ' '.join(cookie_strs)

        submission_req = urllib2.Request(file_url)
        submission_req.add_header(
            'Cookie',
            cookie_string_from_selenium_cookies(
                self.driver.get_cookies()))
        raw_content = urllib2.urlopen(submission_req).read()

        decrypted_submission = self.gpg.decrypt(raw_content)
        submission = self._get_submission_content(file_url,
                                                  decrypted_submission)
        self.assertEqual(self.secret_message, submission)

    def _journalist_sends_reply_to_source(self):
        self.driver.find_element_by_id('reply-text-field').send_keys('Nice docs')

        self.driver.find_element_by_id('reply-button').click()

        self.assertIn("Thanks! Your reply has been stored.",
                      self.driver.page_source)
