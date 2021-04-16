# -*- coding: utf-8 -*-
from os.path import abspath, dirname, join, realpath
import pytest
import sys

# The tests directory should be adjacent to the securedrop directory. By adding
# the securedrop directory to sys.path here, all test modules are able to
# directly import modules in the securedrop directory.
sys.path.append(abspath(join(dirname(realpath(__file__)), '..', 'securedrop')))

# This ensures we get pytest's more detailed assertion output in helper functions
pytest.register_assert_rewrite('tests.functional.journalist_navigation_steps')
pytest.register_assert_rewrite('tests.functional.source_navigation_steps')
