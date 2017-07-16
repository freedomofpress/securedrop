import unittest

import source_navigation_steps
import functional_test


class SourceInterfaceBannerWarnings(
        unittest.TestCase,
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationSteps):

    def setUp(self):
        functional_test.FunctionalTest.setUp(self)

    def tearDown(self):
        functional_test.FunctionalTest.tearDown(self)

    def test_not_found(self):
        self._source_not_found()
