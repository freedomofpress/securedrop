import source_navigation_steps
import functional_test


class TestSourceInterfaceBannerWarnings(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin):

    def test_warning_appears_if_tor_browser_not_in_use(self):
        self.driver.get(self.source_location)

        warning_banner = self.driver.find_element_by_class_name(
            'use-tor-browser')

        assert ("We recommend using Tor Browser to access SecureDrop" in
                warning_banner.text)
