import source_navigation_steps
import journalist_navigation_steps
import functional_test


class TestSubmitAndRetrieveFile(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin,
        journalist_navigation_steps.JournalistNavigationStepsMixin):

    def test_submit_and_retrieve_happy_path(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self.swap_drivers()  # To use Firefox
        self._journalist_logs_in()
        self._journalist_checks_messages()
        self._journalist_stars_and_unstars_single_message()
        self._journalist_downloads_message()
        self._journalist_sends_reply_to_source()
        self.swap_drivers()  # To use Tor
        self._source_visits_source_homepage()
        self._source_chooses_to_login()
        self._source_proceeds_to_login()
        self._source_deletes_a_journalist_reply()

    def test_source_cancels_at_login_page(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_login()
        self._source_hits_cancel_at_login_page()

    def test_source_cancels_at_submit_page(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_hits_cancel_at_submit_page()
