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
from tests.functional import journalist_navigation_steps
from tests.functional import source_navigation_steps
import functional_test

class TestJournalistLayout(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationSteps,
        journalist_navigation_steps.JournalistNavigationSteps):

    def test_account_edit_hotp_secret(self):
        self._journalist_logs_in()
        self._visit_edit_account()
        self._visit_edit_hotp_secret()
        self._screenshot('journalist-account_edit_hotp_secret.png')

    def test_account_new_two_factor_hotp(self):
        self._journalist_logs_in()
        self._visit_edit_account()
        self._visit_edit_hotp_secret()
        self._set_hotp_secret()
        self._screenshot('journalist-account_new_two_factor_hotp.png')

    def test_account_new_two_factor_totp(self):
        self._journalist_logs_in()
        self._visit_edit_account()
        self._visit_edit_totp_secret()
        self._screenshot('journalist-account_new_two_factor_totp.png')

    def test_admin_add_user(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_visits_add_user()
        self._screenshot('journalist-admin_add_user.png')

    def test_admin_edit_hotp_secret(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._admin_visits_edit_user()
        self._admin_visits_reset_2fa_hotp()
        self._screenshot('journalist-admin_edit_hotp_secret.png')

    def test_admin_edit_totp_secret(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._admin_visits_edit_user()
        self._admin_visits_reset_2fa_totp()
        self._screenshot('journalist-admin_edit_totp_secret.png')

    def test_login(self):
        self.driver.get(self.journalist_location + "/login")
        self._screenshot('journalist-login.png')

    def test_admin(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._screenshot('journalist-admin.png')
