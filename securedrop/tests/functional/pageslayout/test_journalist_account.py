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
from typing import Optional

import pytest
from selenium.webdriver import ActionChains
from tests.functional.app_navigators.journalist_app_nav import JournalistAppNavigator
from tests.functional.pageslayout.utils import list_locales, save_screenshot_and_html


@pytest.mark.parametrize("locale", list_locales())
@pytest.mark.pagelayout
class TestJournalistLayoutAccount:
    def test_account_edit_and_set_hotp_secret(
        self, locale, sd_servers_with_clean_state, firefox_web_driver
    ):
        # Given an SD server
        # And a journalist logging into the journalist interface
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

        # And the journalist went to the edit account page
        journ_app_nav.journalist_visits_edit_account()

        # Take a screenshot of the edit hotp page
        self._clicks_reset_secret(
            journ_app_nav, "hotp", assert_tooltip_text_is="RESET SECURITY KEY CREDENTIALS"
        )
        save_screenshot_and_html(
            journ_app_nav.driver, locale, "journalist-account_edit_hotp_secret"
        )

        # Update the hotp secret and take a screenshot
        journ_app_nav.nav_helper.safe_send_keys_by_css_selector(
            'input[name="otp_secret"]', "123456"
        )
        journ_app_nav.nav_helper.safe_click_by_css_selector("button[type=submit]")
        save_screenshot_and_html(
            journ_app_nav.driver, locale, "journalist-account_new_two_factor_hotp"
        )

    @staticmethod
    def _clicks_reset_secret(
        journ_app_nav: JournalistAppNavigator, otp_type: str, assert_tooltip_text_is: Optional[str]
    ) -> None:
        reset_form = journ_app_nav.nav_helper.wait_for(
            lambda: journ_app_nav.driver.find_element_by_id(f"reset-two-factor-{otp_type}")
        )
        assert f"/account/reset-2fa-{otp_type}" in reset_form.get_attribute("action")
        reset_button = journ_app_nav.driver.find_elements_by_css_selector(
            f"#button-reset-two-factor-{otp_type}"
        )[0]

        # 2FA reset buttons show a tooltip with explanatory text on hover.
        # Also, confirm the text on the tooltip is the correct one.
        reset_button.location_once_scrolled_into_view
        ActionChains(journ_app_nav.driver).move_to_element(reset_button).perform()

        def explanatory_tooltip_is_correct() -> None:
            explanatory_tooltip = journ_app_nav.driver.find_element_by_css_selector(
                f"#button-reset-two-factor-{otp_type} span"
            )

            explanatory_tooltip_opacity = explanatory_tooltip.value_of_css_property("opacity")
            assert explanatory_tooltip_opacity == "1"

            if assert_tooltip_text_is:
                assert explanatory_tooltip.text == assert_tooltip_text_is

        journ_app_nav.nav_helper.wait_for(explanatory_tooltip_is_correct)

        reset_form.submit()

        alert = journ_app_nav.driver.switch_to_alert()
        alert.accept()

    def test_account_new_two_factor_totp(
        self, locale, sd_servers_with_clean_state, firefox_web_driver
    ):
        # Given an SD server
        # And a journalist logging into the journalist interface
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

        # And the journalist went to the edit account page
        journ_app_nav.journalist_visits_edit_account()

        # Take a screenshot of the edit totp page
        self._clicks_reset_secret(
            journ_app_nav, "totp", assert_tooltip_text_is="RESET MOBILE APP CREDENTIALS"
        )
        save_screenshot_and_html(
            journ_app_nav.driver, locale, "journalist-account_new_two_factor_totp"
        )
