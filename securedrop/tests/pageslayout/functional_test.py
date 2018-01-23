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
import os
import io
from os.path import abspath, dirname, realpath
import pytest

from selenium import webdriver

from tests.functional import functional_test


def list_locales():
    if 'PAGE_LAYOUT_LOCALES' in os.environ:
        locales = os.environ['PAGE_LAYOUT_LOCALES'].split(',')
    else:
        locales = ['en_US']
    return locales


class FunctionalTest(functional_test.FunctionalTest):

    @pytest.fixture(autouse=True, params=list_locales())
    def webdriver_fixture(self, request):
        self.accept_languages = request.param
        self.log_dir = abspath(
            os.path.join(dirname(realpath(__file__)),
                         'screenshots', self.accept_languages))
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.new_profile = webdriver.FirefoxProfile()
        self.new_profile.set_preference("intl.accept_languages",
                                        self.accept_languages)
        self.override_driver = True
        yield None

    def _screenshot(self, filename):
        self.driver.save_screenshot(os.path.join(self.log_dir, filename))

    def _save_alert(self, filename):
        fd = io.open(os.path.join(self.log_dir, filename), 'wb')
        fd.write(self.driver.switch_to.alert.text.encode('utf-8'))
