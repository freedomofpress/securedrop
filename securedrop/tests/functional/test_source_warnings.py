import os
import shutil

from selenium import webdriver

from . import functional_test
from . import source_navigation_steps


class TestSourceInterfaceBannerWarnings(
    functional_test.FunctionalTest, source_navigation_steps.SourceNavigationStepsMixin
):
    def test_warning_appears_if_tor_browser_not_in_use(self):
        try:
            self.switch_to_firefox_driver()
            self.driver.get(self.source_location)

            warning_banner = self.driver.find_element_by_id("use-tor-browser")

            assert "It is recommended to use Tor Browser" in warning_banner.text

            # User should be able to dismiss the warning
            warning_dismiss_button = self.driver.find_element_by_id("use-tor-browser-close")
            self.banner_is_dismissed(warning_banner, warning_dismiss_button)
        finally:
            self.switch_to_torbrowser_driver()

    def test_warning_appears_if_orbot_is_used(self):
        orbotUserAgent = "Mozilla/5.0 (Android; Mobile;" " rv:52.0) Gecko/20100101 Firefox/52.0"

        self.f_profile_path2 = "/tmp/testprofile2"
        if os.path.exists(self.f_profile_path2):
            shutil.rmtree(self.f_profile_path2)
        # Create new profile and driver with the orbot user agent for this test
        os.mkdir(self.f_profile_path2)
        profile = webdriver.FirefoxProfile(self.f_profile_path2)
        profile.set_preference("general.useragent.override", orbotUserAgent)
        if self.journalist_location.find(".onion") != -1:
            # set FF preference to socks proxy in Tor Browser
            profile.set_preference("network.proxy.type", 1)
            profile.set_preference("network.proxy.socks", "127.0.0.1")
            profile.set_preference("network.proxy.socks_port", 9150)
            profile.set_preference("network.proxy.socks_version", 5)
            profile.set_preference("network.proxy.socks_remote_dns", True)
            profile.set_preference("network.dns.blockDotOnion", False)
        profile.update_preferences()
        self.driver2 = webdriver.Firefox(
            firefox_binary=functional_test.FIREFOX_PATH, firefox_profile=profile
        )
        self.driver2.get(self.source_location)

        currentAgent = self.driver2.execute_script("return navigator.userAgent")
        assert currentAgent == orbotUserAgent

        warning_banner = self.driver2.find_element_by_id("orfox-browser")

        assert "It is recommended you use the desktop version of Tor Browser" in warning_banner.text

        # User should be able to dismiss the warning
        warning_dismiss_button = self.driver2.find_element_by_id("orfox-browser-close")
        self.banner_is_dismissed(warning_banner, warning_dismiss_button)

        self.driver2.quit()

    def banner_is_dismissed(self, warning_banner, dismiss_button):

        dismiss_button.click()

        def warning_banner_is_hidden():
            assert warning_banner.is_displayed() is False

        self.wait_for(warning_banner_is_hidden)

    def test_warning_high_security(self):
        self.driver.get(self.source_location)

        banner = self.driver.find_element_by_id("js-warning")
        assert "Security Slider to Safest", banner.text
