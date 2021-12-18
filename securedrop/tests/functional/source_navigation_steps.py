import tempfile
import time

import pytest
from selenium.common.exceptions import NoSuchElementException


class SourceNavigationStepsMixin:
    def _is_on_source_homepage(self):
        return self.wait_for(lambda: self.driver.find_element_by_id("source-index"))

    def _is_logged_in(self):
        return self.wait_for(lambda: self.driver.find_element_by_id("logout"))

    def _is_on_lookup_page(self):
        return self.wait_for(lambda: self.driver.find_element_by_id("upload"))

    def _is_on_generate_page(self):
        return self.wait_for(lambda: self.driver.find_element_by_id("create-form"))

    def _is_on_logout_page(self):
        return self.wait_for(lambda: self.driver.find_element_by_id("click-new-identity-tor"))

    def _source_sees_orgname(self, name="SecureDrop"):
        assert name in self.driver.title

    def _source_visits_source_homepage(self):
        self.driver.get(self.source_location)
        assert self._is_on_source_homepage()

    def _source_clicks_submit_documents_on_homepage(self, assert_success=True):

        # It's the source's first time visiting this SecureDrop site, so they
        # choose to "Submit Documents".
        self.safe_click_by_id("submit-documents-button")

        if assert_success:
            # The source should now be on the page where they are presented with
            # a diceware codename they can use for subsequent logins
            assert self._is_on_generate_page()

    def _source_regenerates_codename(self):
        self._source_visits_source_homepage()
        # We do not want to assert success here since it's possible they got
        # redirected if already logged in.
        self._source_clicks_submit_documents_on_homepage(assert_success=False)

    def _source_chooses_to_submit_documents(self):
        self._source_clicks_submit_documents_on_homepage()

        codename = self.driver.find_element_by_css_selector("#codename")

        assert len(codename.text) > 0
        self.source_name = codename.text

    def _source_shows_codename(self, verify_source_name=True):
        # The DETAILS element will be missing the OPEN attribute if it is
        # closed, hiding its contents.
        content = self.driver.find_element_by_css_selector("details#codename-hint")
        assert content.get_attribute("open") is None

        self.safe_click_by_id("codename-hint")

        assert content.get_attribute("open") is not None
        content_content = self.driver.find_element_by_css_selector("details#codename-hint mark")
        if verify_source_name:
            assert content_content.text == self.source_name

    def _source_hides_codename(self):
        # The DETAILS element will have the OPEN attribute if it is open,
        # displaying its contents.
        content = self.driver.find_element_by_css_selector("details#codename-hint")
        assert content.get_attribute("open") is not None

        self.safe_click_by_id("codename-hint")

        assert content.get_attribute("open") is None

    def _source_sees_no_codename(self):
        codename = self.driver.find_elements_by_css_selector(".code-reminder")
        assert len(codename) == 0

    def _source_chooses_to_login(self):
        self.driver.find_element_by_id("login-button").click()

        self.wait_for(lambda: self.driver.find_elements_by_id("login-with-existing-codename"))

    def _source_hits_cancel_at_login_page(self):
        self.driver.find_element_by_id("cancel").click()

        self.driver.get(self.source_location)

        assert self._is_on_source_homepage()

    def _source_proceeds_to_login(self):
        self.safe_send_keys_by_id("login-with-existing-codename", self.source_name)
        self.safe_click_by_id("login")

        # Check that we've logged in
        assert self._is_logged_in()

        replies = self.driver.find_elements_by_id("replies")
        assert len(replies) == 1

    def _source_enters_codename_in_login_form(self):
        self.safe_send_keys_by_id(
            "login-with-existing-codename", "ascension hypertext concert synopses"
        )

    def _source_hits_cancel_at_submit_page(self):
        self.driver.find_element_by_id("cancel").click()

        if not self.accept_languages:
            headline = self.driver.find_element_by_class_name("headline")
            assert "Submit Files or Messages" == headline.text

    def _source_continues_to_submit_page(self, files_allowed=True):
        self.safe_click_by_id("continue-button")

        def submit_page_loaded():
            if not self.accept_languages:
                headline = self.driver.find_element_by_class_name("headline")
                if files_allowed:
                    assert "Submit Files or Messages" == headline.text
                else:
                    assert "Submit Messages" == headline.text

        self.wait_for(submit_page_loaded)

    def _source_continues_to_submit_page_with_colliding_journalist_designation(self):
        self.safe_click_by_id("continue-button")

        self.wait_for(lambda: self.driver.find_element_by_css_selector(".error"))
        flash_error = self.driver.find_element_by_css_selector(".error")
        assert "There was a temporary problem creating your account. Please try again." \
               == flash_error.text

    def _source_submits_a_file(self):
        with tempfile.NamedTemporaryFile() as file:
            file.write(self.secret_message.encode("utf-8"))
            file.seek(0)

            filename = file.name

            self.safe_send_keys_by_css_selector("[name=fh]", filename)

            self.safe_click_by_id("submit-doc-button")
            self.wait_for_source_key(self.source_name)

            def file_submitted():
                if not self.accept_languages:
                    notification = self.driver.find_element_by_css_selector(".success")
                    expected_notification = "Thank you for sending this information to us"
                    assert expected_notification in notification.text

            # Allow extra time for file uploads
            self.wait_for(file_submitted, timeout=(self.timeout * 3))

            # allow time for reply key to be generated
            time.sleep(self.timeout)

    def _source_submits_a_message(
        self, verify_notification=False, first_submission=False, first_login=False
    ):
        self._source_enters_text_in_message_field()
        self._source_clicks_submit_button_on_submission_page()

        def message_submitted():
            if not self.accept_languages:
                notification = self.driver.find_element_by_css_selector(".success")
                assert "Thank" in notification.text

                if verify_notification:
                    first_submission_text = (
                        "Please check back later for replies." in notification.text
                    )
                    first_login_text = "Forgot your codename?" in notification.text

                    if first_submission:
                        assert first_submission_text

                        if first_login:
                            assert first_login_text
                        else:
                            assert not first_login_text
                    else:
                        assert not first_submission_text

        self.wait_for(message_submitted)

        # allow time for reply key to be generated
        time.sleep(self.timeout)

    def _source_enters_text_in_message_field(self):
        self.safe_send_keys_by_css_selector("[name=msg]", self.secret_message)

    def _source_clicks_submit_button_on_submission_page(self):
        submit_button = self.driver.find_element_by_id("submit-doc-button")
        submit_button.click()

    def _source_deletes_a_journalist_reply(self):
        # Get the reply filename so we can use IDs to select the delete buttons
        reply_filename_element = self.driver.find_element_by_name("reply_filename")
        reply_filename = reply_filename_element.get_attribute("value")

        delete_button_id = "delete-reply-{}".format(reply_filename)
        delete_button = self.driver.find_element_by_id(delete_button_id)
        delete_button.click()

        def confirm_displayed():
            confirm_button_id = "confirm-delete-reply-button-{}".format(reply_filename)
            confirm_button = self.driver.find_element_by_id(confirm_button_id)
            confirm_button.location_once_scrolled_into_view
            assert confirm_button.is_displayed()

        self.wait_for(confirm_displayed)

        confirm_button_id = "confirm-delete-reply-button-{}".format(reply_filename)
        confirm_button = self.driver.find_element_by_id(confirm_button_id)
        confirm_button.click()

        def reply_deleted():
            if not self.accept_languages:
                notification = self.driver.find_element_by_class_name("notification")
                assert "Reply deleted" in notification.text

        self.wait_for(reply_deleted)

    def _source_logs_out(self):
        self.safe_click_by_id("logout")
        assert self._is_on_logout_page()

    def _source_not_found(self):
        self.driver.get(self.source_location + "/unlikely")
        message = self.driver.find_element_by_id("page-not-found")
        assert message.is_displayed()

    def _source_visits_use_tor(self):
        self.driver.get(self.source_location + "/use-tor")

    def _source_tor2web_warning(self):
        self.driver.get(self.source_location + "/tor2web-warning")

    def _source_why_journalist_key(self):
        self.driver.get(self.source_location + "/why-public-key")

    def _source_waits_for_session_to_timeout(self):
        time.sleep(self.session_expiration + 2)

    def _source_sees_session_timeout_message(self):
        notification = self.driver.find_element_by_css_selector(".important")

        if not self.accept_languages:
            expected_text = "You were logged out due to inactivity."
            assert expected_text in notification.text

    def _source_sees_document_attachment_item(self):
        assert self.driver.find_element_by_class_name("attachment") is not None

    def _source_does_not_sees_document_attachment_item(self):
        with pytest.raises(NoSuchElementException):
            self.driver.find_element_by_class_name("attachment")

    def _source_sees_already_logged_in_in_other_tab_message(self):
        notification = self.driver.find_element_by_css_selector(".notification")

        if not self.accept_languages:
            expected_text = "You are already logged in."
            assert expected_text in notification.text

    def _source_sees_redirect_already_logged_in_message(self):
        notification = self.driver.find_element_by_css_selector(".notification")

        if not self.accept_languages:
            expected_text = "You were redirected because you are already logged in."
            assert expected_text in notification.text
