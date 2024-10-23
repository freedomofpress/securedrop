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
import json
from typing import Union

import pytest
import tbselenium
from tbselenium.utils import disable_js
from tests.functional.app_navigators.source_app_nav import SourceAppNavigator
from tests.functional.pageslayout.utils import list_locales, save_static_data


# Monkey  Patch set_tbb_pref until a new version of tbselenium > 0.8.1 is released
def monkey_patch_set_tbb_pref(
    driver: tbselenium.tbdriver.TorBrowserDriver, name: str, value: Union[bool, str, int]
) -> None:
    try:
        script = "Services.prefs."
        if isinstance(value, bool):
            script += "setBoolPref"
        elif isinstance(value, (str)):
            script += "setStringPref"
        else:
            script += "setIntPref"
        script += f"({json.dumps(name)}, {json.dumps(value)});"

        with driver.context(driver.CONTEXT_CHROME):
            driver.execute_script(script)
    except Exception:
        raise
    finally:
        driver.set_context(driver.CONTEXT_CONTENT)


tbselenium.utils.set_tbb_pref = monkey_patch_set_tbb_pref


@pytest.mark.parametrize("locale", list_locales())
@pytest.mark.pagelayout
class TestSourceLayoutTorBrowser:
    def test_index_and_logout(self, locale, sd_servers):
        # Given a source user accessing the app from their browser
        locale_with_commas = locale.replace("_", "-")
        with SourceAppNavigator.using_tor_browser_web_driver(
            source_app_base_url=sd_servers.source_app_base_url,
            accept_languages=locale_with_commas,
        ) as navigator:
            # And they have disabled JS in their browser
            disable_js(navigator.driver)

            # When they first login, it succeeds
            navigator.source_visits_source_homepage()
            save_static_data(navigator.driver, locale, "source-index")

            navigator.source_clicks_submit_documents_on_homepage()
            navigator.source_continues_to_submit_page()

            # And when they logout, it succeeds
            navigator.source_logs_out()
            save_static_data(navigator.driver, locale, "source-logout_page")
