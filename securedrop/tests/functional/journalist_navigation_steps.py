import urllib2
import tempfile
import zipfile

from selenium.common.exceptions import NoSuchElementException

from db import db_session, Journalist

class JournalistNavigationSteps():

    def _get_submission_content(self, file_url, raw_content):
        if not file_url.endswith(".zip.gpg"):
            return str(raw_content)

        with tempfile.TemporaryFile() as fp:
            fp.write(raw_content.data)
            fp.seek(0)

            zip_file = zipfile.ZipFile(fp)
            content = zip_file.open(zip_file.namelist()[0]).read()

            return content

    def _login_user(self, username, password, token):
        self.driver.get(self.journalist_location + "/login")
        username_field = self.driver.find_element_by_css_selector('input[name="username"]')
        username_field.send_keys(username)

        password_field = self.driver.find_element_by_css_selector('input[name="password"]')
        password_field.send_keys(password)

        token_field = self.driver.find_element_by_css_selector('input[name="token"]')
        token_field.send_keys(token)

        submit_button = self.driver.find_element_by_css_selector('button[type=submit]')
        submit_button.click()

        # Successful login should redirect to the index
        self.assertEquals(self.driver.current_url, self.journalist_location + '/')

    def _journalist_logs_in(self):
        # Create a test user for logging in
        test_user_info = dict(
            username='test',
            password='test')
        test_user = Journalist(**test_user_info)
        db_session.add(test_user)
        db_session.commit()

        self._login_user(test_user_info['username'],
                         test_user_info['password'],
                         test_user.totp.now())

        headline = self.driver.find_element_by_css_selector('span.headline')
        self.assertIn('Sources', headline.text)

    def _admin_logs_in(self):
        # Create a test admin user for logging in
        admin_user_info = dict(
            username='admin',
            password='admin',
            is_admin=True)
        admin_user = Journalist(**admin_user_info)
        db_session.add(admin_user)
        db_session.commit()

        # Stash the admin user on self so we can use it in later tests
        self.admin_user = admin_user_info
        self.admin_user['orm_obj'] = admin_user

        self._login_user(admin_user_info['username'],
                         admin_user_info['password'],
                         admin_user.totp.now())

        # Admin user should log in to the same interface as a normal user,
        # since there may be users who wish to be both journalists and admins.
        headline = self.driver.find_element_by_css_selector('span.headline')
        self.assertIn('Sources', headline.text)

        # Admin user should have a link that take them to the admin page
        links = self.driver.find_elements_by_tag_name('a')
        self.assertIn('Admin', [ el.text for el in links ])

    def _admin_visits_admin_interface(self):
        admin_interface_link = self.driver.find_element_by_link_text('Admin')
        admin_interface_link.click()

        h2s = self.driver.find_elements_by_tag_name('h2')
        self.assertIn("Admin Interface", [ el.text for el in h2s ])

        users_table_rows = self.driver.find_elements_by_css_selector('table#users tr.user')
        self.assertEquals(len(users_table_rows), 1)

    def _add_user(self, username, password, is_admin=False):
        username_field = self.driver.find_element_by_css_selector('input[name="username"]')
        username_field.send_keys(username)

        password_field = self.driver.find_element_by_css_selector('input[name="password"]')
        password_field.send_keys(password)

        password_again_field = self.driver.find_element_by_css_selector('input[name="password_again"]')
        password_again_field.send_keys(password)

        if is_admin:
            # TODO implement (checkbox is unchecked by default)
            pass

        submit_button = self.driver.find_element_by_css_selector('button[type=submit]')
        submit_button.click()

    def _admin_adds_a_user(self):
        add_user_btn = self.driver.find_element_by_css_selector('button#add-user')
        add_user_btn.click()

        # The add user page has a form with an "Add user" button
        btns = self.driver.find_elements_by_tag_name('button')
        self.assertIn('Add user', [ el.text for el in btns ])

        self.new_user = dict(
            username='dellsberg',
            password='pentagonpapers')

        self._add_user(self.new_user['username'], self.new_user['password'])

        # Clicking submit on the add user form should redirect to the Google
        # Authenticator page
        h1s = self.driver.find_elements_by_tag_name('h1')
        self.assertIn("Enable Google Authenticator", [ el.text for el in h1s ])

        # Retrieve the saved user object from the db and keep it around for
        # futher testing
        self.new_user['orm_obj'] = Journalist.query.filter(
                Journalist.username == self.new_user['username']).one()

        # Verify the two factor authentication
        token_field = self.driver.find_element_by_css_selector('input[name="token"]')
        token_field.send_keys(self.new_user['orm_obj'].totp.now())
        submit_button = self.driver.find_element_by_css_selector('button[type=submit]')
        submit_button.click()

        # Successfully verifying the code should redirect to the admin
        # interface, and flash a message indicating success
        flashed_msgs = self.driver.find_elements_by_css_selector('p.flash')
        self.assertIn("Two factor token successfully verified for user {}!".format(self.new_user['username']), [ el.text for el in flashed_msgs ])

    def _logout(self):
        # Click the logout link
        logout_link = self.driver.find_element_by_link_text('Logout')
        logout_link.click()

        # Logging out should redirect back to the login page
        self.wait_for(
            lambda: self.assertIn("Login to access the journalist interface",
                                  self.driver.page_source)
            )

    def _new_user_can_log_in(self):
        # Log the admin user out
        self._logout()

        # Log the new user in
        self._login_user(self.new_user['username'],
                         self.new_user['password'],
                         self.new_user['orm_obj'].totp.now())

        # Test that the new user was logged in successfully
        self.assertIn('Sources', self.driver.page_source)

        # The new user was not an admin, so they should not have the admin
        # interface link available
        self.assertRaises(NoSuchElementException,
                          self.driver.find_element_by_link_text,
                          'Admin')

    def _edit_user(self, username):
        new_user_edit_links = filter(
                lambda el: el.get_attribute('data-username') == username,
                self.driver.find_elements_by_tag_name('a'))
        self.assertEquals(len(new_user_edit_links), 1)
        new_user_edit_links[0].click()

    def _admin_can_edit_new_user(self):
        # Log the new user out
        self._logout()

        self._login_user(self.admin_user['username'],
                         self.admin_user['password'],
                         self.admin_user['orm_obj'].totp.now())

        # Go to the admin interface
        admin_interface_link = self.driver.find_element_by_link_text('Admin')
        admin_interface_link.click()

        # Click the "edit user" link for the new user
        #self._edit_user(self.new_user['username'])
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

        username_field = self.driver.find_element_by_css_selector('input[name="username"]')
        username_field.send_keys(new_username)
        update_user_btn = self.driver.find_element_by_css_selector('button[type=submit]')
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
                         self.new_user['orm_obj'].totp.now())
        self.wait_for(
            lambda: self.assertIn('Sources', self.driver.page_source)
            )

        # Log the admin user back in
        self._logout()
        self._login_user(self.admin_user['username'],
                         self.admin_user['password'],
                         self.admin_user['orm_obj'].totp.now())

        # Go to the admin interface
        admin_interface_link = self.driver.find_element_by_link_text('Admin')
        admin_interface_link.click()
        # Edit the new user's password
        self._edit_user(self.new_user['username'])

        new_password = self.new_user['password'] + "2"
        password_field = self.driver.find_element_by_css_selector('input[name="password"]')
        password_field.send_keys(new_password)
        password_again_field = self.driver.find_element_by_css_selector('input[name="password_again"]')
        password_again_field.send_keys(new_password)
        update_user_btn = self.driver.find_element_by_css_selector('button#update-user')
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
                         self.new_user['orm_obj'].totp.now())
        self.wait_for(
            lambda: self.assertIn('Sources', self.driver.page_source)
            )

    def _journalist_checks_messages(self):
        self.driver.get(self.journalist_location)

        code_names = self.driver.find_elements_by_class_name('code-name')
        self.assertEquals(1, len(code_names))

    def _journalist_downloads_message(self):
        self.driver.find_element_by_css_selector('#un-starred-source-link-1').click()

        submissions = self.driver.find_elements_by_css_selector('#submissions a')
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
        submission_req.add_header('Cookie',
                cookie_string_from_selenium_cookies(self.driver.get_cookies()))
        raw_content = urllib2.urlopen(submission_req).read()

        decrypted_submission = self.gpg.decrypt(raw_content)
        submission = self._get_submission_content(file_url, decrypted_submission)
        self.assertEqual(self.secret_message, submission)
