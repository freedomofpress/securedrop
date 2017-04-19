import tempfile

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By


class SourceNavigationSteps():

    def _source_visits_source_homepage(self):
        self.driver.get(self.source_location)
        expected_title = "SecureDrop | Protecting Journalists and Sources"
        self.assertEqual(expected_title, self.driver.title)

    def _source_chooses_to_submit_documents(self):
        # First move the cursor to a known position in case it happens to
        # be hovering over one of the buttons we are testing below.
        header_image = self.driver.find_element_by_id('header')
        ActionChains(self.driver).move_to_element(header_image).perform()

        # It's the source's first time visiting this SecureDrop site, so they
        # choose to "Submit Documents".
        submit_button = self.driver.find_element_by_id('submit-documents-button')

        submit_button_icon = self.driver.find_element_by_css_selector(
            'a#submit-documents-button > img.off-hover')
        self.assertTrue(submit_button_icon.is_displayed())

        # The source hovers their cursor over the button, and the visual style
        # of the button changes to encourage them to click it.
        ActionChains(self.driver).move_to_element(submit_button).perform()

        ## Let's make sure toggling the icon image with the hover state is working.
        self.assertFalse(submit_button_icon.is_displayed())
        submit_button_hover_icon = self.driver.find_element_by_css_selector(
            'a#submit-documents-button > img.on-hover')
        self.assertTrue(submit_button_hover_icon.is_displayed())

        # The source clicks the submit button.
        submit_button.click()

        codename = self.driver.find_element_by_css_selector('#codename')

        self.assertTrue(len(codename.text) > 0)
        self.source_name = codename.text

    def _source_chooses_to_login(self):
        self.driver.find_element_by_id('login-button').click()

        logins = self.driver.find_elements_by_id('login-with-existing-codename')

        self.assertTrue(len(logins) > 0)

    def _source_hits_cancel_at_login_page(self):
        self.driver.find_element_by_id('cancel').click()

        self.driver.get(self.source_location)

        self.assertEqual("SecureDrop | Protecting Journalists and Sources",
                         self.driver.title)

    def _source_hits_cancel_at_submit_page(self):
        self.driver.find_element_by_id('cancel').click()

        headline = self.driver.find_element_by_class_name('headline')
        self.assertEqual('Submit Materials', headline.text)

    def _source_continues_to_submit_page(self):
        continue_button = self.driver.find_element_by_id('continue-button')

        continue_button_icon = self.driver.find_element_by_css_selector(
            'button#continue-button > img.off-hover')
        self.assertTrue(continue_button_icon.is_displayed())

        ## Hover over the continue button test toggle the icon images with the
        ## hover state.
        ActionChains(self.driver).move_to_element(continue_button).perform()
        self.assertFalse(continue_button_icon.is_displayed())

        continue_button_hover_icon = self.driver.find_element_by_css_selector(
            'button#continue-button img.on-hover'
        )
        self.assertTrue(continue_button_hover_icon.is_displayed())

        continue_button.click()

        headline = self.driver.find_element_by_class_name('headline')
        self.assertEqual('Submit Materials', headline.text)

    def _source_submits_a_file(self):
        with tempfile.NamedTemporaryFile() as file:
            file.write(self.secret_message)
            file.seek(0)

            filename = file.name
            filebasename = filename.split('/')[-1]

            file_upload_box = self.driver.find_element_by_css_selector(
                '[name=fh]')
            file_upload_box.send_keys(filename)

            submit_button = self.driver.find_element_by_id('submit-doc-button')
            ActionChains(self.driver).move_to_element(submit_button).perform()

            toggled_submit_button_icon = self.driver.find_element_by_css_selector(
                'button#submit-doc-button img.on-hover'
            )
            self.assertTrue(toggled_submit_button_icon.is_displayed())

            submit_button.click()

            notification = self.driver.find_element_by_css_selector(
                '.success')
            expected_notification = 'Thank you for sending this information to us'
            self.assertIn(expected_notification, notification.text)

    def _source_submits_a_message(self):
        text_box = self.driver.find_element_by_css_selector('[name=msg]')
        text_box.send_keys(self.secret_message)  # send_keys = type into text box

        submit_button = self.driver.find_element_by_id('submit-doc-button')
        submit_button.click()

        notification = self.driver.find_element_by_css_selector(
            '.success')
        self.assertIn('Thank you for sending this information to us',
                      notification.text)

    def _source_logs_out(self):
        logout_button = self.driver.find_element_by_id('logout').click()
        notification = self.driver.find_element_by_css_selector('.important')
        self.assertIn('Thank you for exiting your session!', notification.text)
