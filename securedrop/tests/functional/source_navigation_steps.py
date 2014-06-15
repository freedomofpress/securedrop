
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
        self.assertEqual('You have three options to send data', headline.text)

