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
import pytest
from tests.functional.app_navigators.source_app_nav import SourceAppNavigator
from tests.functional.pageslayout.utils import list_locales, save_screenshot_and_html


@pytest.mark.parametrize("locale", list_locales())
@pytest.mark.pagelayout
class TestSourceLayout:
    def test(self, locale, sd_servers_with_clean_state, tor_browser_web_driver):
        # Given a source user accessing the app from their browser
        locale_with_commas = locale.replace("_", "-")
        source_app_nav = SourceAppNavigator(
            source_app_base_url=sd_servers_with_clean_state.source_app_base_url,
            web_driver=tor_browser_web_driver,
            accept_languages=locale_with_commas,
        )

        # And they created an account
        source_app_nav.source_visits_source_homepage()

        # Take a screenshot of the "account created" page
        source_app_nav.source_clicks_submit_documents_on_homepage()
        save_screenshot_and_html(source_app_nav.driver, locale, "source-generate")

        # Take a screenshot of showing the codename hint
        source_app_nav.source_continues_to_submit_page()
        source_app_nav.source_retrieves_codename_from_hint()
        save_screenshot_and_html(source_app_nav.driver, locale, "source-lookup-shows-codename")

        # Take a screenshot of entering text in the message field
        source_app_nav.nav_helper.safe_send_keys_by_id("msg", "Secret message éè")
        save_screenshot_and_html(source_app_nav.driver, locale, "source-submission_entered_text")

        # Take a screenshot of submitting a file
        source_app_nav.source_submits_a_file()
        save_screenshot_and_html(source_app_nav.driver, locale, "source-lookup")

        # Take a screenshot of doing a second submission
        source_app_nav.source_submits_a_message()
        save_screenshot_and_html(
            source_app_nav.driver, locale, "source-next_submission_flashed_message"
        )

    def test_login(self, locale, sd_servers_with_clean_state, tor_browser_web_driver):
        # Given a source user accessing the app from their browser
        source_app_nav = SourceAppNavigator(
            source_app_base_url=sd_servers_with_clean_state.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # And they created an account
        source_app_nav.source_visits_source_homepage()

        # Take a screenshot of the login page
        source_app_nav.source_chooses_to_login()
        save_screenshot_and_html(source_app_nav.driver, locale, "source-login")

        # Take a screenshot of entering text in the login form
        source_app_nav.nav_helper.safe_send_keys_by_id(
            "codename", "ascension hypertext concert synopses"
        )
        save_screenshot_and_html(source_app_nav.driver, locale, "source-enter-codename-in-login")
