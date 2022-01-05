# TODO(AD): This test duplicates TestSourceLayout.test_notfound() - remove it?
class TestSourceAppNotFound:

    def test_not_found(self, sd_servers_v2, tor_browser_web_driver):
        # Given a source user
        # When they try to access a page that does not exist
        tor_browser_web_driver.get(f"{sd_servers_v2.source_app_base_url}/does_not_exist")

        # Then the right error is displayed
        message = tor_browser_web_driver.find_element_by_id("page-not-found")
        assert message.is_displayed()
