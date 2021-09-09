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

from tests.functional import journalist_navigation_steps
from tests.functional import source_navigation_steps
import tests.pageslayout.functional_test as pft


@pytest.mark.pagelayout
class TestJournalistLayoutAdmin(
        pft.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin,
        journalist_navigation_steps.JournalistNavigationStepsMixin):

    def test_admin_add_user_hotp(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_visits_add_user()
        self._admin_enters_journalist_account_details_hotp(
            'journalist2',
            'c4 26 43 52 69 13 02 49 9f 6a a5 33 96 46 d9 05 42 a3 4f ae'
        )
        self._screenshot('journalist-admin_add_user_hotp.png')
        self._save_html('journalist-admin_add_user_hotp.html')

    def test_admin_add_user_totp(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_visits_add_user()
        self._screenshot('journalist-admin_add_user_totp.png')
        self._save_html('journalist-admin_add_user_totp.html')

    def test_admin_edit_hotp_secret(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._admin_visits_edit_user()
        self._admin_visits_reset_2fa_hotp()
        self._screenshot('journalist-admin_edit_hotp_secret.png')
        self._save_html('journalist-admin_edit_hotp_secret.html')

    def test_admin_edit_totp_secret(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._admin_visits_edit_user()
        self._admin_visits_reset_2fa_totp()
        self._screenshot('journalist-admin_edit_totp_secret.png')
        self._save_html('journalist-admin_edit_totp_secret.html')

    def test_edit_account_admin(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._admin_visits_edit_user()
        self._screenshot('journalist-edit_account_admin.png')
        self._save_html('journalist-edit_account_admin.html')

    def test_admin(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._screenshot('journalist-admin.png')
        self._save_html('journalist-admin.html')

    def test_admin_new_user_two_factor_hotp(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        valid_hotp = '1234567890123456789012345678901234567890'
        self._admin_creates_a_user(hotp=valid_hotp)
        self._screenshot('journalist-admin_new_user_two_factor_hotp.png')
        self._save_html('journalist-admin_new_user_two_factor_hotp.html')

    def test_admin_new_user_two_factor_totp(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_creates_a_user(hotp=None)
        self._screenshot('journalist-admin_new_user_two_factor_totp.png')
        self._save_html('journalist-admin_new_user_two_factor_totp.html')

    def test_admin_changes_logo(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_visits_system_config_page()
        self._screenshot('journalist-admin_system_config_page.png')
        self._save_html('journalist-admin_system_config_page.html')
        self._admin_updates_logo_image()
        self._screenshot('journalist-admin_changes_logo_image.png')
        self._save_html('journalist-admin_changes_logo_image.html')

    def test_admin_uses_ossec_alert_button(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_visits_system_config_page()
        self._admin_can_send_test_alert()
        self._screenshot('journalist-admin_ossec_alert_button.png')
        self._save_html('journalist-admin_ossec_alert_button.html')

    def test_admin_interface_index(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._screenshot('journalist-admin_interface_index.png')
        self._save_html('journalist-admin_interface_index.html')
