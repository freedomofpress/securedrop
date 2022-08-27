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
from tests.functional.app_navigators.journalist_app_nav import JournalistAppNavigator
from tests.functional.pageslayout.utils import list_locales, save_screenshot_and_html


@pytest.mark.parametrize("locale", list_locales())
@pytest.mark.pagelayout
class TestJournalistLayoutDelete:
    def test_delete_none(self, locale, sd_servers_with_submitted_file, firefox_web_driver):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
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

        # And the journalist went to the individual source's page
        journ_app_nav.journalist_visits_col()

        journ_app_nav.journalist_clicks_delete_selected_link()

        journ_app_nav.journalist_confirm_delete_selected()
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-delete_none")

    def test_delete_one_confirmation(
        self, locale, sd_servers_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
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

        # And the journalist went to the individual source's page
        journ_app_nav.journalist_visits_col()

        # And the journalist selected the first submission
        journ_app_nav.journalist_selects_first_doc()

        # Take a screenshot of the confirmation prompt when the journalist clicks the delete button
        journ_app_nav.journalist_clicks_delete_selected_link()
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-delete_one_confirmation")

    def test_delete_all_confirmation(
        self, locale, sd_servers_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
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

        # And the journalist went to the individual source's page
        journ_app_nav.journalist_visits_col()

        # Take a screenshot of the prompt when the journalist clicks the delete all button
        journ_app_nav.journalist_clicks_delete_all_and_sees_confirmation()
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-delete_all_confirmation")

    def test_delete_one(self, locale, sd_servers_with_submitted_file, firefox_web_driver):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
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

        # And the journalist went to the individual source's page
        journ_app_nav.journalist_visits_col()

        journ_app_nav.journalist_selects_first_doc()

        # And the journalist clicked the delete button and confirmed
        journ_app_nav.journalist_clicks_delete_selected_link()
        journ_app_nav.nav_helper.safe_click_by_id("delete-selected")

        # Take a screenshot
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-delete_one")

    def test_delete_all(self, locale, sd_servers_with_submitted_file, firefox_web_driver):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
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

        # And the journalist went to the individual source's page
        journ_app_nav.journalist_visits_col()

        journ_app_nav.journalist_clicks_delete_all_and_sees_confirmation()
        journ_app_nav.journalist_confirms_delete_selected()

        # Take a screenshot
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-delete_all")
