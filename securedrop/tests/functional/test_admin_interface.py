from . import functional_test as ft
from . import journalist_navigation_steps
from . import source_navigation_steps


class TestAdminInterface(
        ft.FunctionalTest,
        journalist_navigation_steps.JournalistNavigationStepsMixin,
        source_navigation_steps.SourceNavigationStepsMixin):

    def test_admin_interface(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._new_user_can_log_in()
        self._admin_can_edit_new_user()

    def test_admin_edit_invalid_username(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._new_user_can_log_in()
        self._admin_editing_invalid_username()

    def test_admin_edits_hotp_secret(self):
        # Toggle security slider to force prefs change
        self.set_tbb_securitylevel(ft.TBB_SECURITY_HIGH)
        self.set_tbb_securitylevel(ft.TBB_SECURITY_LOW)

        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._admin_visits_edit_user()
        self._admin_visits_reset_2fa_hotp()
        self._admin_visits_edit_hotp()

    def test_admin_edits_totp_secret(self):
        # Toggle security slider to force prefs change
        self.set_tbb_securitylevel(ft.TBB_SECURITY_HIGH)
        self.set_tbb_securitylevel(ft.TBB_SECURITY_LOW)

        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._admin_visits_edit_user()
        self._admin_visits_reset_2fa_totp()

    def test_admin_deletes_user(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._admin_deletes_user()

    def test_admin_updates_image(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_visits_system_config_page()
        self._admin_updates_logo_image()

    def test_ossec_alert_button(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_visits_system_config_page()
        self._admin_can_send_test_alert()

    def test_admin_adds_user_with_invalid_username(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        # Add an user with invalid username
        self._admin_adds_a_user_with_invalid_username()

    def test_admin_adds_admin_user(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        # Add an admin user
        self._admin_adds_a_user(is_admin=True)
        self._new_admin_user_can_log_in()
        self._admin_can_edit_new_user()

    def test_disallow_file_submission(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_visits_system_config_page()
        self._admin_disallows_document_uploads()

        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_does_not_sees_document_attachment_item()

    def test_allow_file_submission(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_visits_system_config_page()
        self._admin_disallows_document_uploads()
        self._admin_allows_document_uploads()

        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_sees_document_attachment_item()
