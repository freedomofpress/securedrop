import functional_test
import journalist_navigation_steps

from functional_test import FunctionalHelper


def test_admin_interface(
        test_admin,
        live_source_app,
        live_journalist_app,
        webdriver):

    helper = FunctionalHelper(
        driver=webdriver,
        admin=test_admin,
        live_source_app=live_source_app,
        live_journalist_app=live_journalist_app)

    helper._admin_logs_in()
    helper._admin_visits_admin_interface()
    helper._admin_adds_a_user()
    helper._new_user_can_log_in()
    helper._admin_can_edit_new_user()


class TestAdminInterface(
        functional_test.FunctionalTest,
        journalist_navigation_steps.JournalistNavigationStepsMixin):


    def test_admin_edits_hotp_secret(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._admin_visits_edit_user()
        self._admin_visits_reset_2fa_hotp()
        self._admin_accepts_2fa_js_alert()

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
