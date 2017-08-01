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

    def test_admin_new_user_two_factor_hotp(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_creates_a_user(hotp='123456')
        self._screenshot('journalist-admin_new_user_two_factor_hotp.png')

    def test_admin_new_user_two_factor_totp(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_creates_a_user(hotp=None)
        self._screenshot('journalist-admin_new_user_two_factor_totp.png')

    def test_col_no_documents(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_delete_all()
        self._journalist_confirm_delete_all()
        self._screenshot('journalist-col_no_document.png')

    def test_col_has_no_key(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._source_delete_key()
        self._journalist_visits_col()
        self._screenshot('journalist-col_has_no_key.png')

    def test_col_flagged(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._source_delete_key()
        self._journalist_visits_col()
        self._journalist_flags_source()
        self._journalist_continues_after_flagging()
        self._screenshot('journalist-col_flagged.png')

    def test_col(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._screenshot('journalist-col.png')

    def test_col_javascript(self):
        self._javascript_toggle()
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._screenshot('journalist-col_javascript.png')

    def test_delete_none(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_delete_none()
        self._screenshot('journalist-delete_none.png')

    def test_delete_one_javascript(self):
        self._javascript_toggle()
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_selects_first_doc()
        self._journalist_clicks_delete_selected_javascript()
        self._save_alert('journalist-delete_one_javascript.txt')
        self._alert_accept()

    def test_delete_all_javascript(self):
        self._javascript_toggle()
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_delete_all_javascript()
        self._save_alert('journalist-delete_all_javascript.txt')
        self._alert_accept()

    def test_delete_one(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_delete_one()
        self._screenshot('journalist-delete_one.png')

    def test_delete_all(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_delete_all()
        self._screenshot('journalist-delete_all.png')

    def test_edit_account_user(self):
        self._journalist_logs_in()
        self._visit_edit_account()
        self._screenshot('journalist-edit_account_user.png')

    def test_edit_account_admin(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._admin_visits_edit_user()
        self._screenshot('journalist-edit_account_admin.png')

    def test_flag(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._source_delete_key()
        self._journalist_visits_col()
        self._journalist_flags_source()
        self._screenshot('journalist-flag.png')
