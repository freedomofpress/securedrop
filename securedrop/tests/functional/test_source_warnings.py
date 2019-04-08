from . import source_navigation_steps
from . import functional_test
from selenium import webdriver


class TestSourceInterfaceBannerWarnings(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin):

    def test_warning_appears_if_tor_browser_not_in_use(self):
        self.driver.get(self.source_location)

        warning_banner = self.driver.find_element_by_id('use-tor-browser')

        assert ("It is recommended to use the Tor Browser" in
                warning_banner.text)

        # User should be able to dismiss the warning
        warning_dismiss_button = self.driver.find_element_by_id(
            'use-tor-browser-close')
        self.banner_is_dismissed(warning_banner, warning_dismiss_button)

    def test_warning_appears_if_orbot_is_used(self):
        orbotUserAgent = ("Mozilla/5.0 (Android; Mobile;"
                          " rv:52.0) Gecko/20100101 Firefox/52.0")

        # Create new profile and driver with the orbot user agent for this test
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", orbotUserAgent)
        self.driver = webdriver.Firefox(profile)
        self.driver.get(self.source_location)

        currentAgent = self.driver.execute_script("return navigator.userAgent")
        assert currentAgent == orbotUserAgent

        warning_banner = self.driver.find_element_by_id('orfox-browser')

        assert ("It is recommended you use the desktop version of Tor Browser"
                in warning_banner.text)

        # User should be able to dismiss the warning
        warning_dismiss_button = self.driver.find_element_by_id(
            'orfox-browser-close')
        self.banner_is_dismissed(warning_banner, warning_dismiss_button)

    def banner_is_dismissed(self, warning_banner, dismiss_button):

        dismiss_button.click()

        def warning_banner_is_hidden():
            assert warning_banner.is_displayed() is False
        self.wait_for(warning_banner_is_hidden)
