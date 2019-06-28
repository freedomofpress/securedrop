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
    default_driver_name = functional_test.FIREFOX

    @pytest.fixture(autouse=True, params=list_locales())
    def set_accept_languages(self, request):
        accept_language_list = request.param.replace("_", "-")
        logging.debug(
            "accept_languages fixture: setting accept_languages to %s", accept_language_list
        )
        self.accept_languages = accept_language_list

    def _screenshot(self, filename):
        # revert the HTTP Accept-Language format
        locale = self.accept_languages.replace("-", "_")

        log_dir = abspath(
            os.path.join(dirname(realpath(__file__)), "screenshots", locale)
        )
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.driver.save_screenshot(os.path.join(log_dir, filename))
