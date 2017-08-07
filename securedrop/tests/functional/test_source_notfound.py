import source_navigation_steps
import functional_test
from step_helpers import screenshots


class TestSourceInterfaceBannerWarnings(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationSteps):

    @screenshots
    def test_not_found(self):
        self._source_not_found()
