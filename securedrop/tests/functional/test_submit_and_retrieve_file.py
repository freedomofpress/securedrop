import source_navigation_steps
import journalist_navigation_steps
import functional_test
from step_helpers import screenshots
import time


class TestSubmitAndRetrieveFile(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationSteps,
        journalist_navigation_steps.JournalistNavigationSteps):

    @screenshots
    def test_submit_and_retrieve_happy_path(self):
        d = time.time()
        self._source_visits_source_homepage()
        print time.time()-d, "self._source_visits_source_homepage()"
        d = time.time()
        self._source_chooses_to_submit_documents()
        print time.time()-d, "self._source_chooses_to_submit_documents()"
        d = time.time()
        self._source_continues_to_submit_page()
        print time.time()-d, "self._source_continues_to_submit_page()"
        d = time.time()
        self._source_submits_a_file()
        print time.time()-d, "self._source_submits_a_file()"
        d = time.time()
        self._source_logs_out()
        print time.time()-d, "self._source_logs_out()"
        d = time.time()
        self._journalist_logs_in()
        print time.time()-d, "self._journalist_logs_in()"
        d = time.time()
        self._journalist_checks_messages()
        print time.time()-d, "self._journalist_checks_messages()"
        d = time.time()
        self._journalist_stars_and_unstars_single_message()
        print time.time()-d, "self._journalist_stars_and_unstars_single_message()"
        d = time.time()
        self._journalist_selects_all_sources_then_selects_none()
        print time.time()-d, "self._journalist_selects_all_sources_then_selects_none()"
        d = time.time()
        self._journalist_downloads_message()
        print time.time()-d, "self._journalist_downloads_message()"
        d = time.time()
        self._journalist_sends_reply_to_source()
        print time.time()-d, "self._journalist_sends_reply_to_source()"
        d = time.time()
        self._source_visits_source_homepage()
        print time.time()-d, "self._source_visits_source_homepage()"
        d = time.time()
        self._source_chooses_to_login()
        print time.time()-d, "self._source_chooses_to_login()"
        d = time.time()
        self._source_proceeds_to_login()
        print time.time()-d, "self._source_proceeds_to_login()"
        d = time.time()
        self._source_deletes_a_journalist_reply()
        print time.time()-d, "self._source_deletes_a_journalist_reply()"

    @screenshots
    def test_source_cancels_at_login_page(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_login()
        self._source_hits_cancel_at_login_page()

    @screenshots
    def test_source_cancels_at_submit_page(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_hits_cancel_at_submit_page()
