from tests.functional.app_navigators.source_app_nav import SourceAppNavigator


class TestSourceUserCancels:
    def test_source_cancels_at_login_page(self, sd_servers, tor_browser_web_driver):
        # Given a source user who goes to the login page
        source_app_nav = SourceAppNavigator(
            source_app_base_url=sd_servers.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )
        source_app_nav.source_visits_source_homepage()
        source_app_nav.source_chooses_to_login()

        # When they click on the cancel button on the login page, it succeeds
        source_app_nav.nav_helper.safe_click_by_css_selector(".form-controls a")
        source_app_nav.driver.get(sd_servers.source_app_base_url)
        assert source_app_nav._is_on_source_homepage()

    def test_source_cancels_at_submit_page(self, sd_servers, tor_browser_web_driver):
        # Given a source user who created an account
        source_app_nav = SourceAppNavigator(
            source_app_base_url=sd_servers.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )
        source_app_nav.source_visits_source_homepage()
        source_app_nav.source_clicks_submit_documents_on_homepage()
        source_app_nav.source_continues_to_submit_page()

        # When they click on the cancel button on the submit page, it succeeds
        source_app_nav.nav_helper.safe_click_by_css_selector(".form-controls a")

        # And the right message is displayed
        heading = source_app_nav.driver.find_element_by_id("submit-heading")
        assert "Submit Files or Messages" == heading.text
