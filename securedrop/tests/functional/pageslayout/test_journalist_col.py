#
# SecureDrop whistleblower submission system
# Copyright (C) 2017 Loic Dachary <loic@dachary.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from pathlib import Path
from typing import Generator, Tuple
from uuid import uuid4

import pytest
from tests.functional.app_navigators.journalist_app_nav import JournalistAppNavigator
from tests.functional.conftest import SdServersFixtureResult, spawn_sd_servers
from tests.functional.factories import SecureDropConfigFactory
from tests.functional.pageslayout.utils import list_locales, save_screenshot_and_html
from tests.functional.sd_config_v2 import SecureDropConfig


def _create_source_and_submission_and_delete_source_key(config_in_use: SecureDropConfig) -> None:
    # This function will be called in a separate Process that runs the app
    # Hence the late imports
    from encryption import EncryptionManager
    from tests.functional.conftest import create_source_and_submission

    source_user, _ = create_source_and_submission(config_in_use)
    EncryptionManager.get_default().delete_source_key_pair(source_user.filesystem_id)


@pytest.fixture(scope="function")
def _sd_servers_with_deleted_source_key(
    setup_journalist_key_and_gpg_folder: Tuple[str, Path]
) -> Generator[SdServersFixtureResult, None, None]:
    """Same as sd_servers but spawns the apps with a source whose key was deleted.

    Slower than sd_servers as it is function-scoped.
    """
    default_config = SecureDropConfigFactory.create(
        SECUREDROP_DATA_ROOT=Path(f"/tmp/sd-tests/functional-with-deleted-source-key-{uuid4()}"),
    )

    # Ensure the GPG settings match the one in the config to use, to ensure consistency
    journalist_key_fingerprint, gpg_dir = setup_journalist_key_and_gpg_folder
    assert Path(default_config.GPG_KEY_DIR) == gpg_dir
    assert default_config.JOURNALIST_KEY == journalist_key_fingerprint

    # Spawn the apps in separate processes with a callback to create a submission
    with spawn_sd_servers(
        config_to_use=default_config,
        journalist_app_setup_callback=_create_source_and_submission_and_delete_source_key,
    ) as sd_servers_result:
        yield sd_servers_result


@pytest.mark.parametrize("locale", list_locales())
@pytest.mark.pagelayout
class TestJournalistLayoutCol:
    def test_col_with_and_without_documents(
        self, locale, sd_servers_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with an already-submitted file
        # And a journalist logging into the journalist interface
        locale_with_commas = locale.replace("_", "-")
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_submitted_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
            accept_languages=locale_with_commas,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_submitted_file.journalist_username,
            password=sd_servers_with_submitted_file.journalist_password,
            otp_secret=sd_servers_with_submitted_file.journalist_otp_secret,
        )

        # Take a screenshot of the individual source's page when there is a document
        journ_app_nav.journalist_visits_col()
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-col")
        # The documentation uses an identical screenshot with a different name:
        # https://github.com/freedomofpress/securedrop-docs/blob/main/docs/images/manual
        # /screenshots/journalist-col_javascript.png
        # So we take the same screenshot again here
        # TODO(AD): Update the documentation to use a single screenshot
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-col_javascript")

        # Take a screenshot of the individual source's page when there are no documents
        journ_app_nav.journalist_clicks_delete_all_and_sees_confirmation()
        journ_app_nav.journalist_confirms_delete_selected()

        def submission_deleted() -> None:
            submissions_after_confirming_count = journ_app_nav.count_submissions_on_current_page()
            # There will be 0 submissions left after deleting the source's submission
            assert submissions_after_confirming_count == 0

        journ_app_nav.nav_helper.wait_for(submission_deleted)
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-col_no_document")

    def test_col_has_no_key(self, locale, _sd_servers_with_deleted_source_key, firefox_web_driver):
        # Given an SD server with an already-submitted file, but the source's key was deleted
        # And a journalist logging into the journalist interface
        locale_with_commas = locale.replace("_", "-")
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=_sd_servers_with_deleted_source_key.journalist_app_base_url,
            web_driver=firefox_web_driver,
            accept_languages=locale_with_commas,
        )
        journ_app_nav.journalist_logs_in(
            username=_sd_servers_with_deleted_source_key.journalist_username,
            password=_sd_servers_with_deleted_source_key.journalist_password,
            otp_secret=_sd_servers_with_deleted_source_key.journalist_otp_secret,
        )

        # Take a screenshot of the source's page after their key was deleted
        journ_app_nav.journalist_visits_col()
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-col_has_no_key")
