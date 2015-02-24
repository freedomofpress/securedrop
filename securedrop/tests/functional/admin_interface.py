import functional_test
import journalist_navigation_steps
import unittest


class AdminInterface(
        unittest.TestCase,
        functional_test.FunctionalTest,
        journalist_navigation_steps.JournalistNavigationSteps):

    def setUp(self):
        functional_test.FunctionalTest.setUp(self)

    def tearDown(self):
        functional_test.FunctionalTest.tearDown(self)

    def test_admin_interface(self):
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        self._new_user_can_log_in()
        self._admin_can_edit_new_user()

if __name__ == "__main__":
    unittest.main(verbosity=2)
