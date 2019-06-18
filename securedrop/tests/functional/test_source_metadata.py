from . import source_navigation_steps
from . import functional_test


class TestInstanceMetadata(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin):

    def test_instance_metadata(self):
        self._source_checks_instance_metadata()
