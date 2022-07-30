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
from tests.functional.app_navigators import JournalistAppNavigator
from tests.functional.pageslayout.functional_test import list_locales
from tests.functional.pageslayout.screenshot_utils import save_screenshot_and_html


@pytest.mark.parametrize("locale", list_locales())
@pytest.mark.pagelayout
class TestJournalistLayout:
    def test_login_index_and_edit(self, locale, sd_servers_v2, firefox_web_driver):
        # Given an SD server
        # And a journalist accessing the journalist interface
        locale_with_commas = locale.replace("_", "-")
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_v2.journalist_app_base_url,
            web_driver=firefox_web_driver,
            accept_languages=locale_with_commas,
        )
        journ_app_nav.driver.get(f"{sd_servers_v2.journalist_app_base_url}/login")
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-login")

        # And they log into the app and are an admin
        assert sd_servers_v2.journalist_is_admin
        journ_app_nav.journalist_logs_in(
            username=sd_servers_v2.journalist_username,
            password=sd_servers_v2.journalist_password,
            otp_secret=sd_servers_v2.journalist_otp_secret,
        )
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-index_no_documents")

        # Take a screenshot of the edit account page
        journ_app_nav.journalist_visits_edit_account()
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-edit_account_user")

    def test_index_with_submission_and_select_documents(
        self, locale, sd_servers_v2_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with an already-submitted file
        # And a journalist logging into the journalist interface
        locale_with_commas = locale.replace("_", "-")
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_v2_with_submitted_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
            accept_languages=locale_with_commas,
        )

        # Take a screenshot of the index page when there is a source and submission
        journ_app_nav.journalist_logs_in(
            username=sd_servers_v2_with_submitted_file.journalist_username,
            password=sd_servers_v2_with_submitted_file.journalist_password,
            otp_secret=sd_servers_v2_with_submitted_file.journalist_otp_secret,
        )
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-index")

        # Take a screenshot of the source's page
        journ_app_nav.journalist_selects_the_first_source()
        checkboxes = journ_app_nav.get_submission_checkboxes_on_current_page()
        for checkbox in checkboxes:
            checkbox.click()
        save_screenshot_and_html(
            journ_app_nav.driver, locale, "journalist-clicks_on_source_and_selects_documents"
        )

        # Take a screenshot of the reply page
        journ_app_nav.journalist_composes_reply_to_source(
            reply_content="Thanks for the documents."
            " Can you submit more information about the main program?"
        )
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-composes_reply")

    def test_fail_to_visit_admin(self, locale, sd_servers_v2, firefox_web_driver):
        # Given an SD server
        # And someone accessing the journalist interface
        locale_with_commas = locale.replace("_", "-")
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_v2.journalist_app_base_url,
            web_driver=firefox_web_driver,
            accept_languages=locale_with_commas,
        )
        # Take a screenshot of them trying to force-browse to the admin interface
        journ_app_nav.driver.get(f"{sd_servers_v2.journalist_app_base_url}/admin")
        save_screenshot_and_html(
            journ_app_nav.driver, locale, "journalist-code-fail_to_visit_admin"
        )

    def test_fail_login(self, locale, sd_servers_v2, firefox_web_driver):
        # Given an SD server
        # And someone accessing the journalist interface
        locale_with_commas = locale.replace("_", "-")
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_v2.journalist_app_base_url,
            web_driver=firefox_web_driver,
            accept_languages=locale_with_commas,
        )

        # Take a screenshot of trying to log in using invalid credentials
        journ_app_nav.journalist_logs_in(
            username="root",
            password="worse",
            otp_secret="2HGGVF5VPHWMCAYQ",
            is_login_expected_to_succeed=False,
        )
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-code-fail_login")

    def test_fail_login_many(self, locale, sd_servers_v2, firefox_web_driver):
        # Given an SD server
        # And someone accessing the journalist interface
        locale_with_commas = locale.replace("_", "-")
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_v2.journalist_app_base_url,
            web_driver=firefox_web_driver,
            accept_languages=locale_with_commas,
        )

        # Take a screenshot of trying to log in using invalid credentials several times
        for _ in range(6):
            journ_app_nav.journalist_logs_in(
                username="root",
                password="worse",
                otp_secret="2HGGVF5VPHWMCAYQ",
                is_login_expected_to_succeed=False,
            )
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-code-fail_login_many")
