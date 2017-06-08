from selenium import webdriver
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

    def test_warning_appears_if_tor_browser_not_in_use(self):
        self.driver.get(self.source_location)

        warning_banner = self.driver.find_element_by_class_name('use-tor-browser')

        self.assertIn("We recommend using Tor Browser to access SecureDrop",
                      warning_banner.text)
