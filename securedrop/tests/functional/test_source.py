import source_navigation_steps
import functional_test


class TestSourceInterfaceBannerWarnings(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationSteps):

    def test_lookup_codename_hint(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_shows_codename()
        self._source_hides_codename()
