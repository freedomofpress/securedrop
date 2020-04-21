from . import source_navigation_steps
from . import functional_test


class TestSourceSessions(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin):

    session_expiration = 5

    def test_source_session_timeout(self):
        self._source_visits_source_homepage()
        self._source_clicks_submit_documents_on_homepage()
        self._source_continues_to_submit_page()
        self._source_waits_for_session_to_timeout()
        self.driver.refresh()
        self._source_sees_session_timeout_message()
