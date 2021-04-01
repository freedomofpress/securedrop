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
import io
import logging
import os
from os.path import abspath
from os.path import dirname
from os.path import realpath

import pytest

from tests.functional import functional_test

from PIL import Image


def list_locales():
    if "TEST_LOCALES" in os.environ:
        locales = os.environ["TEST_LOCALES"].split()
    else:
        locales = ["en_US"]
    return locales


def autocrop_btm(img, bottom_padding=12):
    """Automatically crop the bottom of a screenshot."""
    # Get the grayscale of img
    gray = img.convert('L')
    # We start one row above the bottom since the "modal" windows screenshots
    # have a bottom line color different than the background
    btm = img.height - 2
    # Get the background luminance value from the bottom-leftmost pixel
    bg = gray.getpixel((0, btm))

    # Move up until the full row is not of the background luminance
    while all([gray.getpixel((col, btm)) == bg for col in range(gray.width)]):
        btm -= 1

    btm = min(btm + bottom_padding, img.height)

    return img.crop((0, 0, img.width, btm))


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

        img = Image.open(io.BytesIO(self.driver.get_screenshot_as_png()))
        cropped = autocrop_btm(img)
        cropped.save(os.path.join(log_dir, filename))
