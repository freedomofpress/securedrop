import pytest
import requests
from tests.functional import tor_utils
from tests.functional.pageslayout.utils import list_locales, save_screenshot_and_html
from tests.functional.web_drivers import WebDriverTypeEnum, get_web_driver
from version import __version__


@pytest.mark.pagelayout
class TestSourceAppStaticPages:
    @pytest.mark.parametrize("locale", list_locales())
    def test_notfound(self, locale, sd_servers):
        # Given a source user accessing the app from their browser
        locale_with_commas = locale.replace("_", "-")
        with get_web_driver(
            web_driver_type=WebDriverTypeEnum.TOR_BROWSER,
            accept_languages=locale_with_commas,
        ) as tor_browser_web_driver:

            # When they try to access a page that does not exist
            tor_browser_web_driver.get(f"{sd_servers.source_app_base_url}/does_not_exist")

            # Then the right error is displayed
            message = tor_browser_web_driver.find_element_by_id("page-not-found")
            assert message.is_displayed()

            save_screenshot_and_html(tor_browser_web_driver, locale, "source-notfound")

    @pytest.mark.parametrize("locale", list_locales())
    def test_static_pages(self, locale, sd_servers):
        # Given a source user accessing the app from their browser
        locale_with_commas = locale.replace("_", "-")
        with get_web_driver(
            web_driver_type=WebDriverTypeEnum.TOR_BROWSER,
            accept_languages=locale_with_commas,
        ) as tor_browser_web_driver:
            # The user can browse to some of the app's static pages
            tor_browser_web_driver.get(f"{sd_servers.source_app_base_url}/use-tor")
            save_screenshot_and_html(tor_browser_web_driver, locale, "source-use_tor_browser")

            tor_browser_web_driver.get(f"{sd_servers.source_app_base_url}/tor2web-warning")
            save_screenshot_and_html(tor_browser_web_driver, locale, "source-tor2web_warning")

            tor_browser_web_driver.get(f"{sd_servers.source_app_base_url}/why-public-key")
            save_screenshot_and_html(tor_browser_web_driver, locale, "source-why_journalist_key")

    def test_instance_metadata(self, sd_servers):
        # Given a source app, when fetching the instance's metadata
        url = f"{sd_servers.source_app_base_url}/metadata"
        response = requests.get(url=url, proxies=tor_utils.proxies_for_url(url))

        # Then it succeeds and the right information is returned
        returned_data = response.json()
        assert returned_data["server_os"] == "20.04"
        assert returned_data["sd_version"] == __version__
        assert returned_data["gpg_fpr"]
