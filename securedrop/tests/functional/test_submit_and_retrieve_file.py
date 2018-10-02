import source_navigation_steps
import journalist_navigation_steps
import functional_test


class TestSubmitAndRetrieveFile(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin,
        journalist_navigation_steps.JournalistNavigationStepsMixin):


    def test_source_cancels_at_submit_page(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_hits_cancel_at_submit_page()
