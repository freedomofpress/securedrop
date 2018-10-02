import pytest

from selenium.webdriver import FirefoxProfile

from functional_test import FunctionalHelper

ORBOT_UA = ("Mozilla/5.0 (Android; Mobile;"
            " rv:52.0) Gecko/20100101 Firefox/52.0")


# Create new profile and driver with the orbot user agent for just this test
@pytest.fixture(autouse=True, scope='module')
def firefox_profile():
    profile = FirefoxProfile()
    profile.set_preference("general.useragent.override", ORBOT_UA)
    return profile


def test_warning_appears_if_orbot_is_used(live_source_app, webdriver):
    helper = FunctionalHelper(
        driver=webdriver,
        live_source_app=live_source_app)

    helper.driver.get(helper.source_location)
    currentAgent = helper.driver.execute_script("return navigator.userAgent")
    assert currentAgent == ORBOT_UA  # precondition

    warning_banner = helper.driver.find_element_by_class_name(
        'orfox-browser')

    assert ("It is recommended you use the desktop version of Tor Browser"
            in warning_banner.text)

    # User should be able to dismiss the warning
    warning_dismiss_button = helper.driver.find_element_by_id(
        'orfox-browser-close')
    helper.banner_is_dismissed(warning_banner, warning_dismiss_button)
