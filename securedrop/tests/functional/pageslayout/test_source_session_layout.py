import time
from pathlib import Path

import pytest
from tests.functional.app_navigators.source_app_nav import SourceAppNavigator
from tests.functional.conftest import spawn_sd_servers
from tests.functional.factories import SecureDropConfigFactory
from tests.functional.pageslayout.utils import list_locales, save_screenshot_and_html

# Very short session expiration time
SESSION_EXPIRATION_SECONDS = 3


@pytest.fixture(scope="session")
def _sd_servers_with_short_timeout(setup_journalist_key_and_gpg_folder):
    """Spawn the source and journalist apps as separate processes with a short session timeout."""
    # Generate a securedrop config with a very short session timeout
    config_with_short_timeout = SecureDropConfigFactory.create(
        SESSION_EXPIRATION_MINUTES=SESSION_EXPIRATION_SECONDS / 60,
        SECUREDROP_DATA_ROOT=Path("/tmp/sd-tests/functional-session-timeout"),
    )

    # Ensure the GPG settings match the one in the config to use, to ensure consistency
    journalist_key_fingerprint, gpg_dir = setup_journalist_key_and_gpg_folder
    assert Path(config_with_short_timeout.GPG_KEY_DIR) == gpg_dir
    assert config_with_short_timeout.JOURNALIST_KEY == journalist_key_fingerprint

    # Spawn the apps in separate processes
    with spawn_sd_servers(config_to_use=config_with_short_timeout) as sd_servers_result:
        yield sd_servers_result


@pytest.mark.parametrize("locale", list_locales())
@pytest.mark.pagelayout
class TestSourceAppSessionTimeout:
    def test_source_session_timeout(self, locale, _sd_servers_with_short_timeout):
        # Given a source user accessing the app from their browser
        locale_with_commas = locale.replace("_", "-")
        with SourceAppNavigator.using_tor_browser_web_driver(
            source_app_base_url=_sd_servers_with_short_timeout.source_app_base_url,
            accept_languages=locale_with_commas,
        ) as navigator:

            # And they're logged in and are using the app
            navigator.source_visits_source_homepage()
            navigator.source_clicks_submit_documents_on_homepage()
            navigator.source_continues_to_submit_page()

            # And their session just expired
            time.sleep(SESSION_EXPIRATION_SECONDS + 1)

            # When the source user reloads the page
            navigator.driver.refresh()

            # Then the source user sees the "session expired" message
            notification = navigator.driver.find_element_by_class_name("error")
            assert notification.text
            if locale == "en_US":
                expected_text = "You were logged out due to inactivity."
                assert expected_text in notification.text

            save_screenshot_and_html(navigator.driver, locale, "source-session_timeout")
