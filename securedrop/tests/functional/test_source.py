import requests

from tests.functional.app_navigators import SourceAppNagivator
from tests.functional import tor_utils


class TestSourceAppCodenameHints:

    FIRST_SUBMISSION_TEXT = "Please check back later for replies"

    def test_no_codename_hint_on_second_login(self, sd_servers_v2, tor_browser_web_driver):
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_v2.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # Given a source user who creates an account
        # When they first submit a message
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        navigator.source_continues_to_submit_page()
        navigator.source_submits_a_message("they're here")

        # Then they are able to retrieve their codename from the UI
        source_codename = navigator.source_retrieves_codename_from_hint()
        assert source_codename

        # And they are able to close the codename hint UI
        content = navigator.driver.find_element_by_id("codename-show-checkbox")
        assert content.get_attribute("checked") is not None
        navigator.nav_helper.safe_click_by_id("codename-show")
        assert content.get_attribute("checked") is None

        # And on their second login
        navigator.source_logs_out()
        navigator.source_visits_source_homepage()
        navigator.source_chooses_to_login()
        navigator.source_proceeds_to_login(codename=source_codename)

        # The codename hint UI is no longer present
        codename = navigator.driver.find_elements_by_css_selector("#codename-reminder")
        assert len(codename) == 0

    def test_submission_notifications_on_first_login(self, sd_servers_v2, tor_browser_web_driver):
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_v2.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # Given a source user who creates an account
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        navigator.source_continues_to_submit_page()

        # When they submit a message during their first login
        # Then it succeeds
        confirmation_text_first_submission = navigator.source_submits_a_message()

        # And they see the expected confirmation messages for a first submission on first login
        assert self.FIRST_SUBMISSION_TEXT in confirmation_text_first_submission

        # And when they submit a second message
        confirmation_text_second_submission = navigator.source_submits_a_message()

        # Then they don't see the messages since it's not their first submission
        assert self.FIRST_SUBMISSION_TEXT not in confirmation_text_second_submission

    def test_submission_notifications_on_second_login(self, sd_servers_v2, tor_browser_web_driver):
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_v2.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # Given a source user who creates an account by submitting a
        # message on first login
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        navigator.source_continues_to_submit_page()
        confirmation_text_first_submission = navigator.source_submits_a_message()

        # And they see the expected confirmation messages for a first submission on second login
        assert self.FIRST_SUBMISSION_TEXT in confirmation_text_first_submission

        source_codename = navigator.source_retrieves_codename_from_hint()
        assert source_codename

        # When they submit a message during their second login
        navigator.source_logs_out()
        navigator.source_visits_source_homepage()
        navigator.source_chooses_to_login()
        navigator.source_proceeds_to_login(codename=source_codename)

        # And when they submit a second message
        confirmation_text_second_submission = navigator.source_submits_a_message()

        # Then they don't see the messages since it's not their first submission
        assert self.FIRST_SUBMISSION_TEXT not in confirmation_text_second_submission


class TestSourceAppDownloadJournalistKey:
    def test(self, sd_servers_v2):
        # Given a source app, when fetching the instance's journalist public key
        url = f"{sd_servers_v2.source_app_base_url}/public-key"
        response = requests.get(url=url, proxies=tor_utils.proxies_for_url(url))

        # Then it succeeds and the right data is returned
        assert "BEGIN PGP PUBLIC KEY BLOCK" in response.content.decode("utf-8")


class TestSourceAppCodenamesInMultipleTabs:
    """Test generation of multiple codenames in different browser tabs, ref. issue 4458."""

    @staticmethod
    def _assert_is_on_lookup_page(navigator: SourceAppNagivator) -> None:
        navigator.nav_helper.wait_for(lambda: navigator.driver.find_element_by_id("upload"))

    @staticmethod
    def _extract_generated_codename(navigator: SourceAppNagivator) -> str:
        codename = navigator.driver.find_element_by_css_selector("#codename span").text
        assert codename
        return codename

    def test_generate_codenames_in_multiple_tabs(self, sd_servers_v2, tor_browser_web_driver):
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_v2.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # Given a user who opens /lookup in tab A
        tab_a = navigator.driver.window_handles[0]
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        navigator.source_continues_to_submit_page()

        # And they then opened a new tab, Tab B
        navigator.driver.execute_script("window.open('about:blank', '_blank')")
        tab_b = navigator.driver.window_handles[1]
        navigator.driver.switch_to.window(tab_b)
        assert tab_a != tab_b

        # And they also opened /lookup in Tab B
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        navigator.source_continues_to_submit_page()

        # And they ended up creating their account and submitting documents in Tab A
        navigator.driver.switch_to.window(tab_a)
        navigator.source_continues_to_submit_page()
        self._assert_is_on_lookup_page(navigator)
        navigator.source_submits_a_message()
        passphrase_a = navigator.source_retrieves_codename_from_hint()

        # When the user tries to create an account and submit documents in Tab B
        navigator.driver.switch_to.window(tab_b)
        navigator.source_submits_a_message()
        passphrase_b = navigator.source_retrieves_codename_from_hint()

        # Then the submission succeeds
        self._assert_is_on_lookup_page(navigator)

        # And the user's actual codename is the one initially generated in Tab A
        assert passphrase_b == passphrase_a
