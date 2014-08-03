import functional_test
import source_navigation_steps
import journalist_navigation_steps
import unittest
import urllib2

class SubmitAndRetrieveMessage(
        unittest.TestCase,
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationSteps,
        journalist_navigation_steps.JournalistNavigationSteps):

    def setUp(self):
        functional_test.FunctionalTest.setUp(self)

    def tearDown(self):
        functional_test.FunctionalTest.tearDown(self)

    def test_submit_and_retrieve_happy_path(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_message()
        self._journalist_checks_messages()
        self._journalist_downloads_message()

if __name__ == "__main__":
    unittest.main(verbosity=2)
