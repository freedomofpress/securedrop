from . import source_navigation_steps
from . import functional_test


class TestSourceInterfaceNotFound(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin):

    def test_not_found(self):
        self._source_not_found()
