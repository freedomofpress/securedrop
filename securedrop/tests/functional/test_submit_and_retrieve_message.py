from pathlib import Path

from encryption import EncryptionManager
from tests.functional.app_navigators.journalist_app_nav import JournalistAppNavigator
from tests.functional.app_navigators.source_app_nav import SourceAppNavigator


class TestSubmitAndRetrieveMessage:
    def test_submit_and_retrieve_happy_path(
        self, sd_servers_with_clean_state, tor_browser_web_driver, firefox_web_driver
    ):
        # Given a source user accessing the app from their browser
        source_app_nav = SourceAppNavigator(
            source_app_base_url=sd_servers_with_clean_state.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # And they created an account
        source_app_nav.source_visits_source_homepage()
        source_app_nav.source_clicks_submit_documents_on_homepage()
        source_app_nav.source_continues_to_submit_page()

        # And the source user submitted a message
        submitted_message = "Confidential message with some international characters: éèö"
        source_app_nav.source_submits_a_message(message=submitted_message)
        source_app_nav.source_logs_out()

        # When a journalist logs in
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_clean_state.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_clean_state.journalist_username,
            password=sd_servers_with_clean_state.journalist_password,
            otp_secret=sd_servers_with_clean_state.journalist_otp_secret,
        )
        journ_app_nav.journalist_checks_messages()

        #  And they try to download the message
        #  Then it succeeds and the journalist sees correct message
        servers_sd_config = sd_servers_with_clean_state.config_in_use
        retrieved_message = journ_app_nav.journalist_downloads_first_message(
            encryption_mgr_to_use_for_decryption=EncryptionManager(
                gpg_key_dir=Path(servers_sd_config.GPG_KEY_DIR),
                journalist_key_fingerprint=servers_sd_config.JOURNALIST_KEY,
            )
        )
        assert retrieved_message == submitted_message
