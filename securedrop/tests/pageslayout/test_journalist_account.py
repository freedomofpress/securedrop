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
import pytest

from tests.functional import journalist_navigation_steps
from tests.functional import source_navigation_steps
import tests.pageslayout.functional_test as pft


@pytest.mark.pagelayout
class TestJournalistLayoutAccount(
        pft.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin,
        journalist_navigation_steps.JournalistNavigationStepsMixin):

    def test_account_edit_hotp_secret(self):
        self._journalist_logs_in()
        self._visit_edit_account()
        self._visit_edit_hotp_secret()
        self._screenshot('journalist-account_edit_hotp_secret.png')
        self._save_html('journalist-account_edit_hotp_secret.html')

    def test_account_new_two_factor_hotp(self):
        self._journalist_logs_in()
        self._visit_edit_account()
        self._visit_edit_hotp_secret()
        self._set_hotp_secret()
        self._screenshot('journalist-account_new_two_factor_hotp.png')
        self._save_html('journalist-account_new_two_factor_hotp.html')

    def test_account_new_two_factor_totp(self):
        self._journalist_logs_in()
        self._visit_edit_account()
        self._visit_edit_totp_secret()
        self._screenshot('journalist-account_new_two_factor_totp.png')
        self._save_html('journalist-account_new_two_factor_totp.html')
