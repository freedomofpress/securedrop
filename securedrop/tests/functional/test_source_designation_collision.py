from pathlib import Path

import pytest
from tests.factories.configs_factories import SecureDropConfigFactory
from tests.functional.app_navigators.source_app_nav import SourceAppNavigator
from tests.functional.conftest import spawn_sd_servers


@pytest.fixture(scope="session")
def _sd_servers_with_designation_collisions(setup_journalist_key_and_gpg_folder, setup_rqworker):
    """Spawn source and journalist apps that can only generate a single journalist designation."""
    # Generate a config that can only generate a single journalist designation
    folder_for_fixture_path = Path("/tmp/sd-tests/functional-designation-collisions")
    folder_for_fixture_path.mkdir(parents=True, exist_ok=True)
    nouns_path = folder_for_fixture_path / "nouns.txt"
    nouns_path.touch(exist_ok=True)
    nouns_path.write_text("accent")
    adjectives_path = folder_for_fixture_path / "adjectives.txt"
    adjectives_path.touch(exist_ok=True)
    adjectives_path.write_text("tonic")

    worker_name, _ = setup_rqworker
    journalist_key_fingerprint, gpg_key_dir = setup_journalist_key_and_gpg_folder
    config_for_collisions = SecureDropConfigFactory.create(
        SECUREDROP_DATA_ROOT=folder_for_fixture_path / "sd_data_root",
        NOUNS=nouns_path,
        ADJECTIVES=adjectives_path,
        GPG_KEY_DIR=gpg_key_dir,
        JOURNALIST_KEY=journalist_key_fingerprint,
        RQ_WORKER_NAME=worker_name,
    )

    # Spawn the apps in separate processes
    with spawn_sd_servers(config_to_use=config_for_collisions) as sd_servers_result:
        yield sd_servers_result


class TestSourceAppDesignationCollision:
    def test(self, _sd_servers_with_designation_collisions, tor_browser_web_driver):
        navigator = SourceAppNavigator(
            source_app_base_url=_sd_servers_with_designation_collisions.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # Given a source user who created an account
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()
        navigator.source_continues_to_submit_page()
        navigator.source_logs_out()

        # When another source user creates an account but gets the same journalist designation
        navigator.source_visits_source_homepage()
        navigator.source_clicks_submit_documents_on_homepage()

        # Then the right error message is displayed
        navigator.nav_helper.safe_click_by_css_selector("#create-form button")
        navigator.nav_helper.wait_for(
            lambda: navigator.driver.find_element_by_css_selector(".error")
        )
        flash_error = navigator.driver.find_element_by_css_selector(".error")
        assert "There was a temporary problem creating your account" in flash_error.text
