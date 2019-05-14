#
# SecureDrop whistleblower submission system
# Copyright (C) 2017 Loic Dachary <loic@dachary.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import logging
import os
from os.path import abspath
from os.path import dirname
from os.path import realpath

import pytest

from tests.functional import functional_test


def list_locales():
    if "PAGE_LAYOUT_LOCALES" in os.environ:
        locales = os.environ["PAGE_LAYOUT_LOCALES"].split(",")
    else:
        locales = ["en_US"]
    return locales


class FunctionalTest(functional_test.FunctionalTest):
    @pytest.fixture(autouse=True, params=list_locales())
    def i18n_fixture(self, request):
        logging.debug("i18n_fixture: setting accept_languages to '%s'", request.param)
        self.accept_languages = request.param

    @pytest.fixture(autouse=True)
    def use_firefox(self):
        self.switch_to_firefox_driver()

    def _screenshot(self, filename):
        log_dir = abspath(
            os.path.join(dirname(realpath(__file__)), "screenshots", self.accept_languages)
        )
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.driver.save_screenshot(os.path.join(log_dir, filename))
