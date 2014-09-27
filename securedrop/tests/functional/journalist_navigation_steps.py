import urllib2
import tempfile
import zipfile

from db import db_session, Journalist

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

    def _journalist_logs_in(self):
        # Create a test user for logging in
        test_user_info = dict(
            username='test',
            password='test')
        test_user = Journalist(**test_user_info)
        db_session.add(test_user)
        db_session.commit()

        # Test logging in
        self.driver.get(self.journalist_location)
        username = self.driver.find_element_by_css_selector('input[name="username"]')
        username.send_keys(test_user_info['username'])

        password = self.driver.find_element_by_css_selector('input[name="password"]')
        password.send_keys(test_user_info['password'])

        token = self.driver.find_element_by_css_selector('input[name="token"]')
        token.send_keys(test_user.totp.now())

        submit_button = self.driver.find_element_by_css_selector('button[type=submit]')
        submit_button.click()

        headline = self.driver.find_element_by_css_selector('span.headline')
        self.assertIn('Sources', headline.text)

    def _journalist_checks_messages(self):
        self.driver.get(self.journalist_location)

        code_names = self.driver.find_elements_by_class_name('code-name')
        self.assertEquals(1, len(code_names))

    def _journalist_downloads_message(self):
        self.driver.find_element_by_css_selector('#un-starred-source-link-1').click()

        submissions = self.driver.find_elements_by_css_selector('#submissions a')
        self.assertEqual(1, len(submissions))

        file_url = submissions[0].get_attribute('href')

        # Downloading files with Selenium is tricky because it cannot automate
        # the browser's file download dialog. We can directly request the file
        # using urllib2, but we need to pass the cookies for the logged in user
        # for Flask to allow this.
        def cookie_string_from_selenium_cookies(cookies):
            cookie_strs = []
            for cookie in cookies:
                cookie_str = "=".join([cookie['name'], cookie['value']]) + ';'
                cookie_strs.append(cookie_str)
            return ' '.join(cookie_strs)

        submission_req = urllib2.Request(file_url)
        submission_req.add_header('Cookie',
                cookie_string_from_selenium_cookies(self.driver.get_cookies()))
        raw_content = urllib2.urlopen(submission_req).read()

        decrypted_submission = self.gpg.decrypt(raw_content)
        submission = self._get_submission_content(file_url, decrypted_submission)
        self.assertEqual(self.secret_message, submission)
