
class JournalistNavigationSteps():

    def _journalist_checks_messages(self):
        self.driver.get(self.journalist_location)

        code_names = self.driver.find_elements_by_class_name('code-name')
        self.assertEquals(1, len(code_names))

    def _journalist_downloads_message(self):
        self.driver.find_element_by_css_selector('.code-name a').click()

        submissions = self.driver.find_elements_by_css_selector('#submissions a')

        self.assertEqual(1, len(submissions))

        file_url = submissions[0].get_attribute('href')

        encrypted_submission = urllib2.urlopen(file_url).read()
        submission = str(self.gpg.decrypt(encrypted_submission))
        self.assertEqual(self.secret_message, submission)
