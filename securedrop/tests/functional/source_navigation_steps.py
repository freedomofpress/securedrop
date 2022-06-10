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
        return self.wait_for(lambda: self.driver.find_element_by_id("source-lookup"))

    def _is_on_logout_page(self):
        return self.wait_for(lambda: self.driver.find_element_by_id("source-logout"))

    def _source_sees_orgname(self, name="SecureDrop"):
        assert name in self.driver.title

    def _source_visits_source_homepage(self):
        self.driver.get(self.source_location)
        assert self._is_on_source_homepage()

    def _source_clicks_submit_documents_on_homepage(self, assert_success=True):

        # It's the source's first time visiting this SecureDrop site, so they
        # choose to "Submit Documents".
        self.safe_click_by_css_selector("#started-form button")

        if assert_success:
            # The source should now be on the lookup page - codename is not
            # yet visible
            assert self._is_on_lookup_page()

    def _source_regenerates_codename(self):
        self._source_visits_source_homepage()
        # We do not want to assert success here since it's possible they got
        # redirected if already logged in.
        self._source_clicks_submit_documents_on_homepage(assert_success=False)

    def _source_chooses_to_submit_documents(self):
        self._source_clicks_submit_documents_on_homepage()
        submit_header = self.driver.find_element_by_css_selector("#welcome-heading")
        assert len(submit_header.text) > 0

    def _source_shows_codename(self, verify_source_name=True):
        # We use inputs to change CSS states for subsequent elements in the DOM, if it is unchecked
        # the codename is hidden
        content = self.driver.find_element_by_id("codename-show-checkbox")
        assert content.get_attribute("checked") is None

        # In the UI, the label is actually the element that is being clicked, altering the state
        # of the input
        self.safe_click_by_id("codename-show")

        assert content.get_attribute("checked") is not None
        content_content = self.driver.find_element_by_css_selector("#codename span")
        if verify_source_name:
            assert content_content.text == self.source_name

    def _source_hides_codename(self):
        # We use inputs to change CSS states for subsequent elements in the DOM, if it is checked
        # the codename is visible
        content = self.driver.find_element_by_id("codename-show-checkbox")
        assert content.get_attribute("checked") is not None

        # In the UI, the label is actually the element that is being clicked, altering the state
        # of the input
        self.safe_click_by_id("codename-show")

        assert content.get_attribute("checked") is None

    def _source_sees_no_codename(self):
        codename = self.driver.find_elements_by_css_selector("#codename span")
        assert len(codename) == 0

    def _source_chooses_to_login(self):
        self.safe_click_by_css_selector("#return-visit a")

        self.wait_for(lambda: self.driver.find_elements_by_id("source-login"))

    def _source_hits_cancel_at_login_page(self):
        self.safe_click_by_css_selector(".form-controls a")

        self.driver.get(self.source_location)

        assert self._is_on_source_homepage()

    def _source_proceeds_to_login(self):
        self.safe_send_keys_by_id("passphrase", self.source_name)
        self.safe_click_by_css_selector(".form-controls button")

        # Check that we've logged in
        assert self._is_logged_in()

        replies = self.driver.find_elements_by_id("replies")
        assert len(replies) == 1

    def _source_enters_codename_in_login_form(self):
        self.safe_send_keys_by_id(
            "codename", "ascension hypertext concert synopses"
        )

    def _source_hits_cancel_at_submit_page(self):
        self.safe_click_by_css_selector(".form-controls a")

        if not self.accept_languages:
            heading = self.driver.find_element_by_id("welcome-heading")
            assert "Welcome!" == heading.text

    def _source_continues_to_submit_page(self, files_allowed=True):
        def submit_page_loaded():
            def uploader_is_visible():
                try:
                    self.driver.find_element_by_class_name("attachment")
                except NoSuchElementException:
                    return False
                return True

            if not self.accept_languages:
                if files_allowed:
                    assert uploader_is_visible()
                else:
                    assert not uploader_is_visible()

    def _source_submits_a_file(self, first_submission=False):
        with tempfile.NamedTemporaryFile() as file:
            file.write(self.secret_message.encode("utf-8"))
            file.seek(0)

            filename = file.name

            self.safe_send_keys_by_id("fh", filename)

            self.safe_click_by_css_selector(".form-controls button")

            def file_submitted(first_submission=False):
                if not self.accept_languages:
                    notification = self.driver.find_element_by_class_name("success")
                    if first_submission:
                        expected_notification = "Please check back later for replies."
                    else:
                        expected_notification = "Success!\nThanks! We received your document."
                    assert expected_notification in notification.text

            # Allow extra time for file uploads
            self.wait_for(lambda: file_submitted(first_submission), timeout=(self.timeout * 3))

            if first_submission:
                codename = self.driver.find_element_by_css_selector("#codename span")
                self.source_name = codename.text

    def _source_submits_a_message(
        self, verify_notification=False, first_submission=False, first_login=False
    ):
        self._source_enters_text_in_message_field()
        self.safe_click_by_css_selector(".form-controls button")

        def message_submitted():
            if not self.accept_languages:
                notification = self.driver.find_element_by_class_name("success")
                assert "Thank" in notification.text

                if first_submission:
                    codename = self.driver.find_element_by_css_selector("#codename span")
                    self.source_name = codename.text

                if verify_notification:
                    first_submission_text = (
                        "Please check back later for replies." in notification.text
                    )

                    if first_submission:
                        assert first_submission_text
                    else:
                        assert not first_submission_text

        self.wait_for(message_submitted)

        # allow time for reply key to be generated
        time.sleep(self.timeout)

    def _source_enters_text_in_message_field(self):
        self.safe_send_keys_by_id("msg", self.secret_message)

    def _source_deletes_a_journalist_reply(self):
        # Get the reply filename so we can use IDs to select the delete buttons
        reply_filename_element = self.driver.find_element_by_name("reply_filename")
        reply_filename = reply_filename_element.get_attribute("value")

        confirm_dialog_id = "confirm-delete-{}".format(reply_filename)
        self.safe_click_by_css_selector("a[href='#{}']".format(confirm_dialog_id))

        def confirm_displayed():
            confirm_dialog = self.driver.find_element_by_id(confirm_dialog_id)
            confirm_dialog.location_once_scrolled_into_view
            assert confirm_dialog.is_displayed()

        self.wait_for(confirm_displayed)
        # Due to the . in the filename (which is used as ID), we need to escape it because otherwise
        # we'd select the class gpg
        self.safe_click_by_css_selector("#{} button".format(confirm_dialog_id.replace(".", "\\.")))

        def reply_deleted():
            if not self.accept_languages:
                notification = self.driver.find_element_by_class_name("success")
                assert "Reply deleted" in notification.text

        self.wait_for(reply_deleted)

    def _source_logs_out(self):
        self.safe_click_by_id("logout")
        assert self._is_on_logout_page()

    def _source_sees_document_attachment_item(self):
        assert self.driver.find_element_by_class_name("attachment") is not None

    def _source_does_not_sees_document_attachment_item(self):
        with pytest.raises(NoSuchElementException):
            self.driver.find_element_by_class_name("attachment")

    def _source_sees_already_logged_in_in_other_tab_message(self):
        notification = self.driver.find_element_by_class_name("notification")

        if not self.accept_languages:
            expected_text = "You are already logged in."
            assert expected_text in notification.text

    def _source_sees_redirect_already_logged_in_message(self):
        notification = self.driver.find_element_by_class_name("notification")

        if not self.accept_languages:
            expected_text = "You were redirected because you are already logged in."
            assert expected_text in notification.text
