import functional_test
import journalist_navigation_steps
import source_navigation_steps
import unittest


class TagTest(
        unittest.TestCase,
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationSteps,
        journalist_navigation_steps.JournalistNavigationSteps):

    def setUp(self):
        functional_test.FunctionalTest.setUp(self)

    def tearDown(self):
        functional_test.FunctionalTest.tearDown(self)

    def test_admin_can_add_and_remove_label_types(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_can_add_source_label_type()
        self._admin_can_remove_source_label_type()
        self._admin_can_add_submission_label_type()
        self._admin_can_remove_submission_label_type()

    def test_journalist_can_add_and_remove_labels(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_can_add_source_label_type()
        self._admin_can_add_submission_label_type()
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_checks_messages()
        self._journalist_downloads_message()
        self._journalist_can_add_source_tag()
        self._journalist_can_add_and_remove_submission_tag()
        self._journalist_can_remove_source_tag()

    def test_journalist_can_filter_by_labels(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_can_add_source_label_type()
        self._admin_can_add_submission_label_type()
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_checks_messages()
        self._journalist_downloads_message()
        self._journalist_can_add_source_tag()
        self._journalist_can_filter_by_source_tag()


if __name__ == "__main__":
    unittest.main(verbosity=2)
