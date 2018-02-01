import source_navigation_steps
import journalist_navigation_steps
import functional_test


class TestThatCode(
        functional_test.FunctionalTest,
        journalist_navigation_steps.JournalistNavigationStepsMixin):

    def test_if_we_can_see(self):
        self._journalist_logs_in()
        def cookie_string_from_selenium_cookies(cookies):
            cookie_strs = []
            for cookie in cookies:
                cookie_str = "=".join([cookie['name'], cookie['value']]) + ';'
                cookie_strs.append(cookie_str)
            return ' '.join(cookie_strs)

        #data = cookie_string_from_selenium_cookies(self.driver.get_cookies())
        data = cookie_string_from_selenium_cookies(self.driver.execute_script("return document.cookie"))
        assert len(data) > 1, data
