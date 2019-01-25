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
import pytest
import time


@pytest.mark.pagelayout
class TestJournalistLayout(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin,
        journalist_navigation_steps.JournalistNavigationStepsMixin):

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

    def test_admin_add_user_hotp(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_visits_add_user()
        self._admin_enters_journalist_account_details_hotp(
            'journalist2',
            'c4 26 43 52 69 13 02 49 9f 6a a5 33 96 46 d9 05 42 a3 4f ae'
        )
        self._screenshot('journalist-admin_add_user_hotp.png')

    def test_admin_add_user_totp(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_visits_add_user()
        self._screenshot('journalist-admin_add_user_totp.png')

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
        valid_hotp = '1234567890123456789012345678901234567890'
        self._admin_creates_a_user(hotp=valid_hotp)
        self._screenshot('journalist-admin_new_user_two_factor_hotp.png')

    def test_admin_new_user_two_factor_totp(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_creates_a_user(hotp=None)
        self._screenshot('journalist-admin_new_user_two_factor_totp.png')

    def test_admin_changes_logo(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_visits_system_config_page()
        self._screenshot('journalist-admin_system_config_page.png')
        self._admin_updates_logo_image()
        self._screenshot('journalist-admin_changes_logo_image.png')

    def test_col_no_documents(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_delete_all()
        self._journalist_confirm_delete_selected()
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

    def test_journalist_composes_reply(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_checks_messages()
        self._journalist_downloads_message()
        self._journalist_composes_reply()
        self._screenshot('journalist-composes_reply.png')

    def test_admin_uses_ossec_alert_button(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_visits_system_config_page()
        self._admin_can_send_test_alert()
        self._screenshot('journalist-admin_ossec_alert_button.png')

    def test_delete_none(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_clicks_delete_selected_link()
        self._journalist_confirm_delete_selected()
        self._screenshot('journalist-delete_none.png')

    def test_delete_one_confirmation(self):
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
        self._journalist_clicks_delete_selected_link()
        time.sleep(1)
        self._screenshot('journalist-delete_one_confirmation.png')

    def test_delete_all_confirmation(self):
        self._javascript_toggle()
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_delete_all_confirmation()
        time.sleep(1)
        self._screenshot('journalist-delete_all_confirmation.png')

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
        self._journalist_confirm_delete_selected()
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
        self._journalist_confirm_delete_selected()
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

    def test_index_no_documents_admin(self):
        self._admin_logs_in()
        self._screenshot('journalist-admin_index_no_documents.png')

    def test_admin_interface_index(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._screenshot('journalist-admin_interface_index.png')

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

    def test_index_no_documents(self):
        self._journalist_logs_in()
        self._screenshot('journalist-index_no_documents.png')

    def test_index(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._screenshot('journalist-index.png')

    def test_index_javascript(self):
        self._javascript_toggle()
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._screenshot('journalist-index_javascript.png')
        self._journalist_selects_the_first_source()
        self._journalist_selects_documents_to_download()
        self._screenshot(
            'journalist-clicks_on_source_and_selects_documents.png'
        )

    def test_index_entered_text(self):
        self._input_text_in_login_form('jane_doe', 'my password is long',
                                       '117264')
        self._screenshot('journalist-index_with_text.png')

    def test_fail_to_visit_admin(self):
        self._journalist_visits_admin()
        self._screenshot('journalist-code-fail_to_visit_admin.png')

    def test_fail_login(self, hardening):
        self._journalist_fail_login()
        self._screenshot('journalist-code-fail_login.png')

    def test_fail_login_many(self, hardening):
        self._journalist_fail_login_many()
        self._screenshot('journalist-code-fail_login_many.png')
