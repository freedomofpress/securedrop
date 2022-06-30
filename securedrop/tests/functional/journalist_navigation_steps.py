from __future__ import print_function

import gzip
import logging
import os
import random
import re
import tempfile
import time
from os.path import dirname

import pytest
import requests
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


# Number of times to try flaky clicks.
from encryption import EncryptionManager
from tests.functional.tor_utils import proxies_for_url
from source_user import _SourceScryptManager
from tests.test_encryption import import_journalist_private_key

CLICK_ATTEMPTS = 15


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


class JournalistNavigationStepsMixin:
    def _get_submission_content(self, file_url, raw_content):
        if not file_url.endswith(".gz.gpg"):
            return str(raw_content)

        with tempfile.TemporaryFile() as fp:
            fp.write(raw_content.data)
            fp.seek(0)

            gzf = gzip.GzipFile(mode="rb", fileobj=fp)
            content = gzf.read()

            return content

    def return_downloaded_content(self, url, cookies):
        """
        This downloads and returns the content to the caller
        :param url: URL to download
        :param cookies: the cookies to access
        :return: Content of the URL
        """
        r = requests.get(url, cookies=cookies, proxies=proxies_for_url(url), stream=True)
        if r.status_code != 200:
            raise Exception("Failed to download the data.")
        data = b""
        for chunk in r.iter_content(1024):
            data += chunk
        return data

    def _input_text_in_login_form(self, username, password, token):
        self.driver.get(self.journalist_location + "/login")
        self.safe_send_keys_by_css_selector('input[name="username"]', username)
        self.safe_send_keys_by_css_selector('input[name="password"]', password)
        self.safe_send_keys_by_css_selector('input[name="token"]', token)

    def _try_login_user(self, username, password, token):
        self._input_text_in_login_form(username, password, token)
        self.safe_click_by_css_selector('button[type="submit"]')

    def _login_user(self, username, password, otp, maxtries=3):
        token = str(otp.now())
        for i in range(maxtries):

            self._try_login_user(username, password, token)
            # Successful login should redirect to the index
            self.wait_for(
                lambda: self.driver.find_element_by_id("link-logout"), timeout=self.timeout * 2
            )
            if self.driver.current_url != self.journalist_location + "/":
                new_token = str(otp.now())
                while token == new_token:
                    time.sleep(1)
                    new_token = str(otp.now())
                token = new_token
            else:
                return

        # If we reach here, assert the error
        assert self.driver.current_url == self.journalist_location + "/", (
            self.driver.current_url + " " + self.journalist_location
        )

    def _is_on_journalist_homepage(self):
        return self.wait_for(
            lambda: self.driver.find_element_by_css_selector("div.journalist-view-all")
        )

    def _journalist_logs_in(self):
        # Create a test user for logging in
        self.user = self.admin_user["name"]
        self.user_pw = self.admin_user["password"]
        self._login_user(self.user, self.user_pw, self.admin_user["totp"])
        assert self._is_on_journalist_homepage()

    def _journalist_visits_col(self):
        self.wait_for(lambda: self.driver.find_element_by_css_selector("table#collections"))

        self.safe_click_by_id("un-starred-source-link-1")

        self.wait_for(lambda: self.driver.find_element_by_css_selector("table#submissions"))

    def _journalist_selects_first_doc(self):
        self.safe_click_by_css_selector('input[type="checkbox"][name="doc_names_selected"]')

        self.wait_for(
            lambda: expected_conditions.element_located_to_be_selected(
                (By.CSS_SELECTOR, 'input[type="checkbox"][name="doc_names_selected"]')
            )
        )

        assert self.driver.find_element_by_css_selector(
            'input[type="checkbox"][name="doc_names_selected"]'
        ).is_selected()

    def _journalist_clicks_on_modal(self, click_id):
        self.safe_click_by_id(click_id)

    def _journalist_clicks_delete_collections_cancel_on_modal(self):
        self._journalist_clicks_on_modal("cancel-collections-deletions")

    def _journalist_clicks_delete_link(self, click_id, displayed_id):
        self.safe_click_by_id(click_id)
        self.wait_for(lambda: self.driver.find_element_by_id(displayed_id))

    def _journalist_clicks_delete_selected_link(self):
        self.safe_click_by_css_selector("a#delete-selected-link")
        self.wait_for(lambda: self.driver.find_element_by_id("delete-selected-confirmation-modal"))

    def _admin_logs_in(self):
        self.admin = self.admin_user["name"]
        self.admin_pw = self.admin_user["password"]
        self._login_user(self.admin, self.admin_pw, self.admin_user["totp"])

        # Admin user should log in to the same interface as a
        # normal user, since there may be users who wish to be
        # both journalists and admins.
        assert self._is_on_journalist_homepage()

        # Admin user should have a link that take them to the admin page
        assert self.driver.find_element_by_id("link-admin-index")

    def _admin_visits_admin_interface(self):
        self.safe_click_by_id("link-admin-index")

        self.wait_for(lambda: self.driver.find_element_by_id("add-user"))

    def _admin_visits_system_config_page(self):
        self.safe_click_by_id("update-instance-config")

        def config_page_loaded():
            assert self.driver.find_element_by_id("test-ossec-alert")

        self.wait_for(config_page_loaded)

    def _admin_updates_logo_image(self):
        dir_name = dirname(dirname(dirname(os.path.abspath(__file__))))
        image_path = os.path.abspath(os.path.join(dir_name, "static/i/logo.png"))

        self.safe_send_keys_by_id("logo-upload", image_path)

        self.safe_click_by_id("submit-logo-update")

        def updated_image():
            if not self.accept_languages:
                flash_msg = self.driver.find_element_by_css_selector(".flash")
                assert "Image updated." in flash_msg.text

        # giving extra time for upload to complete
        self.wait_for(updated_image, timeout=self.timeout * 6)

    def _admin_disallows_document_uploads(self):
        if not self.driver.find_element_by_id("prevent_document_uploads").is_selected():
            self.safe_click_by_id("prevent_document_uploads")
            self.safe_click_by_id("submit-submission-preferences")

        def preferences_saved():
            flash_msg = self.driver.find_element_by_css_selector(".flash")
            assert "Preferences saved." in flash_msg.text
        self.wait_for(preferences_saved, timeout=self.timeout * 6)

    def _admin_allows_document_uploads(self):
        if self.driver.find_element_by_id("prevent_document_uploads").is_selected():
            self.safe_click_by_id("prevent_document_uploads")
            self.safe_click_by_id("submit-submission-preferences")

        def preferences_saved():
            flash_msg = self.driver.find_element_by_css_selector(".flash")
            assert "Preferences saved." in flash_msg.text
        self.wait_for(preferences_saved, timeout=self.timeout * 6)

    def _admin_sets_organization_name(self):
        assert self.orgname_default == self.driver.title
        self.driver.find_element_by_id('organization_name').clear()
        self.safe_send_keys_by_id("organization_name", self.orgname_new)
        self.safe_click_by_id("submit-update-org-name")

        def preferences_saved():
            flash_msg = self.driver.find_element_by_css_selector(".flash")
            assert "Preferences saved." in flash_msg.text

        self.wait_for(preferences_saved, timeout=self.timeout * 6)
        assert self.orgname_new == self.driver.title

    def _add_user(self, username, first_name="", last_name="", is_admin=False, hotp=None):
        self.safe_send_keys_by_css_selector('input[name="username"]', username)

        if first_name:
            self.safe_send_keys_by_id("first_name", first_name)

        if last_name:
            self.safe_send_keys_by_id("last_name", last_name)

        if hotp:
            self.safe_click_all_by_css_selector('input[name="is_hotp"]')
            self.safe_send_keys_by_css_selector('input[name="otp_secret"]', hotp)

        if is_admin:
            self.safe_click_by_css_selector('input[name="is_admin"]')

        self.safe_click_by_css_selector("button[type=submit]")

        self.wait_for(lambda: self.driver.find_element_by_id("check-token"))

    def _admin_adds_a_user_with_invalid_username(self):
        self.safe_click_by_id("add-user")

        self.wait_for(lambda: self.driver.find_element_by_id("username"))

        if not self.accept_languages:
            # The add user page has a form with an "ADD USER" button
            btns = self.driver.find_elements_by_tag_name("button")
            assert "ADD USER" in [el.text for el in btns]

        invalid_username = 'deleted'

        self.safe_send_keys_by_css_selector('input[name="username"]', invalid_username)

        self.safe_click_by_css_selector("button[type=submit]")

        self.wait_for(lambda: self.driver.find_element_by_css_selector(".form-validation-error"))

        error_msg = self.driver.find_element_by_css_selector(".form-validation-error")
        assert "This username is invalid because it is reserved for internal use " \
               "by the software." in error_msg.text

    def _admin_adds_a_user(self, is_admin=False, new_username=""):
        self.safe_click_by_id("add-user")

        self.wait_for(lambda: self.driver.find_element_by_id("username"))

        if not self.accept_languages:
            # The add user page has a form with an "ADD USER" button
            btns = self.driver.find_elements_by_tag_name("button")
            assert "ADD USER" in [el.text for el in btns]

        password = self.driver.find_element_by_css_selector("#password").text.strip()

        if not new_username:
            new_username = next(journalist_usernames)
        self.new_user = dict(username=new_username, first_name='', last_name='', password=password)
        self._add_user(self.new_user["username"],
                       first_name=self.new_user['first_name'],
                       last_name=self.new_user['last_name'],
                       is_admin=is_admin)

        if not self.accept_languages:
            # Clicking submit on the add user form should redirect to
            # the FreeOTP page
            h1s = [h1.text for h1 in self.driver.find_elements_by_tag_name("h1")]
            assert "Enable FreeOTP" in h1s

        shared_secret = (
            self.driver.find_element_by_css_selector("#shared-secret").text.strip().replace(" ", "")
        )
        self.create_new_totp(shared_secret)

        # Verify the two-factor authentication
        self.safe_send_keys_by_css_selector('input[name="token"]', str(self.new_totp.now()))
        self.safe_click_by_css_selector("button[type=submit]")

        def user_token_added():
            if not self.accept_languages:
                # Successfully verifying the code should redirect to the admin
                # interface, and flash a message indicating success
                flash_msg = self.driver.find_elements_by_css_selector(".flash")
                assert "The two-factor code for user \"{}\" was verified successfully.".format(
                    self.new_user["username"]
                ) in [el.text for el in flash_msg]

        self.wait_for(user_token_added)

    def _admin_deletes_user(self):
        for i in range(CLICK_ATTEMPTS):
            try:
                self.safe_click_by_css_selector(".delete-user a")
                self.wait_for(
                    lambda: expected_conditions.element_to_be_clickable((By.ID, "delete-selected"))
                )
                self.safe_click_by_id("delete-selected")
                self.alert_wait()
                self.alert_accept()
                break
            except TimeoutException:
                # Selenium has failed to click, and the confirmation
                # alert didn't happen. Try once more.
                logging.info("Selenium has failed to click yet again; retrying.")

        def user_deleted():
            if not self.accept_languages:
                flash_msg = self.driver.find_element_by_css_selector(".flash")
                assert "Deleted user" in flash_msg.text

        self.wait_for(user_deleted)

    def _admin_can_send_test_alert(self):
        alert_button = self.driver.find_element_by_id("test-ossec-alert")
        alert_button.click()

        def test_alert_sent():
            if not self.accept_languages:
                flash_msg = self.driver.find_element_by_css_selector(".flash")
                assert "Test alert sent. Please check your email." in flash_msg.text

        self.wait_for(test_alert_sent)

    def _logout(self):
        # Click the logout link
        self.safe_click_by_id("link-logout")
        self.wait_for(lambda: self.driver.find_element_by_css_selector(".login-form"))

        # Logging out should redirect back to the login page
        def login_page():
            assert "Login to access the journalist interface" in self.driver.page_source

        self.wait_for(login_page)

    def _check_login_with_otp(self, otp):
        self._logout()
        self._login_user(self.new_user["username"], self.new_user["password"], otp)
        assert self._is_on_journalist_homepage()

    def _new_user_can_log_in(self):
        # Log the admin user out
        self._logout()

        self.wait_for(lambda: self.driver.find_element_by_css_selector(".login-form"))
        # Log the new user in
        self._login_user(self.new_user["username"], self.new_user["password"], self.new_totp)

        assert self._is_on_journalist_homepage()

        # The new user was not an admin, so they should not have the admin
        # interface link available
        with pytest.raises(NoSuchElementException):
            self.driver.find_element_by_id("link-admin-index")

    def _new_admin_user_can_log_in(self):
        # Test login with mocked token
        self._check_login_with_otp(self.new_totp)

        # Newly added user who is an admin can visit admin interface
        self._admin_visits_admin_interface()

    def _edit_account(self):
        edit_account_link = self.driver.find_element_by_id("link-edit-account")
        edit_account_link.click()

        # The header says "Edit your account"
        def edit_page_loaded():
            h1s = self.driver.find_elements_by_tag_name("h1")[0]
            assert "Edit your account" == h1s.text

        self.wait_for(edit_page_loaded)

        # There's no link back to the admin interface.
        with pytest.raises(NoSuchElementException):
            self.driver.find_element_by_partial_link_text("Back to admin interface")
        # There's no field to change your username.
        with pytest.raises(NoSuchElementException):
            self.driver.find_element_by_css_selector("#username")
        # There's no checkbox to change the admin status of your
        # account.
        with pytest.raises(NoSuchElementException):
            self.driver.find_element_by_css_selector("#is-admin")
        # 2FA reset buttons at the bottom point to the user URLs for reset.
        totp_reset_button = self.driver.find_elements_by_css_selector("#reset-two-factor-totp")[0]
        assert "/account/reset-2fa-totp" in totp_reset_button.get_attribute("action")
        hotp_reset_button = self.driver.find_elements_by_css_selector("#reset-two-factor-hotp")[0]
        assert "/account/reset-2fa-hotp" in hotp_reset_button.get_attribute("action")

    def _edit_user(self, username, is_admin=False):
        self.wait_for(lambda: self.driver.find_element_by_id("users"))

        selector = 'a.edit-user[data-username="{}"]'.format(username)
        new_user_edit_links = self.driver.find_elements_by_css_selector(selector)

        assert 1 == len(new_user_edit_links)
        new_user_edit_links[0].click()

        def edit_user_page_loaded():
            h1s = self.driver.find_elements_by_tag_name("h1")[0]
            assert 'Edit user "{}"'.format(username) == h1s.text

        self.wait_for(edit_user_page_loaded)

        # There's a convenient link back to the admin interface.
        admin_interface_link = self.driver.find_element_by_partial_link_text(
            "Back to admin interface"
        )
        assert re.search("/admin$", admin_interface_link.get_attribute("href"))
        # There's a field to change the user's username and it's already filled
        # out with the user's username.
        username_field = self.driver.find_element_by_css_selector("#username")
        assert username_field.get_attribute("value") == username
        # There's a checkbox to change the admin status of the user and
        # it's already checked appropriately to reflect the current status of
        # our user.
        username_field = self.driver.find_element_by_css_selector("#is-admin")
        assert bool(username_field.get_attribute("checked")) == is_admin
        # 2FA reset buttons at the bottom point to the admin URLs for
        # resettting 2FA and include the correct user id in the hidden uid.
        totp_reset_button = self.driver.find_elements_by_css_selector("#reset-two-factor-totp")[0]
        assert "/admin/reset-2fa-totp" in totp_reset_button.get_attribute("action")
        totp_reset_uid = totp_reset_button.find_element_by_name("uid")
        assert totp_reset_uid.is_displayed() is False
        hotp_reset_button = self.driver.find_elements_by_css_selector("#reset-two-factor-hotp")[0]
        assert "/admin/reset-2fa-hotp" in hotp_reset_button.get_attribute("action")

        hotp_reset_uid = hotp_reset_button.find_element_by_name("uid")
        assert hotp_reset_uid.is_displayed() is False

    def _admin_editing_invalid_username(self):
        # Log the new user out
        self._logout()

        self.wait_for(lambda: self.driver.find_element_by_css_selector(".login-form"))

        self._login_user(self.admin, self.admin_pw, self.admin_user["totp"])

        # Go to the admin interface
        self.safe_click_by_id("link-admin-index")

        self.wait_for(lambda: self.driver.find_element_by_id("add-user"))

        # Click the "edit user" link for the new user
        # self._edit_user(self.new_user['username'])
        selector = 'a.edit-user[data-username="{}"]'.format(self.new_user["username"])
        new_user_edit_links = self.driver.find_elements_by_css_selector(selector)
        assert len(new_user_edit_links) == 1
        new_user_edit_links[0].click()

        def can_edit_user():
            h = self.driver.find_elements_by_tag_name("h1")[0]
            assert 'Edit user "{}"'.format(self.new_user["username"]) == h.text

        self.wait_for(can_edit_user)

        new_username = "deleted"

        self.safe_send_keys_by_css_selector('input[name="username"]', Keys.CONTROL + "a")
        self.safe_send_keys_by_css_selector('input[name="username"]', Keys.DELETE)
        self.safe_send_keys_by_css_selector('input[name="username"]', new_username)
        self.safe_click_by_css_selector("button[type=submit]")

        def user_edited():
            if not self.accept_languages:
                flash_msg = self.driver.find_element_by_css_selector(".flash")
                assert "Invalid username" in flash_msg.text

        self.wait_for(user_edited)

    def _admin_can_edit_new_user(self):
        # Log the new user out
        self._logout()

        self.wait_for(lambda: self.driver.find_element_by_css_selector(".login-form"))

        self._login_user(self.admin, self.admin_pw, self.admin_user["totp"])

        # Go to the admin interface
        self.safe_click_by_id("link-admin-index")

        self.wait_for(lambda: self.driver.find_element_by_id("add-user"))

        # Click the "edit user" link for the new user
        # self._edit_user(self.new_user['username'])
        selector = 'a.edit-user[data-username="{}"]'.format(self.new_user["username"])
        new_user_edit_links = self.driver.find_elements_by_css_selector(selector)
        assert len(new_user_edit_links) == 1
        new_user_edit_links[0].click()

        def can_edit_user():
            h = self.driver.find_elements_by_tag_name("h1")[0]
            assert 'Edit user "{}"'.format(self.new_user["username"]) == h.text

        self.wait_for(can_edit_user)

        new_characters = "2"
        new_username = self.new_user["username"] + new_characters

        self.safe_send_keys_by_css_selector('input[name="username"]', new_characters)
        self.safe_click_by_css_selector("button[type=submit]")

        def user_edited():
            if not self.accept_languages:
                flash_msg = self.driver.find_element_by_css_selector(".flash")
                assert "Account updated." in flash_msg.text

        self.wait_for(user_edited)

        def can_edit_user2():
            assert '"{}"'.format(new_username) in self.driver.page_source

        self.wait_for(can_edit_user2)

        # Update self.new_user with the new username for the future tests
        self.new_user["username"] = new_username

        # Log the new user in with their new username
        self._logout()

        self.wait_for(lambda: self.driver.find_element_by_css_selector(".login-form"))

        self._login_user(self.new_user["username"], self.new_user["password"], self.new_totp)

        assert self._is_on_journalist_homepage()

        # Log the admin user back in
        self._logout()

        self.wait_for(lambda: self.driver.find_element_by_css_selector(".login-form"))

        self._login_user(self.admin, self.admin_pw, self.admin_user["totp"])

        # Go to the admin interface
        self.safe_click_by_id("link-admin-index")

        self.wait_for(lambda: self.driver.find_element_by_id("add-user"))

        selector = 'a.edit-user[data-username="{}"]'.format(self.new_user["username"])
        new_user_edit_links = self.driver.find_elements_by_css_selector(selector)
        assert len(new_user_edit_links) == 1
        self.safe_click_by_css_selector(selector)

        self.wait_for(can_edit_user)

        new_password = self.driver.find_element_by_css_selector("#password").text.strip()
        self.new_user["password"] = new_password

        reset_pw_btn = self.driver.find_element_by_css_selector("#reset-password")
        reset_pw_btn.click()

        def update_password_success():
            assert "Password updated." in self.driver.page_source

        # Wait until page refreshes to avoid causing a broken pipe error (#623)
        self.wait_for(update_password_success)

        # Log the new user in with their new password
        self._logout()
        self._login_user(self.new_user["username"], self.new_user["password"], self.new_totp)

        assert self._is_on_journalist_homepage()

    def _journalist_checks_messages(self):
        self.driver.get(self.journalist_location)

        # There should be 1 collection in the list of collections
        code_names = self.driver.find_elements_by_class_name("code-name")
        assert 0 != len(code_names), code_names
        assert 1 <= len(code_names), code_names

        if not self.accept_languages:
            # There should be a "1 unread" span in the sole collection entry
            unread_span = self.driver.find_element_by_css_selector("tr.unread")
            assert "1 unread" in unread_span.text

    def _journalist_stars_and_unstars_single_message(self):
        # Message begins unstarred
        with pytest.raises(NoSuchElementException):
            self.driver.find_element_by_id("starred-source-link-1")

        # Journalist stars the message
        self.driver.find_element_by_class_name("button-star").click()

        def message_starred():
            starred = self.driver.find_elements_by_id("starred-source-link-1")
            assert 1 == len(starred)

        self.wait_for(message_starred)

        # Journalist unstars the message
        self.driver.find_element_by_class_name("button-star").click()

        def message_unstarred():
            with pytest.raises(NoSuchElementException):
                self.driver.find_element_by_id("starred-source-link-1")

        self.wait_for(message_unstarred)

    def _journalist_selects_the_first_source(self):
        self.driver.find_element_by_css_selector("#un-starred-source-link-1").click()

    def _journalist_selects_all_documents(self):
        checkboxes = self.driver.find_elements_by_name("doc_names_selected")
        for checkbox in checkboxes:
            checkbox.click()

    def _journalist_downloads_message(self):
        self._journalist_selects_the_first_source()

        self.wait_for(lambda: self.driver.find_element_by_css_selector("table#submissions"))

        submissions = self.driver.find_elements_by_css_selector("#submissions a")
        assert 1 == len(submissions)

        file_url = submissions[0].get_attribute("href")

        # Downloading files with Selenium is tricky because it cannot automate
        # the browser's file download dialog. We can directly request the file
        # using requests, but we need to pass the cookies for logged in user
        # for Flask to allow this.
        def cookie_string_from_selenium_cookies(cookies):
            result = {}
            for cookie in cookies:
                result[cookie["name"]] = cookie["value"]
            return result

        cks = cookie_string_from_selenium_cookies(self.driver.get_cookies())
        raw_content = self.return_downloaded_content(file_url, cks)

        encryption_mgr = EncryptionManager.get_default()
        with import_journalist_private_key(encryption_mgr):
            decrypted_submission = encryption_mgr._gpg.decrypt(raw_content)
        submission = self._get_submission_content(file_url, decrypted_submission)
        if type(submission) == bytes:
            submission = submission.decode("utf-8")

        assert self.secret_message == submission

    def _journalist_composes_reply(self):
        reply_text = (
            "Thanks for the documents. Can you submit more " "information about the main program?"
        )
        self.wait_for(lambda: self.driver.find_element_by_id("reply-text-field"))
        self.safe_send_keys_by_id("reply-text-field", reply_text)

    def _journalist_sends_reply_to_source(self):
        self._journalist_composes_reply()
        self.driver.find_element_by_id("reply-button").click()

        def reply_stored():
            if not self.accept_languages:
                assert "The source will receive your reply" in self.driver.page_source

        self.wait_for(reply_stored)

    def _visit_edit_account(self):
        self.safe_click_by_id("link-edit-account")

    def _visit_edit_secret(self, otp_type, tooltip_text=''):
        reset_form = self.wait_for(
            lambda: self.driver.find_element_by_id("reset-two-factor-" + otp_type)
        )
        assert "/account/reset-2fa-" + otp_type in reset_form.get_attribute("action")
        reset_button = self.driver.find_elements_by_css_selector(
            "#button-reset-two-factor-" + otp_type)[0]

        # 2FA reset buttons show a tooltip with explanatory text on hover.
        # Also, confirm the text on the tooltip is the correct one.
        reset_button.location_once_scrolled_into_view
        ActionChains(self.driver).move_to_element(reset_button).perform()

        def explanatory_tooltip_is_correct():
            explanatory_tooltip = self.driver.find_element_by_css_selector(
                "#button-reset-two-factor-" + otp_type + " span"
            )

            explanatory_tooltip_opacity = explanatory_tooltip.value_of_css_property("opacity")
            assert explanatory_tooltip_opacity == "1"

            if not self.accept_languages:
                assert explanatory_tooltip.text == tooltip_text

        self.wait_for(explanatory_tooltip_is_correct)

        reset_form.submit()

        alert = self.driver.switch_to_alert()
        alert.accept()

    def _set_hotp_secret(self):
        self.safe_send_keys_by_css_selector('input[name="otp_secret"]', "123456")
        self.safe_click_by_css_selector("button[type=submit]")

    def _visit_edit_hotp_secret(self):
        self._visit_edit_secret(
            "hotp",
            "Reset two-factor authentication for security keys, like a YubiKey")

    def _visit_edit_totp_secret(self):
        self._visit_edit_secret(
            "totp",
            "Reset two-factor authentication for mobile apps, such as FreeOTP"
        )

    def _admin_visits_add_user(self):
        add_user_btn = self.driver.find_element_by_id("add-user")
        self.wait_for(lambda: add_user_btn.is_enabled() and add_user_btn.is_displayed())
        add_user_btn.click()

        self.wait_for(lambda: self.driver.find_element_by_id("username"))

    def _admin_visits_edit_user(self):
        selector = 'a.edit-user[data-username="{}"]'.format(self.new_user["username"])
        new_user_edit_links = self.driver.find_elements_by_css_selector(selector)
        assert len(new_user_edit_links) == 1
        self.safe_click_by_css_selector(selector)
        try:
            self.wait_for(lambda: self.driver.find_element_by_id("new-password"))
        except NoSuchElementException:
            # try once more
            self.safe_click_by_css_selector(selector)
            self.wait_for(lambda: self.driver.find_element_by_id("new-password"))

    def retry_2fa_pop_ups(self, navigation_step, button_to_click):
        """Clicking on Selenium alerts can be flaky. We need to retry them if they timeout."""

        for i in range(CLICK_ATTEMPTS):
            try:
                try:
                    # This is the button we click to trigger the alert.
                    self.wait_for(lambda: self.driver.find_elements_by_id(
                        button_to_click)[0])
                except IndexError:
                    # If the button isn't there, then the alert is up from the last
                    # time we attempted to run this test. Switch to it and accept it.
                    self.alert_wait()
                    self.alert_accept()
                    break

                # The alert isn't up. Run the rest of the logic.
                navigation_step()

                self.alert_wait()
                self.alert_accept()
                break
            except TimeoutException:
                # Selenium has failed to click, and the confirmation
                # alert didn't happen. We'll try again.
                logging.info("Selenium has failed to click; retrying.")

    def _admin_visits_reset_2fa_hotp(self):
        def _admin_visits_reset_2fa_hotp_step():
            # 2FA reset buttons show a tooltip with explanatory text on hover.
            # Also, confirm the text on the tooltip is the correct one.
            hotp_reset_button = self.driver.find_elements_by_id(
                "reset-two-factor-hotp")[0]
            hotp_reset_button.location_once_scrolled_into_view
            ActionChains(self.driver).move_to_element(hotp_reset_button).perform()

            time.sleep(1)

            tip_opacity = self.driver.find_elements_by_css_selector(
                "#button-reset-two-factor-hotp span.tooltip")[0].value_of_css_property('opacity')
            tip_text = self.driver.find_elements_by_css_selector(
                "#button-reset-two-factor-hotp span.tooltip")[0].text

            assert tip_opacity == "1"

            if not self.accept_languages:
                assert (
                    tip_text == "Reset two-factor authentication for security keys, like a YubiKey"
                )

            self.safe_click_by_id("button-reset-two-factor-hotp")

        # Run the above step in a retry loop
        self.retry_2fa_pop_ups(_admin_visits_reset_2fa_hotp_step, "reset-two-factor-hotp")

    def _admin_visits_edit_hotp(self):
        self.wait_for(lambda: self.driver.find_element_by_css_selector('input[name="otp_secret"]'))

    def _admin_visits_reset_2fa_totp(self):
        def _admin_visits_reset_2fa_totp_step():
            totp_reset_button = self.driver.find_elements_by_id("reset-two-factor-totp")[0]
            assert "/admin/reset-2fa-totp" in totp_reset_button.get_attribute("action")
            # 2FA reset buttons show a tooltip with explanatory text on hover.
            # Also, confirm the text on the tooltip is the correct one.
            totp_reset_button = self.driver.find_elements_by_css_selector(
                "#button-reset-two-factor-totp")[0]
            totp_reset_button.location_once_scrolled_into_view
            ActionChains(self.driver).move_to_element(totp_reset_button).perform()

            time.sleep(1)

            tip_opacity = self.driver.find_elements_by_css_selector(
                "#button-reset-two-factor-totp span.tooltip")[0].value_of_css_property('opacity')
            tip_text = self.driver.find_elements_by_css_selector(
                "#button-reset-two-factor-totp span.tooltip")[0].text

            assert tip_opacity == "1"
            if not self.accept_languages:
                expected_text = (
                    "Reset two-factor authentication for mobile apps, such as FreeOTP"
                )
                assert tip_text == expected_text

            self.safe_click_by_id("button-reset-two-factor-totp")

        # Run the above step in a retry loop
        self.retry_2fa_pop_ups(_admin_visits_reset_2fa_totp_step, "reset-two-factor-totp")

    def _admin_creates_a_user(self, hotp):
        self.safe_click_by_id("add-user")
        self.wait_for(lambda: self.driver.find_element_by_id("username"))
        self.new_user = dict(username="dellsberg",
                             first_name='',
                             last_name='',
                             password="pentagonpapers")
        self._add_user(self.new_user["username"],
                       first_name=self.new_user['first_name'],
                       last_name=self.new_user['last_name'],
                       is_admin=False,
                       hotp=hotp)

    def _journalist_delete_all(self):
        for checkbox in self.driver.find_elements_by_name("doc_names_selected"):
            checkbox.click()

        delete_selected_link = self.driver.find_element_by_id("delete-selected-link")
        ActionChains(self.driver).move_to_element(delete_selected_link).click().perform()

    def _journalist_confirm_delete_selected(self):
        self.wait_for(
            lambda: expected_conditions.element_to_be_clickable((By.ID, "delete-selected"))
        )
        confirm_btn = self.driver.find_element_by_id("delete-selected")
        confirm_btn.location_once_scrolled_into_view
        ActionChains(self.driver).move_to_element(confirm_btn).click().perform()

    def _source_delete_key(self):
        filesystem_id = _SourceScryptManager.get_default().derive_source_filesystem_id(
            self.source_name
        )
        EncryptionManager.get_default().delete_source_key_pair(filesystem_id)

    def _journalist_continues_after_flagging(self):
        self.wait_for(lambda: self.driver.find_element_by_id("continue-to-list"))
        continue_link = self.driver.find_element_by_id("continue-to-list")

        actions = ActionChains(self.driver)
        actions.move_to_element(continue_link).perform()
        continue_link.click()

    def _journalist_delete_none(self):
        self.driver.find_element_by_id("delete-selected-link").click()

    def _journalist_delete_all_confirmation(self):
        self.safe_click_all_by_css_selector("[name=doc_names_selected]")
        self.safe_click_by_css_selector("a#delete-selected-link")

    def _journalist_delete_one(self):
        self.safe_click_by_css_selector("[name=doc_names_selected]")

        el = WebDriverWait(self.driver, self.timeout, self.poll_frequency).until(
            expected_conditions.element_to_be_clickable((By.ID, "delete-selected-link"))
        )
        el.location_once_scrolled_into_view
        ActionChains(self.driver).move_to_element(el).click().perform()

    def _journalist_visits_admin(self):
        self.driver.get(self.journalist_location + "/admin")

    def _journalist_fail_login(self):
        self._try_login_user("root", "worse", "mocked")

    def _journalist_fail_login_many(self):
        self.user = ""
        for _ in range(5 + 1):
            self._try_login_user(self.user, "worse", "mocked")

    def _admin_enters_journalist_account_details_hotp(self, username, hotp_secret):
        self.safe_send_keys_by_css_selector('input[name="username"]', username)
        self.safe_send_keys_by_css_selector('input[name="otp_secret"]', hotp_secret)
        self.safe_click_by_css_selector('input[name="is_hotp"]')
