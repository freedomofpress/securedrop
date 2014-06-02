import urllib2
import tempfile
import zipfile

class JournalistNavigationSteps():

    def _get_submission_content(self, file_url, raw_content):
        if not file_url.endswith(".zip.gpg"):
            return str(raw_content)

        with tempfile.TemporaryFile() as fp:
            fp.write(raw_content.data)
            fp.seek(0)

            zip_file = zipfile.ZipFile(fp)
            content = zip_file.open(zip_file.namelist()[0]).read()

            return content

    def _journalist_checks_messages(self):
        self.driver.get(self.journalist_location)

        code_names = self.driver.find_elements_by_class_name('code-name')
        self.assertEquals(1, len(code_names))

    def _journalist_downloads_message(self):
        self.driver.find_element_by_css_selector('#un-starred-source-link-1').click()

        submissions = self.driver.find_elements_by_css_selector('#submissions a')

        self.assertEqual(1, len(submissions))

        file_url = submissions[0].get_attribute('href')

        raw_content = urllib2.urlopen(file_url).read()

        decrypted_submission = self.gpg.decrypt(raw_content)

        submission = self._get_submission_content(file_url, decrypted_submission)
        self.assertEqual(self.secret_message, submission)
