import time
from pathlib import Path

import pytest

from tests.functional.conftest import spawn_sd_servers
from tests.functional.app_navigators import SourceAppNagivator
from tests.functional.factories import SecureDropConfigFactory


# Very short session expiration time
SESSION_EXPIRATION_SECONDS = 3


@pytest.fixture(scope="session")
def sd_servers_with_short_session_timeout(setup_journalist_key_and_gpg_folder):
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


# TODO(AD): This test duplicates TestSourceSessionLayout - remove it?
class TestSourceAppSessionExpiration:
    def test(self, sd_servers_with_short_session_timeout, tor_browser_web_driver):
        navigator = SourceAppNagivator(
            source_app_base_url=sd_servers_with_short_session_timeout.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # Given a source user who's logged in and is using the source app
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        navigator.source_continues_to_submit_page()

        # And their session just expired
        time.sleep(SESSION_EXPIRATION_SECONDS + 1)

        # When the source user reloads the page
        navigator.driver.refresh()

        # Then the source user sees the "session expired" message
        notification = navigator.driver.find_element_by_css_selector(".important")
        expected_text = "You were logged out due to inactivity."
        assert expected_text in notification.text
