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
from datetime import datetime
import os
from os.path import abspath, dirname, realpath
import pytest

from selenium import webdriver
from selenium.webdriver.firefox import firefox_binary

from tests.functional import functional_test


def list_locales():
    d = os.path.join(dirname(__file__), '..', '..', 'translations')
    locales = ['en_US']
    if os.path.isdir(d):
        files = os.listdir(d)
        locales.extend([f for f in files if f != 'messages.pot'])
    return locales


class FunctionalTest(functional_test.FunctionalTest):

    @pytest.fixture(autouse=True, params=list_locales())
    def webdriver_fixture(self, request):
        self.accept_languages = request.param
        self.log_dir = abspath(
            os.path.join(dirname(realpath(__file__)),
                         'screenshots', self.accept_languages))
        os.system("mkdir -p " + self.log_dir)
        log_file = open(os.path.join(self.log_dir, 'firefox.log'), 'a')
        log_file.write(
            '\n\n[%s] Running Functional Tests\n' % str(
                datetime.now()))
        log_file.flush()
        firefox = firefox_binary.FirefoxBinary(log_file=log_file)
        profile = webdriver.FirefoxProfile()
        profile.set_preference("intl.accept_languages", self.accept_languages)
        self.override_driver = True
        self.driver = webdriver.Firefox(firefox_binary=firefox,
                                        firefox_profile=profile)
        yield None

        self.driver.quit()

    def _screenshot(self, filename):
        self.driver.save_screenshot(os.path.join(self.log_dir, filename))
