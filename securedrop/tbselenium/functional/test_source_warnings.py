import source_navigation_steps
import functional_test


class TestSourceInterfaceBannerWarnings(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin):

    def test_warning_appears_if_tor_browser_not_in_use(self):
        self.swap_drivers()
        self.driver.get(self.source_location)

        warning_banner = self.driver.find_element_by_class_name(
            'use-tor-browser')

        assert ("We recommend using Tor Browser to access SecureDrop" in
                warning_banner.text)
        # User should be able to dismiss the warning
        warning_dismiss_button = self.driver.find_element_by_id(
            'use-tor-browser-close')
        warning_dismiss_button.click()

        def warning_banner_is_hidden():
            assert warning_banner.is_displayed() is False
        self.wait_for(warning_banner_is_hidden)
        self.swap_drivers()



    def test_warning_high_security(self):
        self.driver.get(self.source_location)

        banner = self.driver.find_element_by_class_name('js-warning')
        assert "Security Slider to High", banner.text
