import tempfile

class SourceNavigationSteps():

    def _source_visits_source_homepage(self):
        self.driver.get(self.source_location)

        self.assertEqual("SecureDrop | Protecting Journalists and Sources", self.driver.title)

    def _source_chooses_to_submit_documents(self):
        self.driver.find_element_by_id('submit-documents-button').click()

        codename = self.driver.find_element_by_css_selector('#codename')

        self.assertTrue(len(codename.text) > 0)
        self.source_name = codename.text

    def _source_continues_to_submit_page(self):
        continue_button = self.driver.find_element_by_id('continue-button')

        continue_button.click()
        headline = self.driver.find_element_by_class_name('headline')
        self.assertEqual('Submit documents and messages', headline.text)

    def _source_submits_a_file(self):
        with tempfile.NamedTemporaryFile() as file:
            file.write(self.secret_message)
            file.seek(0)

            filename = file.name
            filebasename = filename.split('/')[-1]

            file_upload_box = self.driver.find_element_by_css_selector('[name=fh]')
            file_upload_box.send_keys(filename)

            submit_button = self.driver.find_element_by_css_selector(
                'button[type=submit]')
            submit_button.click()

            notification = self.driver.find_element_by_css_selector( 'p.notification')
            expected_notification = 'Thanks! We received your document "%s".' % filebasename
            self.assertIn(expected_notification, notification.text)

    def _source_submits_a_message(self):
        text_box = self.driver.find_element_by_css_selector('[name=msg]')

        text_box.send_keys(self.secret_message) # send_keys = type into text box
        submit_button = self.driver.find_element_by_css_selector(
            'button[type=submit]')
        submit_button.click()

        notification = self.driver.find_element_by_css_selector( 'p.notification')
        self.assertIn('Thanks! We received your message.', notification.text)
