
class SourceNavigationSteps():

    def _source_visits_source_homepage(self):
        self.driver.get(self.source_location)

        self.assertEqual("SecureDrop | Protecting Journalists and Sources", self.driver.title)

    def _source_chooses_to_submit_documents(self):
        self.driver.find_element_by_id('submit-documents-button').click()

        code_name = self.driver.find_element_by_css_selector('#code-name')

        self.assertTrue(len(code_name.text) > 0)
        self.source_name = code_name.text

    def _source_continues_to_submit_page(self):
        continue_button = self.driver.find_element_by_id('continue-button')

        continue_button.click()
        headline = self.driver.find_element_by_class_name('headline')
        self.assertEqual('Submit a document, message, or both', headline.text)

