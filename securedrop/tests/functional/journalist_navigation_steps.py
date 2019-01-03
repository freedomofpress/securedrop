import pytest
import re
import tempfile
import gzip
import time
import os
import random
import requests

from os.path import dirname

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


# A generator to get unlimited user names for our tests.
# The pages-layout tests require many users during
# the test run, that is why have the following
# implementation.
def get_journalist_usernames():
    yield "dellsberg"
    yield "jpb"
    yield "bassel"
    while True:
        num = random.randint(1000, 1000000)
        yield "journalist" + str(num)


journalist_usernames = get_journalist_usernames()


class JournalistNavigationStepsMixin():

    def _get_submission_content(self, file_url, raw_content):
        if not file_url.endswith(".gz.gpg"):
            return str(raw_content)

        with tempfile.TemporaryFile() as fp:
            fp.write(raw_content.data)
            fp.seek(0)

            gzf = gzip.GzipFile(mode='rb', fileobj=fp)
            content = gzf.read()

            return content

    def return_downloaded_content(self, url, cookies):
        """
        This downloads and returns the content to the caller
        :param url: URL to download
        :param cookies: the cookies to access
        :return: Content of the URL
        """
        proxies = None
        if ".onion" in url:
            proxies = {
                'http': 'socks5h://127.0.0.1:9150',
                'https': 'socks5h://127.0.0.1:9150'
            }
        r = requests.get(url, cookies=cookies, proxies=proxies,  stream=True)
        if r.status_code != 200:
            raise Exception("Failed to download the data.")
        data = b""
        for chunk in r.iter_content(1024):
            data += chunk
        return data

    def _input_text_in_login_form(self, username, password, token):
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

    def _try_login_user(self, username, password, token):
        self._input_text_in_login_form(username, password, token)
        submit_button = self.driver.find_element_by_css_selector(
            'button[type="submit"]')
        submit_button.send_keys(u'\ue007')

    def _login_user(self, username, password, otp, maxtries=3):
        token = str(otp.now())
        for i in range(maxtries):

            self._try_login_user(username, password, token)
            # Successful login should redirect to the index
            self.wait_for(lambda: self.driver.find_element_by_id(
               'logout'), timeout=self.sleep_time+10)
            if self.driver.current_url != self.journalist_location + '/':
                    new_token = str(otp.now())
                    while token == new_token:
                        time.sleep(1)
                        new_token = str(otp.now())
                        print("Token: {} New token: {}".format(token,
                                                               new_token))
                    token = new_token
            else:
                return

        # If we reach here, assert the error
        assert self.driver.current_url == self.journalist_location + '/',\
            self.driver.current_url + " " + self.journalist_location

    def _journalist_logs_in(self):
        # Create a test user for logging in
        self.user = self.admin_user['name']
        self.user_pw = self.admin_user['password']
        self._login_user(self.user, self.user_pw, self.admin_user['totp'])

        assert self.driver.find_element_by_css_selector(
            'div.journalist-view-all')

    def _journalist_visits_col(self):
        self.wait_for(lambda: self.driver.find_element_by_id(
            'cols'))

        self.safe_click_by_id('un-starred-source-link-1')

        self.wait_for(lambda: self.driver.find_element_by_css_selector(
            'ul#submissions'))

    def _journalist_selects_first_doc(self):
        self.driver.find_elements_by_name('doc_names_selected')[0].click()

        def doc_selected():
            assert self.driver.find_elements_by_name(
                'doc_names_selected')[0].is_selected()

        self.wait_for(doc_selected)

    def _journalist_clicks_on_modal(self, click_id):
        self.safe_click_by_id(click_id)

    def _journalist_clicks_delete_collections_cancel_on_modal(self):
        self._journalist_clicks_on_modal('cancel-collections-deletions')

    def _journalist_clicks_delete_selected_cancel_on_modal(self):
        self._journalist_clicks_on_modal('cancel-selected-deletions')

    def _journalist_clicks_delete_collection_cancel_on_modal(self):
        self._journalist_clicks_on_modal('cancel-collection-deletions')

    def _journalist_clicks_delete_collections_on_modal(self):
        self._journalist_clicks_on_modal('delete-collections')

        def collection_deleted():
            if not hasattr(self, 'accept_languages'):
                flash_msg = self.driver.find_element_by_css_selector('.flash')
                assert '1 collection deleted' in flash_msg.text
        self.wait_for(collection_deleted)

    def _journalist_clicks_delete_selected_on_modal(self):
        self._journalist_clicks_on_modal('delete-selected')

        def submission_deleted():
            if not hasattr(self, 'accept_languages'):
                flash_msg = self.driver.find_element_by_css_selector('.flash')
                assert 'Submission deleted.' in flash_msg.text
        self.wait_for(submission_deleted)

    def _journalist_clicks_delete_collection_on_modal(self):
        self._journalist_clicks_on_modal('delete-collection-button')

    def _journalist_clicks_delete_link(self, click_id, displayed_id):
        self.safe_click_by_id(click_id)
        self.wait_for(lambda: self.driver.find_element_by_id(displayed_id))

    def _journalist_clicks_delete_selected_link(self):
        self.safe_click_by_css_selector(
            'a#delete-selected-link > button.danger')
        self.wait_for(lambda: self.driver.find_element_by_id(
                      'delete-selected-confirmation-modal'))

    def _journalist_clicks_delete_collections_link(self):
        self._journalist_clicks_delete_link(
            'delete-collections-link',
            'delete-confirmation-modal')

    def _journalist_clicks_delete_collection_link(self):
        self._journalist_clicks_delete_link(
            'delete-collection-link',
            'delete-collection-confirmation-modal')

    def _journalist_uses_delete_selected_button_confirmation(self):
        selected_count = len(self.driver.find_elements_by_name(
            'doc_names_selected'))
        assert selected_count > 0

        self._journalist_selects_first_doc()
        self._journalist_clicks_delete_selected_link()
        self._journalist_clicks_delete_selected_cancel_on_modal()
        assert selected_count == len(self.driver.find_elements_by_name(
            'doc_names_selected'))

        self._journalist_clicks_delete_selected_link()
        self._journalist_clicks_delete_selected_on_modal()
        assert selected_count > len(self.driver.find_elements_by_name(
            'doc_names_selected'))

    def _journalist_uses_delete_collection_button_confirmation(self):
        self._journalist_clicks_delete_collection_link()
        self._journalist_clicks_delete_collection_cancel_on_modal()
        self._journalist_clicks_delete_collection_link()
        self._journalist_clicks_delete_collection_on_modal()

        # Now we should be redirected to the index.
        if not hasattr(self, 'accept-languages'):
            assert "Sources" in self.driver.find_element_by_tag_name('h1').text

    def _journalist_uses_delete_collections_button_confirmation(self):
        sources = self.driver.find_elements_by_class_name("code-name")
        assert len(sources) > 0

        self.safe_click_by_id('select_all')
        self._journalist_clicks_delete_collections_link()
        self._journalist_clicks_delete_collections_cancel_on_modal()

        self.safe_click_by_id('select_all')
        sources = self.driver.find_elements_by_class_name("code-name")
        assert len(sources) > 0

        self._journalist_clicks_delete_collections_link()
        self._journalist_clicks_delete_collections_on_modal()

        # We should be redirected to the index without those boxes selected.
        sources = self.driver.find_elements_by_class_name("code-name")
        assert len(sources) == 0

    def _admin_logs_in(self):
        self.admin = self.admin_user['name']
        self.admin_pw = self.admin_user['password']
        self._login_user(self.admin, self.admin_pw, self.admin_user['totp'])

        # Admin user should log in to the same interface as a
        # normal user, since there may be users who wish to be
        # both journalists and admins.
        assert self.driver.find_element_by_css_selector(
            'div.journalist-view-all')

        # Admin user should have a link that take them to the admin page
        assert self.driver.find_element_by_id(
            'link-admin-index')

    def _admin_visits_admin_interface(self):
        self.safe_click_by_id('link-admin-index')

        self.wait_for(lambda: self.driver.find_element_by_id(
            'add-user'))

    def _admin_visits_system_config_page(self):
        self.safe_click_by_id('update-instance-config')

        def config_page_loaded():
            assert self.driver.find_element_by_id(
                'test-ossec-alert')

        self.wait_for(config_page_loaded)

    def _admin_updates_logo_image(self):
        dir_name = dirname(dirname(dirname(os.path.abspath(__file__))))
        image_path = os.path.abspath(os.path.join(dir_name,
                                                  'static/i/logo.png'))
        logo_upload_input = self.driver.find_element_by_id('logo-upload')
        logo_upload_input.send_keys(image_path)

        self.safe_click_by_id('submit-logo-update')

        def updated_image():
            if not hasattr(self, 'accept_languages'):
                flash_msg = self.driver.find_element_by_css_selector('.flash')
                assert 'Image updated.' in flash_msg.text

        # giving extra time for upload to complete
        self.wait_for(updated_image, timeout=self.sleep_time*3)

    def _add_user(self, username, is_admin=False, hotp=None):
        username_field = self.driver.find_element_by_css_selector(
            'input[name="username"]')
        username_field.send_keys(username)

        if hotp:
            hotp_checkbox = self.driver.find_element_by_css_selector(
                'input[name="is_hotp"]')
            print(str(hotp_checkbox.__dict__))
            hotp_checkbox.click()
            hotp_secret = self.driver.find_element_by_css_selector(
                'input[name="otp_secret"]')
            hotp_secret.send_keys(hotp)

        if is_admin:
            self.safe_click_by_css_selector('input[name="is_admin"]')

        self.safe_click_by_css_selector('button[type=submit]')

    def _admin_adds_a_user(self, is_admin=False, new_username=''):
        self.wait_for(lambda: self.driver.find_element_by_id(
            'add-user').is_enabled())
        self.safe_click_by_css_selector('button#add-user')

        self.wait_for(lambda: self.driver.find_element_by_id(
            'username'))

        if not hasattr(self, 'accept_languages'):
            # The add user page has a form with an "ADD USER" button
            btns = self.driver.find_elements_by_tag_name('button')
            assert 'ADD USER' in [el.text for el in btns]

        password = self.driver.find_element_by_css_selector('#password') \
            .text.strip()

        if not new_username:
            new_username = journalist_usernames.next()
        self.new_user = dict(
                username=new_username,
                password=password,
            )
        self._add_user(self.new_user['username'], is_admin=is_admin)

        if not hasattr(self, 'accept_languages'):
            # Clicking submit on the add user form should redirect to
            # the FreeOTP page
            h1s = self.driver.find_elements_by_tag_name('h1')
            assert "Enable FreeOTP" in [el.text for el in h1s]

        shared_secret = self.driver.find_element_by_css_selector('#shared-secret').text.strip().replace(' ', '')  # noqa: E501
        self.create_new_totp(shared_secret)

        # Verify the two-factor authentication
        token_field = self.driver.find_element_by_css_selector(
            'input[name="token"]')
        token_field.send_keys(str(self.new_totp.now()))
        self.safe_click_by_css_selector('button[type=submit]')

        def user_token_added():
            if not hasattr(self, 'accept_languages'):
                # Successfully verifying the code should redirect to the admin
                # interface, and flash a message indicating success
                flash_msg = self.driver.find_elements_by_css_selector('.flash')
                assert (("Token in two-factor authentication "
                         "accepted for user {}.").format(
                             self.new_user['username']) in
                        [el.text for el in flash_msg])

        self.wait_for(user_token_added)

    def _admin_deletes_user(self):
        self.wait_for(lambda: self.driver.find_element_by_css_selector(
            '.delete-user'), timeout=60)

        # Get the delete user buttons
        delete_buttons = self.driver.find_elements_by_css_selector(
            '.delete-user')

        # Try to delete a user
        delete_buttons[0].click()

        # Wait for JavaScript alert to pop up and accept it.
        self._alert_wait()
        self._alert_accept()

        def user_deleted():
            if not hasattr(self, 'accept_languages'):
                flash_msg = self.driver.find_element_by_css_selector('.flash')
                assert "Deleted user" in flash_msg.text

        self.wait_for(user_deleted)

    def _admin_can_send_test_alert(self):
        alert_button = self.driver.find_element_by_id('test-ossec-alert')
        alert_button.click()

        def test_alert_sent():
            if not hasattr(self, 'accept_languages'):
                flash_msg = self.driver.find_element_by_css_selector('.flash')
                assert ("Test alert sent. Please check your email."
                        in flash_msg.text)
        self.wait_for(test_alert_sent)

    def _logout(self):
        # Click the logout link
        logout_link = self.driver.find_element_by_id('link-logout')
        logout_link.send_keys(" ")
        logout_link.click()
        self.wait_for(lambda: self.driver.find_element_by_css_selector(
           '.login-form'))

        # Logging out should redirect back to the login page
        def login_page():
            assert ("Login to access the journalist interface" in
                    self.driver.page_source)
        self.wait_for(login_page)

    def _check_login_with_otp(self, otp):
        self._logout()
        self._login_user(self.new_user['username'],
                         self.new_user['password'], otp)
        if not hasattr(self, 'accept_languages'):
            # Test that the new user was logged in successfully
            assert 'Sources' in self.driver.page_source

    def _new_user_can_log_in(self):
        # Log the admin user out
        self._logout()

        self.wait_for(lambda: self.driver.find_element_by_css_selector(
           '.login-form'))
        # Log the new user in
        self._login_user(self.new_user['username'],
                         self.new_user['password'],
                         self.new_totp)

        if not hasattr(self, 'accept_languages'):
            # Test that the new user was logged in successfully
            assert 'Sources' in self.driver.page_source

        # The new user was not an admin, so they should not have the admin
        # interface link available
        with pytest.raises(NoSuchElementException):
            self.driver.find_element_by_id('link-admin-index')

    def _new_admin_user_can_log_in(self):
        # Test login with mocked token
        self._check_login_with_otp(self.new_totp)

        # Newly added user who is an admin can visit admin interface
        self._admin_visits_admin_interface()

    def _edit_account(self):
        edit_account_link = self.driver.find_element_by_id(
            'link-edit-account')
        edit_account_link.click()

        # The header says "Edit your account"
        def edit_page_loaded():
            h1s = self.driver.find_elements_by_tag_name('h1')[0]
            assert 'Edit your account' == h1s.text
        self.wait_for(edit_page_loaded)

        # There's no link back to the admin interface.
        with pytest.raises(NoSuchElementException):
            self.driver.find_element_by_partial_link_text(
                'Back to admin interface')
        # There's no field to change your username.
        with pytest.raises(NoSuchElementException):
            self.driver.find_element_by_css_selector('#username')
        # There's no checkbox to change the admin status of your
        # account.
        with pytest.raises(NoSuchElementException):
            self.driver.find_element_by_css_selector('#is-admin')
        # 2FA reset buttons at the bottom point to the user URLs for reset.
        totp_reset_button = self.driver.find_elements_by_css_selector(
            '#reset-two-factor-totp')[0]
        assert ('/account/reset-2fa-totp' in
                totp_reset_button.get_attribute('action'))
        hotp_reset_button = self.driver.find_elements_by_css_selector(
            '#reset-two-factor-hotp')[0]
        assert ('/account/reset-2fa-hotp' in
                hotp_reset_button.get_attribute('action'))

    def _edit_user(self, username, is_admin=False):
        # XXXX
        self.wait_for(lambda: self.driver.find_element_by_id(
            'users'))

        new_user_edit_links = filter(
            lambda el: el.get_attribute('data-username') == username,
            self.driver.find_elements_by_tag_name('a'))
        assert 1 == len(new_user_edit_links)
        new_user_edit_links[0].click()

        def edit_user_page_loaded():
            h1s = self.driver.find_elements_by_tag_name('h1')[0]
            assert 'Edit user "{}"'.format(username) == h1s.text
        self.wait_for(edit_user_page_loaded)

        # There's a convenient link back to the admin interface.
        admin_interface_link = self.driver.find_element_by_partial_link_text(
            'Back to admin interface')
        assert re.search('/admin$', admin_interface_link.get_attribute('href'))
        # There's a field to change the user's username and it's already filled
        # out with the user's username.
        username_field = self.driver.find_element_by_css_selector('#username')
        assert username_field.get_attribute('placeholder') == username
        # There's a checkbox to change the admin status of the user and
        # it's already checked appropriately to reflect the current status of
        # our user.
        username_field = self.driver.find_element_by_css_selector('#is-admin')
        assert bool(username_field.get_attribute('checked')) == is_admin
        # 2FA reset buttons at the bottom point to the admin URLs for
        # resettting 2FA and include the correct user id in the hidden uid.
        totp_reset_button = self.driver.find_elements_by_css_selector(
            '#reset-two-factor-totp')[0]
        assert '/admin/reset-2fa-totp' in totp_reset_button.get_attribute(
            'action')
        totp_reset_uid = totp_reset_button.find_element_by_name('uid')
        assert totp_reset_uid.is_displayed() is False
        hotp_reset_button = self.driver.find_elements_by_css_selector(
            '#reset-two-factor-hotp')[0]
        assert '/admin/reset-2fa-hotp' in hotp_reset_button.get_attribute(
            'action')

        hotp_reset_uid = hotp_reset_button.find_element_by_name('uid')
        assert hotp_reset_uid.is_displayed() is False

    def _admin_can_edit_new_user(self):
        # Log the new user out
        self._logout()

        self.wait_for(lambda: self.driver.find_element_by_css_selector(
           '.login-form'))

        self._login_user(self.admin, self.admin_pw, self.admin_user['totp'])

        # Go to the admin interface
        self.safe_click_by_id('link-admin-index')

        self.wait_for(lambda: self.driver.find_element_by_css_selector(
            'button#add-user'))

        # Click the "edit user" link for the new user
        # self._edit_user(self.new_user['username'])
        new_user_edit_links = filter(
            lambda el: (el.get_attribute('data-username') ==
                        self.new_user['username']),
            self.driver.find_elements_by_tag_name('a'))
        assert len(new_user_edit_links) == 1
        new_user_edit_links[0].click()

        def can_edit_user():
            h = self.driver.find_elements_by_tag_name('h1')[0]
            assert 'Edit user "{}"'.format(self.new_user['username']) == h.text
        self.wait_for(can_edit_user)

        new_username = self.new_user['username'] + "2"

        username_field = self.driver.find_element_by_css_selector(
            'input[name="username"]')
        username_field.send_keys(new_username)
        update_user_btn = self.driver.find_element_by_css_selector(
            'button[type=submit]')
        update_user_btn.click()

        def user_edited():
            if not hasattr(self, 'accept_languages'):
                flash_msg = self.driver.find_element_by_css_selector('.flash')
                assert "Account updated." in flash_msg.text

        self.wait_for(user_edited)

        def can_edit_user2():
            assert ('"{}"'.format(new_username) in self.driver.page_source)
        self.wait_for(can_edit_user2)

        # Update self.new_user with the new username for the future tests
        self.new_user['username'] = new_username

        # Log the new user in with their new username
        self._logout()

        self.wait_for(lambda: self.driver.find_element_by_css_selector(
           '.login-form'))

        self._login_user(self.new_user['username'],
                         self.new_user['password'],
                         self.new_totp)
        if not hasattr(self, 'accept_languages'):
            def found_sources():
                assert 'Sources' in self.driver.page_source
            self.wait_for(found_sources)

        # Log the admin user back in
        self._logout()

        self.wait_for(lambda: self.driver.find_element_by_css_selector(
           '.login-form'))

        self._login_user(self.admin, self.admin_pw, self.admin_user['totp'])

        # Go to the admin interface
        self.safe_click_by_id('link-admin-index')

        self.wait_for(lambda: self.driver.find_element_by_css_selector(
            'button#add-user'))

        new_user_edit_links = filter(
            lambda el: (el.get_attribute('data-username') ==
                        self.new_user['username']),
            self.driver.find_elements_by_tag_name('a'))
        assert len(new_user_edit_links) == 1
        new_user_edit_links[0].click()

        self.wait_for(can_edit_user)

        new_password = self.driver.find_element_by_css_selector('#password') \
            .text.strip()
        self.new_user['password'] = new_password

        reset_pw_btn = self.driver.find_element_by_css_selector(
            '#reset-password')
        reset_pw_btn.click()

        def update_password_success():
            assert 'Password updated.' in self.driver.page_source

        # Wait until page refreshes to avoid causing a broken pipe error (#623)
        self.wait_for(update_password_success)

        # Log the new user in with their new password
        self._logout()
        self._login_user(self.new_user['username'],
                         self.new_user['password'],
                         self.new_totp)
        self.wait_for(found_sources)

    def _journalist_checks_messages(self):
        self.driver.get(self.journalist_location)

        # There should be 1 collection in the list of collections
        code_names = self.driver.find_elements_by_class_name('code-name')
        assert 0 != len(code_names), code_names
        assert 1 <= len(code_names), code_names

        if not hasattr(self, 'accept_languages'):
            # There should be a "1 unread" span in the sole collection entry
            unread_span = self.driver.find_element_by_css_selector(
                'span.unread')
            assert "1 unread" in unread_span.text

    def _journalist_stars_and_unstars_single_message(self):
        # Message begins unstarred
        with pytest.raises(NoSuchElementException):
            self.driver.find_element_by_id('starred-source-link-1')

        # Journalist stars the message
        self.driver.find_element_by_class_name('button-star').click()

        def message_starred():
            starred = self.driver.find_elements_by_id('starred-source-link-1')
            assert 1 == len(starred)
        self.wait_for(message_starred)

        # Journalist unstars the message
        self.driver.find_element_by_class_name('button-star').click()

        def message_unstarred():
            with pytest.raises(NoSuchElementException):
                self.driver.find_element_by_id('starred-source-link-1')
        self.wait_for(message_unstarred)

    def _journalist_selects_all_sources_then_selects_none(self):
        self.driver.find_element_by_id('select_all').click()
        checkboxes = self.driver.find_elements_by_id('checkbox')
        for checkbox in checkboxes:
            assert checkbox.is_selected()

        self.driver.find_element_by_id('select_none').click()
        checkboxes = self.driver.find_elements_by_id('checkbox')
        for checkbox in checkboxes:
            assert checkbox.is_selected() is False

    def _journalist_selects_the_first_source(self):
        self.driver.find_element_by_css_selector(
            '#un-starred-source-link-1').click()

    def _journalist_selects_documents_to_download(self):
        self.driver.find_element_by_id('select_all').click()

    def _journalist_downloads_message(self):
        self._journalist_selects_the_first_source()

        self.wait_for(lambda: self.driver.find_element_by_css_selector(
            'ul#submissions'))

        submissions = self.driver.find_elements_by_css_selector(
            '#submissions a')
        assert 1 == len(submissions)

        file_url = submissions[0].get_attribute('href')

        # Downloading files with Selenium is tricky because it cannot automate
        # the browser's file download dialog. We can directly request the file
        # using requests, but we need to pass the cookies for logged in user
        # for Flask to allow this.
        def cookie_string_from_selenium_cookies(cookies):
            result = {}
            for cookie in cookies:
                result[cookie['name']] = cookie['value']
            return result

        cks = cookie_string_from_selenium_cookies(self.driver.get_cookies())
        raw_content = self.return_downloaded_content(file_url, cks)

        decrypted_submission = self.gpg.decrypt(raw_content)
        submission = self._get_submission_content(file_url,
                                                  decrypted_submission)
        assert self.secret_message == submission

    def _journalist_composes_reply(self):
        reply_text = ('Thanks for the documents. Can you submit more '
                      'information about the main program?')
        self.wait_for(lambda: self.driver.find_element_by_id(
            'reply-text-field'))
        self.driver.find_element_by_id('reply-text-field').send_keys(
            reply_text
        )

    def _journalist_sends_reply_to_source(self):
        self._journalist_composes_reply()
        self.driver.find_element_by_id('reply-button').click()

        def reply_stored():
            if not hasattr(self, 'accept_languages'):
                assert ("Thanks. Your reply has been stored." in
                        self.driver.page_source)
        self.wait_for(reply_stored)

    def _visit_edit_account(self):
        self.safe_click_by_id('link-edit-account')

    def _visit_edit_secret(self, type):

        def edit_self_loaded():
            assert self.driver.find_element_by_id('reset-password')

        self.wait_for(edit_self_loaded)

        reset_form = self.driver.find_elements_by_css_selector(
            '#reset-two-factor-' + type)[0]
        assert ('/account/reset-2fa-' + type in
                reset_form.get_attribute('action'))

        reset_button = self.driver.find_elements_by_css_selector(
            '#button-reset-two-factor-' + type)[0]
        self.wait_for(lambda: reset_button.is_enabled())
        reset_button.click()

    def _set_hotp_secret(self):
        self.wait_for(lambda: self.driver.find_elements_by_css_selector(
            'input[name="otp_secret"]')[0])

        hotp_secret_field = self.driver.find_elements_by_css_selector(
            'input[name="otp_secret"]')[0]
        hotp_secret_field.send_keys('123456')
        submit_button = self.driver.find_element_by_css_selector(
            'button[type=submit]')
        submit_button.click()

    def _visit_edit_hotp_secret(self):
        self._visit_edit_secret('hotp')

    def _visit_edit_totp_secret(self):
        self._visit_edit_secret('totp')

    def _admin_visits_add_user(self):
        add_user_btn = self.driver.find_element_by_css_selector(
            'button#add-user')
        self.wait_for(lambda: add_user_btn.is_enabled() and
                      add_user_btn.is_displayed())
        add_user_btn.click()

        self.wait_for(lambda: self.driver.find_element_by_id(
            'username'))

    def _admin_visits_edit_user(self):
        new_user_edit_links = filter(
            lambda el: (el.get_attribute('data-username') ==
                        self.new_user['username']),
            self.driver.find_elements_by_tag_name('a'))
        assert len(new_user_edit_links) == 1
        new_user_edit_links[0].click()

        def can_edit_user():
            assert ('"{}"'.format(self.new_user['username']) in
                    self.driver.page_source)
        self.wait_for(can_edit_user)

    def _admin_visits_reset_2fa_hotp(self):
        hotp_reset_button = self.driver.find_elements_by_css_selector(
            '#reset-two-factor-hotp')[0]
        assert ('/admin/reset-2fa-hotp' in
                hotp_reset_button.get_attribute('action'))
        self.wait_for(lambda: hotp_reset_button.is_enabled())

        hotp_reset_button.location_once_scrolled_into_view
        actions = ActionChains(self.driver)
        actions.move_to_element(hotp_reset_button)
        actions.perform()
        hotp_reset_button.click()

    def _admin_accepts_2fa_js_alert(self):
        self._alert_wait()
        self._alert_accept()

    def _admin_visits_reset_2fa_totp(self):
        totp_reset_button = self.driver.find_elements_by_css_selector(
            '#reset-two-factor-totp')[0]
        assert ('/admin/reset-2fa-totp' in
                totp_reset_button.get_attribute('action'))
        totp_reset_button.click()

    def _admin_creates_a_user(self, hotp):
        add_user_btn = self.driver.find_element_by_css_selector(
            'button#add-user')
        self.wait_for(lambda: add_user_btn.is_enabled())
        add_user_btn.submit()
        self.wait_for(lambda: self.driver.find_element_by_id(
            'username'))

        self.new_user = dict(
            username='dellsberg',
            password='pentagonpapers')

        self._add_user(self.new_user['username'],
                       is_admin=False,
                       hotp=hotp)

    def _journalist_delete_all(self):
        for checkbox in self.driver.find_elements_by_name(
                'doc_names_selected'):
            checkbox.click()
        self.driver.find_element_by_id('delete-selected-link').click()

    def _journalist_confirm_delete_selected(self):
        self.wait_for(
            lambda: self.driver.find_element_by_id('delete-selected'))
        confirm_btn = self.driver.find_element_by_id('delete-selected')

        def button_available():
            confirm_btn = self.driver.find_element_by_id('delete-selected')
            assert (confirm_btn.is_enabled() and confirm_btn.is_displayed())

        self.wait_for(button_available)
        confirm_btn.submit()

    def _source_delete_key(self):
        filesystem_id = self.source_app.crypto_util.hash_codename(
            self.source_name)
        self.source_app.crypto_util.delete_reply_keypair(filesystem_id)

    def _journalist_continues_after_flagging(self):
        self.wait_for(lambda: self.driver.find_element_by_id(
            'continue-to-list'))
        continue_link = self.driver.find_element_by_id('continue-to-list')

        actions = ActionChains(self.driver)
        actions.move_to_element(continue_link).perform()
        continue_link.click()

    def _journalist_delete_none(self):
        self.driver.find_element_by_id('delete-selected-link').click()

    def _journalist_delete_all_confirmation(self):
        self.safe_click_by_id('select_all')
        self.safe_click_by_css_selector(
            'a#delete-selected-link > button.danger')

    def _journalist_delete_one(self):
        self.driver.find_elements_by_name('doc_names_selected')[0].click()
        self.driver.find_element_by_id('delete-selected-link').click()

    def _journalist_flags_source(self):
        self.safe_click_by_id('flag-button')

    def _journalist_visits_admin(self):
        self.driver.get(self.journalist_location + "/admin")

    def _journalist_fail_login(self):
        self._try_login_user("root", 'worse', 'mocked')

    def _journalist_fail_login_many(self):
        self.user = ""
        for _ in range(5 + 1):
            self._try_login_user(self.user, 'worse', 'mocked')

    def _admin_enters_journalist_account_details_hotp(self, username,
                                                      hotp_secret):
        username_field = self.driver.find_element_by_css_selector(
            'input[name="username"]')
        username_field.send_keys(username)

        hotp_secret_field = self.driver.find_element_by_css_selector(
            'input[name="otp_secret"]')
        hotp_secret_field.send_keys(hotp_secret)

        hotp_checkbox = self.driver.find_element_by_css_selector(
            'input[name="is_hotp"]')
        hotp_checkbox.click()

    def _journalist_uses_js_filter_by_sources(self):
        self.wait_for(lambda: self.driver.find_element_by_id("filter"))

        filter_box = self.driver.find_element_by_id("filter")
        filter_box.send_keys("thiswordisnotinthewordlist")

        sources = self.driver.find_elements_by_class_name("code-name")
        assert len(sources) > 0
        for source in sources:
            assert source.is_displayed() is False
        filter_box.clear()
        filter_box.send_keys(Keys.RETURN)

        for source in sources:
            assert source.is_displayed() is True

    def _journalist_uses_js_buttons_to_download_unread(self):
        self.driver.find_element_by_id('select_all').click()
        checkboxes = self.driver.find_elements_by_name('doc_names_selected')
        assert len(checkboxes) > 0
        for checkbox in checkboxes:
            assert checkbox.is_selected()

        self.driver.find_element_by_id('select_none').click()
        checkboxes = self.driver.find_elements_by_name('doc_names_selected')
        for checkbox in checkboxes:
            assert checkbox.is_selected() is False

        self.driver.find_element_by_id('select_unread').click()
        checkboxes = self.driver.find_elements_by_name('doc_names_selected')
        for checkbox in checkboxes:
            classes = checkbox.get_attribute('class')
            assert 'unread-cb' in classes
