from . import source_navigation_steps
from . import functional_test


class TestSourceInterface(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin):

    def test_lookup_codename_hint(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_shows_codename()
        self._source_hides_codename()
        self._source_logs_out()
        self._source_visits_source_homepage()
        self._source_chooses_to_login()
        self._source_proceeds_to_login()
        self._source_sees_no_codename()
