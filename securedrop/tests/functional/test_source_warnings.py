import os
import shutil
import pytest
from selenium import webdriver

from tests.functional.app_navigators import SourceAppNagivator

from . import functional_test


@pytest.fixture
def orbot_web_driver(sd_servers_v2):
    # Create new profile and driver with the orbot user agent
    orbot_user_agent = "Mozilla/5.0 (Android; Mobile; rv:52.0) Gecko/20100101 Firefox/52.0"
    f_profile_path2 = "/tmp/testprofile2"
    if os.path.exists(f_profile_path2):
        shutil.rmtree(f_profile_path2)
    os.mkdir(f_profile_path2)
    profile = webdriver.FirefoxProfile(f_profile_path2)
    profile.set_preference("general.useragent.override", orbot_user_agent)

    if sd_servers_v2.journalist_app_base_url.find(".onion") != -1:
        # set FF preference to socks proxy in Tor Browser
        profile.set_preference("network.proxy.type", 1)
        profile.set_preference("network.proxy.socks", "127.0.0.1")
        profile.set_preference("network.proxy.socks_port", 9150)
        profile.set_preference("network.proxy.socks_version", 5)
        profile.set_preference("network.proxy.socks_remote_dns", True)
        profile.set_preference("network.dns.blockDotOnion", False)
    profile.update_preferences()
    orbot_web_driver = webdriver.Firefox(
        firefox_binary=functional_test.FIREFOX_PATH, firefox_profile=profile
    )

    try:
        driver_user_agent = orbot_web_driver.execute_script("return navigator.userAgent")
        assert driver_user_agent == orbot_user_agent
        yield orbot_web_driver
    finally:
        orbot_web_driver.quit()


class TestSourceAppBrowserWarnings:
    def test_warning_appears_if_tor_browser_not_in_use(self, sd_servers_v2, firefox_web_driver):
        # Given a user
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_v2.source_app_base_url,
            # Who is using Firefox instead of the tor browser
            web_driver=firefox_web_driver,
        )

        # When they access the source app's home page
        navigator.source_visits_source_homepage()

        # Then they see a warning
        warning_banner = navigator.driver.find_element_by_id("use-tor-browser")
        assert "It is recommended to use Tor Browser" in warning_banner.text

        # And they are able to dismiss the warning
        warning_dismiss_button = navigator.driver.find_element_by_id("use-tor-browser-close")
        warning_dismiss_button.click()

        def warning_banner_is_hidden():
            assert warning_banner.is_displayed() is False

        navigator.nav_helper.wait_for(warning_banner_is_hidden)

    def test_warning_appears_if_orbot_is_used(self, sd_servers_v2, orbot_web_driver):
        # Given a user
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_v2.source_app_base_url,
            # Who is using Orbot instead of the (desktop) Tor browser
            web_driver=orbot_web_driver,
        )

        # When they access the source app's home page
        navigator.source_visits_source_homepage()

        # Then they see a warning
        warning_banner = navigator.driver.find_element_by_id("orfox-browser")
        assert "use the desktop version of Tor Browser" in warning_banner.text

        # And they are able to dismiss the warning
        warning_dismiss_button = navigator.driver.find_element_by_id("orfox-browser-close")
        warning_dismiss_button.click()

        def warning_banner_is_hidden():
            assert warning_banner.is_displayed() is False

        navigator.nav_helper.wait_for(warning_banner_is_hidden)

    def test_warning_high_security(self, sd_servers_v2, tor_browser_web_driver):
        # Given a user
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_v2.source_app_base_url,
            # Who is using the Tor browser
            web_driver=tor_browser_web_driver,
        )

        # When they access the source app's home page
        navigator.source_visits_source_homepage()

        # Then they see a warning
        banner = navigator.driver.find_element_by_id("js-warning")
        assert "Security Slider to Safest", banner.text
