import unittest
import source_navigation_steps
import journalist_navigation_steps
import functional_test
import tempfile

class SubmitAndRetrieveFile(
        unittest.TestCase,
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationSteps,
        journalist_navigation_steps.JournalistNavigationSteps
        ):

    def setUp(self):
        functional_test.FunctionalTest.setUp(self)

    def tearDown(self):
        functional_test.FunctionalTest.tearDown(self)

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
            expected_notification = "Thanks! We received your document '%s'." % filebasename
            self.assertEquals(expected_notification, notification.text)


    def test_submit_and_retrieve_happy_path(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._journalist_checks_messages()
        self._journalist_downloads_message()
