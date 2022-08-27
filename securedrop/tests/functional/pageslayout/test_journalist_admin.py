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
import logging
import time
from pathlib import Path
from typing import Callable

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from tests.functional.app_navigators.journalist_app_nav import JournalistAppNavigator
from tests.functional.pageslayout.utils import list_locales, save_screenshot_and_html


@pytest.mark.parametrize("locale", list_locales())
@pytest.mark.pagelayout
class TestAdminLayoutAddAndEditUser:
    def test_admin_adds_user_hotp_and_edits_hotp(
        self, locale, sd_servers_with_clean_state, firefox_web_driver
    ):
        # Given an SD server
        # And a journalist logging into the journalist interface as an admin
        assert sd_servers_with_clean_state.journalist_is_admin
        locale_with_commas = locale.replace("_", "-")
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_clean_state.journalist_app_base_url,
            web_driver=firefox_web_driver,
            accept_languages=locale_with_commas,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_clean_state.journalist_username,
            password=sd_servers_with_clean_state.journalist_password,
            otp_secret=sd_servers_with_clean_state.journalist_otp_secret,
        )

        # Take a screenshot of the admin interface
        journ_app_nav.admin_visits_admin_interface()
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-admin_interface_index")

        # Take screenshots of the steps for creating an hotp journalist
        def screenshot_of_add_user_hotp_form() -> None:
            save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-admin_add_user_hotp")

        def screenshot_of_journalist_new_user_two_factor_hotp() -> None:
            save_screenshot_and_html(
                journ_app_nav.driver, locale, "journalist-admin_new_user_two_factor_hotp"
            )

        result = journ_app_nav.admin_creates_a_user(
            hotp_secret="c4 26 43 52 69 13 02 49 9f 6a a5 33 96 46 d9 05 42 a3 4f ae",
            callback_before_submitting_add_user_step=screenshot_of_add_user_hotp_form,
            callback_before_submitting_2fa_step=screenshot_of_journalist_new_user_two_factor_hotp,
        )
        new_user_username, new_user_pw, new_user_otp_secret = result
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-admin")

        # Take a screenshot of the new journalist's edit page
        journ_app_nav.admin_visits_user_edit_page(username_of_journalist_to_edit=new_user_username)
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-edit_account_admin")
        # The documentation uses an identical screenshot with a different name:
        # https://github.com/freedomofpress/securedrop-docs/blob/main/docs/images/manual
        # /screenshots/journalist-admin_edit_hotp_secret.png
        # So we take the same screenshot again here
        # TODO(AD): Update the documentation to use a single screenshot
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-admin_edit_hotp_secret")

        # Then the admin resets the new journalist's hotp
        def _admin_visits_reset_2fa_hotp_step() -> None:
            # 2FA reset buttons show a tooltip with explanatory text on hover.
            # Also, confirm the text on the tooltip is the correct one.
            hotp_reset_button = journ_app_nav.driver.find_elements_by_id("reset-two-factor-hotp")[0]
            hotp_reset_button.location_once_scrolled_into_view
            ActionChains(journ_app_nav.driver).move_to_element(hotp_reset_button).perform()

            time.sleep(1)

            tip_opacity = journ_app_nav.driver.find_elements_by_css_selector(
                "#button-reset-two-factor-hotp span.tooltip"
            )[0].value_of_css_property("opacity")
            tip_text = journ_app_nav.driver.find_elements_by_css_selector(
                "#button-reset-two-factor-hotp span.tooltip"
            )[0].text
            assert tip_opacity == "1"

            if not journ_app_nav.accept_languages:
                assert (
                    tip_text == "Reset two-factor authentication for security keys, like a YubiKey"
                )

            journ_app_nav.nav_helper.safe_click_by_id("button-reset-two-factor-hotp")

        # Run the above step in a retry loop
        self._retry_2fa_pop_ups(
            journ_app_nav, _admin_visits_reset_2fa_hotp_step, "reset-two-factor-hotp"
        )

        # Wait for it to succeed
        journ_app_nav.nav_helper.wait_for(
            lambda: journ_app_nav.driver.find_element_by_css_selector('input[name="otp_secret"]')
        )

    def test_admin_adds_user_totp_and_edits_totp(
        self, locale, sd_servers_with_clean_state, firefox_web_driver
    ):
        # Given an SD server
        # And a journalist logging into the journalist interface as an admin
        assert sd_servers_with_clean_state.journalist_is_admin
        locale_with_commas = locale.replace("_", "-")
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_clean_state.journalist_app_base_url,
            web_driver=firefox_web_driver,
            accept_languages=locale_with_commas,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_clean_state.journalist_username,
            password=sd_servers_with_clean_state.journalist_password,
            otp_secret=sd_servers_with_clean_state.journalist_otp_secret,
        )
        journ_app_nav.admin_visits_admin_interface()

        # Take screenshots of the steps for creating a totp journalist
        def screenshot_of_add_user_totp_form() -> None:
            save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-admin_add_user_totp")

        def screenshot_of_journalist_new_user_two_factor_totp() -> None:
            save_screenshot_and_html(
                journ_app_nav.driver, locale, "journalist-admin_new_user_two_factor_totp"
            )

        result = journ_app_nav.admin_creates_a_user(
            callback_before_submitting_add_user_step=screenshot_of_add_user_totp_form,
            callback_before_submitting_2fa_step=screenshot_of_journalist_new_user_two_factor_totp,
        )
        new_user_username, new_user_pw, new_user_otp_secret = result

        # Then the admin resets the second journalist's totp
        journ_app_nav.admin_visits_user_edit_page(username_of_journalist_to_edit=new_user_username)

        def _admin_visits_reset_2fa_totp_step() -> None:
            totp_reset_button = journ_app_nav.driver.find_elements_by_id("reset-two-factor-totp")[0]
            assert "/admin/reset-2fa-totp" in totp_reset_button.get_attribute("action")
            # 2FA reset buttons show a tooltip with explanatory text on hover.
            # Also, confirm the text on the tooltip is the correct one.
            totp_reset_button = journ_app_nav.driver.find_elements_by_css_selector(
                "#button-reset-two-factor-totp"
            )[0]
            totp_reset_button.location_once_scrolled_into_view
            ActionChains(journ_app_nav.driver).move_to_element(totp_reset_button).perform()

            time.sleep(1)

            tip_opacity = journ_app_nav.driver.find_elements_by_css_selector(
                "#button-reset-two-factor-totp span.tooltip"
            )[0].value_of_css_property("opacity")
            tip_text = journ_app_nav.driver.find_elements_by_css_selector(
                "#button-reset-two-factor-totp span.tooltip"
            )[0].text

            assert tip_opacity == "1"
            if not journ_app_nav.accept_languages:
                expected_text = "Reset two-factor authentication for mobile apps, such as FreeOTP"
                assert tip_text == expected_text

            journ_app_nav.nav_helper.safe_click_by_id("button-reset-two-factor-totp")

        # Run the above step in a retry loop
        self._retry_2fa_pop_ups(
            journ_app_nav, _admin_visits_reset_2fa_totp_step, "reset-two-factor-totp"
        )

        # Then it succeeds
        # Take a screenshot
        save_screenshot_and_html(journ_app_nav.driver, locale, "journalist-admin_edit_totp_secret")

    @staticmethod
    def _retry_2fa_pop_ups(
        journ_app_nav: JournalistAppNavigator, navigation_step: Callable, button_to_click: str
    ) -> None:
        """Clicking on Selenium alerts can be flaky. We need to retry them if they timeout."""
        for i in range(15):
            try:
                try:
                    # This is the button we click to trigger the alert.
                    journ_app_nav.nav_helper.wait_for(
                        lambda: journ_app_nav.driver.find_elements_by_id(button_to_click)[0]
                    )
                except IndexError:
                    # If the button isn't there, then the alert is up from the last
                    # time we attempted to run this test. Switch to it and accept it.
                    journ_app_nav.nav_helper.alert_wait()
                    journ_app_nav.nav_helper.alert_accept()
                    break

                # The alert isn't up. Run the rest of the logic.
                navigation_step()

                journ_app_nav.nav_helper.alert_wait()
                journ_app_nav.nav_helper.alert_accept()
                break
            except TimeoutException:
                # Selenium has failed to click, and the confirmation
                # alert didn't happen. We'll try again.
                logging.info("Selenium has failed to click; retrying.")


@pytest.mark.parametrize("locale", list_locales())
@pytest.mark.pagelayout
class TestAdminLayoutEditConfig:
    def test_admin_changes_logo(self, locale, sd_servers_with_clean_state, firefox_web_driver):
        # Given an SD server
        # And a journalist logging into the journalist interface as an admin
        assert sd_servers_with_clean_state.journalist_is_admin
        locale_with_commas = locale.replace("_", "-")
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_clean_state.journalist_app_base_url,
            web_driver=firefox_web_driver,
            accept_languages=locale_with_commas,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_clean_state.journalist_username,
            password=sd_servers_with_clean_state.journalist_password,
            otp_secret=sd_servers_with_clean_state.journalist_otp_secret,
        )

        # Take a screenshot of the system config page
        journ_app_nav.admin_visits_admin_interface()
        journ_app_nav.admin_visits_system_config_page()
        save_screenshot_and_html(
            journ_app_nav.driver, locale, "journalist-admin_system_config_page"
        )

        # When the admin tries to upload a new logo
        current_file_path = Path(__file__).absolute().parent
        logo_path = current_file_path / ".." / ".." / ".." / "static" / "i" / "logo.png"
        assert logo_path.is_file()
        journ_app_nav.nav_helper.safe_send_keys_by_id("logo-upload", str(logo_path))
        journ_app_nav.nav_helper.safe_click_by_id("submit-logo-update")

        # Then it succeeds
        def updated_image() -> None:
            flash_msg = journ_app_nav.driver.find_element_by_css_selector(".flash")
            assert "Image updated." in flash_msg.text

        journ_app_nav.nav_helper.wait_for(updated_image, timeout=20)

        # Take a screenshot
        save_screenshot_and_html(
            journ_app_nav.driver, locale, "journalist-admin_changes_logo_image"
        )

    def test_ossec_alert_button(self, locale, sd_servers, firefox_web_driver):
        # Given an SD server
        # And a journalist logging into the journalist interface as an admin
        assert sd_servers.journalist_is_admin
        locale_with_commas = locale.replace("_", "-")
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers.journalist_app_base_url,
            web_driver=firefox_web_driver,
            accept_languages=locale_with_commas,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers.journalist_username,
            password=sd_servers.journalist_password,
            otp_secret=sd_servers.journalist_otp_secret,
        )
        # And they go to the admin config page
        journ_app_nav.admin_visits_admin_interface()
        journ_app_nav.admin_visits_system_config_page()

        # When they try to send an OSSEC alert
        alert_button = journ_app_nav.driver.find_element_by_id("test-ossec-alert")
        alert_button.click()

        # Then it succeeds
        def test_alert_sent():
            flash_msg = journ_app_nav.driver.find_element_by_css_selector(".flash")
            assert "Test alert sent. Please check your email." in flash_msg.text

        journ_app_nav.nav_helper.wait_for(test_alert_sent)

        # Take a screenshot
        save_screenshot_and_html(
            journ_app_nav.driver, locale, "journalist-admin_ossec_alert_button"
        )
