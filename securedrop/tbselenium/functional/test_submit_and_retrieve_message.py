import functional_test
import source_navigation_steps
import journalist_navigation_steps


class TestSubmitAndRetrieveMessage(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin,
        journalist_navigation_steps.JournalistNavigationStepsMixin):

    def test_submit_and_retrieve_happy_path(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_message()
        self._source_logs_out()
        self.swap_drivers()  # To use Firefox
        self._journalist_logs_in()
        self._journalist_checks_messages()
        self._journalist_downloads_message()
