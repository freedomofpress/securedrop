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
from os.path import abspath, dirname, realpath, join
import pytest

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

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
        firefox = self._prepare_webdriver()
        profile = webdriver.FirefoxProfile()
        profile.set_preference("intl.accept_languages", self.accept_languages)
        self.override_driver = True
        self.driver = self._create_webdriver(firefox, profile)
        self._javascript_toggle()

        yield None

        self.driver.quit()

    def _screenshot(self, filename):
        self.driver.set_window_size(1024, 500)  # Trim size of images for docs
        path = os.path.join(self.log_dir, filename)
        self.driver.save_screenshot(path)
        # save the l10n strings used by the last request
        source_strings_path = abspath(join(dirname(realpath(__file__)),
                                           '..', 'log', 'source_strings.json'))
        if os.path.exists(source_strings_path):
            l10n_filename = os.path.splitext(filename)[0] + ".json"
            l10n_path = os.path.join(self.log_dir, l10n_filename)
            os.rename(source_strings_path, l10n_path)

    def _javascript_toggle(self):
        # the following is a noop for some reason, workaround it
        # profile.set_preference("javascript.enabled", False)
        # https://stackoverflow.com/a/36782979/837471
        self.driver.get("about:config")
        actions = ActionChains(self.driver)
        actions.send_keys(Keys.RETURN)
        actions.send_keys("javascript.enabled")
        actions.perform()
        actions.send_keys(Keys.TAB)
        actions.send_keys(Keys.RETURN)
        actions.perform()

    def _save_alert(self, filename):
        fd = open(os.path.join(self.log_dir, filename), 'wb')
        fd.write(self.driver.switch_to.alert.text.encode('utf-8'))
