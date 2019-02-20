import tempfile
import time

from selenium.webdriver.common.action_chains import ActionChains


class SourceNavigationStepsMixin():

    def _source_visits_source_homepage(self):
        self.driver.get(self.source_location)

        if not hasattr(self, 'accept_languages'):
            assert ("SecureDrop | Protecting Journalists and Sources" ==
                    self.driver.title)

    def _source_clicks_submit_documents_on_homepage(self):
        # First move the cursor to a known position in case it happens to
        # be hovering over one of the buttons we are testing below.
        header_image = self.driver.find_element_by_css_selector('.header')
        ActionChains(self.driver).move_to_element(header_image).perform()

        # It's the source's first time visiting this SecureDrop site, so they
        # choose to "Submit Documents".
        submit_button = self.driver.find_element_by_id(
            'submit-documents-button')

        submit_button_icon = self.driver.find_element_by_css_selector(
            'a#submit-documents-button > img.off-hover')
        assert submit_button_icon.is_displayed()

        # The source hovers their cursor over the button, and the visual style
        # of the button changes to encourage them to click it.
        ActionChains(self.driver).move_to_element(submit_button).perform()

        # Let's make sure toggling the icon image with the hover state
        # is working.
        assert submit_button_icon.is_displayed() is False
        submit_button_hover_icon = self.driver.find_element_by_css_selector(
            'a#submit-documents-button > img.on-hover')
        assert submit_button_hover_icon.is_displayed()

        # The source clicks the submit button.
        submit_button.click()

    def _source_chooses_to_submit_documents(self):
        self._source_clicks_submit_documents_on_homepage()

        codename = self.driver.find_element_by_css_selector('#codename')

        assert len(codename.text) > 0
        self.source_name = codename.text

    def _source_shows_codename(self):
        content = self.driver.find_element_by_id('codename-hint-content')
        assert not content.is_displayed()
        self.driver.find_element_by_id('codename-hint-show').click()
        assert content.is_displayed()
        content_content = self.driver.find_element_by_css_selector(
                '#codename-hint-content p')
        assert content_content.text == self.source_name

    def _source_hides_codename(self):
        content = self.driver.find_element_by_id('codename-hint-content')
        assert content.is_displayed()
        self.driver.find_element_by_id('codename-hint-hide').click()
        assert not content.is_displayed()

    def _source_sees_no_codename(self):
        codename = self.driver.find_elements_by_css_selector('.code-reminder')
        assert len(codename) == 0

    def _source_chooses_to_login(self):
        self.driver.find_element_by_id('login-button').click()

        logins = self.driver.find_elements_by_id(
            'login-with-existing-codename')

        assert len(logins) > 0

    def _source_hits_cancel_at_login_page(self):
        self.driver.find_element_by_id('cancel').click()

        self.driver.get(self.source_location)

        if not hasattr(self, 'accept_languages'):
            assert ("SecureDrop | Protecting Journalists and Sources" ==
                    self.driver.title)

    def _source_proceeds_to_login(self):
        codename_input = self.driver.find_element_by_id(
            'login-with-existing-codename')
        codename_input.send_keys(self.source_name)

        continue_button = self.driver.find_element_by_id('login')
        continue_button.click()

        if not hasattr(self, 'accept_languages'):
            assert ("SecureDrop | Protecting Journalists and Sources" ==
                    self.driver.title)
        # Check that we've logged in

        replies = self.driver.find_elements_by_id("replies")
        assert len(replies) == 1

    def _source_enters_codename_in_login_form(self):
        codename_input = self.driver.find_element_by_id(
            'login-with-existing-codename')
        codename_input.send_keys('ascension hypertext concert synopses')

    def _source_hits_cancel_at_submit_page(self):
        self.driver.find_element_by_id('cancel').click()

        if not hasattr(self, 'accept_languages'):
            headline = self.driver.find_element_by_class_name('headline')
            assert 'Submit Files or Messages' == headline.text

    def _source_continues_to_submit_page(self):
        continue_button = self.driver.find_element_by_id('continue-button')

        continue_button_icon = self.driver.find_element_by_css_selector(
            'button#continue-button > img.off-hover')
        assert continue_button_icon.is_displayed()

        # Hover over the continue button test toggle the icon images
        # with the hover state.
        ActionChains(self.driver).move_to_element(continue_button).perform()
        assert continue_button_icon.is_displayed() is False

        continue_button_hover_icon = self.driver.find_element_by_css_selector(
            'button#continue-button img.on-hover'
        )
        assert continue_button_hover_icon.is_displayed()

        continue_button.click()

        if not hasattr(self, 'accept_languages'):
            headline = self.driver.find_element_by_class_name('headline')
            assert 'Submit Files or Messages' == headline.text

    def _source_submits_a_file(self):
        with tempfile.NamedTemporaryFile() as file:
            file.write(self.secret_message)
            file.seek(0)

            filename = file.name

            file_upload_box = self.driver.find_element_by_css_selector(
                '[name=fh]')
            file_upload_box.send_keys(filename)

            submit_button = self.driver.find_element_by_id('submit-doc-button')
            ActionChains(self.driver).move_to_element(submit_button).perform()

            toggled_submit_button_icon = (
                self.driver.find_element_by_css_selector(
                    'button#submit-doc-button img.on-hover'))
            assert toggled_submit_button_icon.is_displayed()

            submit_button.click()
            self.wait_for_source_key(self.source_name)

            if not hasattr(self, 'accept_languages'):
                notification = self.driver.find_element_by_css_selector(
                    '.success')
                expected_notification = (
                    'Thank you for sending this information to us')
                assert expected_notification in notification.text

    def _source_submits_a_message(self):
        self._source_enters_text_in_message_field()
        self._source_clicks_submit_button_on_submission_page()

        if not hasattr(self, 'accept_languages'):
            notification = self.driver.find_element_by_css_selector(
                '.success')
            assert 'Thank' in notification.text

    def _source_enters_text_in_message_field(self):
        text_box = self.driver.find_element_by_css_selector('[name=msg]')
        text_box.send_keys(self.secret_message)

    def _source_clicks_submit_button_on_submission_page(self):
        submit_button = self.driver.find_element_by_id('submit-doc-button')
        submit_button.click()
        self.wait_for_source_key(self.source_name)

    def _source_deletes_a_journalist_reply(self):
        # Get the reply filename so we can use IDs to select the delete buttons
        reply_filename_element = self.driver.find_element_by_name(
            'reply_filename')
        reply_filename = reply_filename_element.get_attribute('value')

        delete_button_id = 'delete-reply-{}'.format(reply_filename)
        delete_button = self.driver.find_element_by_id(delete_button_id)
        delete_button.click()

        confirm_button_id = 'confirm-delete-reply-button-{}'.format(
            reply_filename)
        confirm_button = self.driver.find_element_by_id(confirm_button_id)
        assert confirm_button.is_displayed()
        confirm_button.click()

        if not hasattr(self, 'accept_languages'):
            notification = self.driver.find_element_by_class_name(
                'notification')
            assert 'Reply deleted' in notification.text

    def _source_logs_out(self):
        self.driver.find_element_by_id('logout').click()
        assert self.driver.find_element_by_css_selector('.important')

    def _source_not_found(self):
        self.driver.get(self.source_location + "/unlikely")
        message = self.driver.find_element_by_id('page-not-found')
        assert message.is_displayed()

    def _source_visits_use_tor(self):
        self.driver.get(self.source_location + "/use-tor")

    def _source_tor2web_warning(self):
        self.driver.get(self.source_location + "/tor2web-warning")

    def _source_why_journalist_key(self):
        self.driver.get(self.source_location + "/why-journalist-key")

    def _source_disable_noscript_xss(self):
        self.driver.get(self.source_location + "/disable-noscript-xss")

    def _source_waits_for_session_to_timeout(self, session_length_minutes):
        time.sleep(session_length_minutes * 60 + 0.1)

    def _source_sees_session_timeout_message(self):
        notification = self.driver.find_element_by_css_selector('.important')

        if not hasattr(self, 'accept_languages'):
            expected_text = 'Your session timed out due to inactivity.'
            assert expected_text in notification.text
