# -*- coding: utf-8 -*-
from os.path import abspath, dirname, join, realpath
import sys

# The tests directory should be adjacent to the securedrop directory. By adding
# the securedrop directory to sys.path here, all test modules are able to
# directly import modules in the securedrop directory.
sys.path.append(abspath(join(dirname(realpath(__file__)), '..', 'securedrop')))
