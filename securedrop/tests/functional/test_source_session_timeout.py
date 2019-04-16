from . import source_navigation_steps
from . import functional_test


class TestSourceSessions(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin):

    def setup(self):
        # The session expiration here cannot be set to -1
        # as it will trigger an exception in /create.
        # Instead, we pick a 1-2s value to allow the account
        # to be generated.
        self.session_length_minutes = 0.03
        super(TestSourceSessions, self).setup(
            session_expiration=self.session_length_minutes)

    def test_source_session_timeout(self):
        self._source_visits_source_homepage()
        self._source_clicks_submit_documents_on_homepage()
        self._source_continues_to_submit_page()
        self._source_waits_for_session_to_timeout(
            self.session_length_minutes)
        self._source_visits_source_homepage()
        self._source_sees_session_timeout_message()
