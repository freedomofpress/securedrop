from pathlib import Path
import requests
from tests.functional.app_navigators import SourceAppNagivator
from tests.functional.conftest import spawn_sd_servers
from tests.functional.factories import SecureDropConfigFactory
from tests.functional import tor_utils
import werkzeug
import pytest

from tests.test_journalist import VALID_PASSWORD


@pytest.fixture(scope="session")
def sd_servers_with_designation_collisions(setup_journalist_key_and_gpg_folder):
    """Spawn source and journalist apps that can only generate the same journalist designation."""
    sd_tests_path = Path("/tmp/sd-tests")
    sd_tests_path.mkdir(exist_ok=True)

    # Create a nouns file of 1 word
    nouns_path = sd_tests_path / "noun_for_collisions.txt"
    nouns_path.touch(exist_ok=True)
    nouns_path.write_text("accent")

    # Create an adjectives file of 1 word
    adjectives_path = sd_tests_path / "adjective_for_collisions.txt"
    adjectives_path.touch(exist_ok=True)
    adjectives_path.write_text("tonic")

    config_for_collisions = SecureDropConfigFactory.create(
        SECUREDROP_DATA_ROOT=Path("/tmp/sd-tests/functional-designation-collisions"),
        NOUNS=nouns_path,
        ADJECTIVES=adjectives_path,
    )

    # Ensure the GPG settings match the one in the config to use, to ensure consistency
    journalist_key_fingerprint, gpg_dir = setup_journalist_key_and_gpg_folder
    assert Path(config_for_collisions.GPG_KEY_DIR) == gpg_dir
    assert config_for_collisions.JOURNALIST_KEY == journalist_key_fingerprint

    # Spawn the apps in separate processes
    with spawn_sd_servers(config_to_use=config_for_collisions) as sd_servers_result:
        yield sd_servers_result


class TestSourceAppesignationCollision:

    def test(self, sd_servers_with_designation_collisions, tor_browser_web_driver):
        # Given a source app configured to always generate the same journalist designation
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_with_designation_collisions.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # And a source user who created an account
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        navigator.source_continues_to_submit_page()
        navigator.source_logs_out()

        # When another source user creates an account but gets the same journalist designation
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()

        # Then the right error message is displayed
        navigator.nav_helper.safe_click_by_id("continue-button")
        navigator.nav_helper.wait_for(
            lambda: navigator.driver.find_element_by_css_selector(".error")
        )
        flash_error = navigator.driver.find_element_by_css_selector(".error")
        assert "There was a temporary problem creating your account" in flash_error.text


class TestSourceAppCodenameHints:

    FIRST_SUBMISSION_TEXT = "Please check back later for replies"
    SUBMISSION_ON_FIRST_LOGIN_TEXT = "Forgot your codename?"

    def test_no_codename_hint_on_second_login(self, sd_servers_v2, tor_browser_web_driver):
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_v2.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # Given a source user who creates an account
        # When they first login
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        navigator.source_continues_to_submit_page()

        # Then they are able to retrieve their codename from the UI
        source_codename = navigator.source_retrieves_codename_from_hint()
        assert source_codename

        # And they are able to close the codename hint UI
        content = navigator.driver.find_element_by_css_selector("details#codename-hint")
        assert content.get_attribute("open") is not None
        navigator.nav_helper.safe_click_by_id("codename-hint")
        assert content.get_attribute("open") is None

        # And on their second login
        navigator.source_logs_out()
        navigator.source_visits_source_homepage()
        navigator.source_chooses_to_login()
        navigator.source_proceeds_to_login(codename=source_codename)

        # The codename hint UI is no longer present
        codename = navigator.driver.find_elements_by_css_selector(".code-reminder")
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
        assert self.SUBMISSION_ON_FIRST_LOGIN_TEXT in confirmation_text_first_submission
        assert self.FIRST_SUBMISSION_TEXT in confirmation_text_first_submission

        # And when they submit a second message
        confirmation_text_second_submission = navigator.source_submits_a_message()

        # Then they don't see the messages since it's not their first submission
        assert self.SUBMISSION_ON_FIRST_LOGIN_TEXT not in confirmation_text_second_submission
        assert self.FIRST_SUBMISSION_TEXT not in confirmation_text_second_submission

    def test_submission_notifications_on_second_login(self, sd_servers_v2, tor_browser_web_driver):
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_v2.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # Given a source user who creates an account
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        navigator.source_continues_to_submit_page()
        source_codename = navigator.source_retrieves_codename_from_hint()
        assert source_codename

        # When they submit a message during their second login
        navigator.source_logs_out()
        navigator.source_visits_source_homepage()
        navigator.source_chooses_to_login()
        navigator.source_proceeds_to_login(codename=source_codename)

        # Then it succeeds
        confirmation_text_first_submission = navigator.source_submits_a_message()

        # And they see the expected confirmation messages for a first submission on second login
        assert self.SUBMISSION_ON_FIRST_LOGIN_TEXT not in confirmation_text_first_submission
        assert self.FIRST_SUBMISSION_TEXT in confirmation_text_first_submission

        # And when they submit a second message
        confirmation_text_second_submission = navigator.source_submits_a_message()

        # Then they don't see the messages since it's not their first submission
        assert self.SUBMISSION_ON_FIRST_LOGIN_TEXT not in confirmation_text_second_submission
        assert self.FIRST_SUBMISSION_TEXT not in confirmation_text_second_submission


# TODO(AD): This test duplicates TestSourceLayout.test_why_journalist_key() - remove it?
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
        codename = navigator.driver.find_element_by_css_selector("#codename").text
        assert codename
        return codename

    def test_generate_codenames_in_multiple_tabs(self, sd_servers_v2, tor_browser_web_driver):
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_v2.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # Given a user who generated a codename in Tab A
        tab_a = navigator.driver.window_handles[0]
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        codename_a = self._extract_generated_codename(navigator)

        # And they then opened a new tab, Tab B
        navigator.driver.execute_script("window.open('about:blank', '_blank')")
        tab_b = navigator.driver.window_handles[1]
        navigator.driver.switch_to.window(tab_b)
        assert tab_a != tab_b

        # And they also generated another codename in Tab B
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        codename_b = self._extract_generated_codename(navigator)
        assert codename_a != codename_b

        # And they ended up creating their account and submitting documents in Tab A
        navigator.driver.switch_to.window(tab_a)
        navigator.source_continues_to_submit_page()
        self._assert_is_on_lookup_page(navigator)
        assert navigator.source_retrieves_codename_from_hint() == codename_a
        navigator.source_submits_a_message()

        # When the user tries to create an account and submit documents in Tab B
        navigator.driver.switch_to.window(tab_b)
        navigator.source_continues_to_submit_page()

        # Then the submission fails and the user sees the corresponding flash message in Tab B
        self._assert_is_on_lookup_page(navigator)
        notification = navigator.source_sees_flash_message()
        if not navigator.accept_languages:
            assert "You are already logged in." in notification.text

        # And the user's actual codename is the one initially generated in Tab A
        assert navigator.source_retrieves_codename_from_hint() == codename_a

    def test_generate_and_refresh_codenames_in_multiple_tabs(
        self, sd_servers_v2, tor_browser_web_driver
    ):
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_v2.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # Given a user who generated a codename in Tab A
        tab_a = navigator.driver.window_handles[0]
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        codename_a1 = self._extract_generated_codename(navigator)

        # And they then re-generated their codename in Tab A
        navigator.driver.refresh()
        codename_a2 = self._extract_generated_codename(navigator)
        assert codename_a1 != codename_a2

        # And they then opened a new tab, Tab B
        navigator.driver.execute_script("window.open('about:blank', '_blank')")
        tab_b = navigator.driver.window_handles[1]
        navigator.driver.switch_to.window(tab_b)
        assert tab_a != tab_b

        # And they also generated another codename in Tab B
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        codename_b = self._extract_generated_codename(navigator)
        assert codename_a2 != codename_b

        # And they ended up creating their account and submitting documents in Tab A
        navigator.driver.switch_to.window(tab_a)
        navigator.source_continues_to_submit_page()
        self._assert_is_on_lookup_page(navigator)
        assert navigator.source_retrieves_codename_from_hint() == codename_a2
        navigator.source_submits_a_message()

        # When they try to re-generate a codename in Tab B
        navigator.driver.switch_to.window(tab_b)
        navigator.driver.refresh()

        # Then they get redirected to /lookup with the corresponding flash message
        self._assert_is_on_lookup_page(navigator)
        notification = navigator.source_sees_flash_message()
        if not navigator.accept_languages:
            assert "You were redirected because you are already logged in." in notification.text

        # And the user's actual codename is the expected one
        assert navigator.source_retrieves_codename_from_hint() == codename_a2

    # TODO(AD): This test takes ~50s ; we could refactor it to speed it up
    def test_codenames_exceed_max_cookie_size(self, sd_servers_v2, tor_browser_web_driver):
        """Test generation of enough codenames that the resulting cookie exceeds the recommended
        `werkzeug.Response.max_cookie_size` = 4093 bytes. (#6043)
        """
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_v2.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        too_many = 2*(werkzeug.Response.max_cookie_size // len(VALID_PASSWORD))
        for _ in range(too_many):
            navigator.source_visits_source_homepage()
            navigator.source_clicks_submit_documents_on_homepage()

        navigator.source_continues_to_submit_page()
