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

from functional_test import FunctionalHelper


def test_journalist_verifies_deletion_of_one_submission_modal(
        test_journo,
        live_source_app,
        live_journalist_app,
        webdriver):

    helper = FunctionalHelper(
        driver=webdriver,
        journalist=test_journo,
        live_source_app=live_source_app,
        live_journalist_app=live_journalist_app)

    # This deletion button is displayed on the individual source page
    helper._source_visits_source_homepage()
    helper._source_chooses_to_submit_documents()
    helper._source_continues_to_submit_page()
    helper._source_submits_a_file()
    helper._source_logs_out()
    helper._journalist_logs_in()
    helper._journalist_visits_col()
    helper._journalist_uses_delete_selected_button_confirmation()


def test_journalist_uses_col_delete_collection_button_modal(
        test_journo,
        live_source_app,
        live_journalist_app,
        webdriver):

    helper = FunctionalHelper(
        driver=webdriver,
        journalist=test_journo,
        live_source_app=live_source_app,
        live_journalist_app=live_journalist_app)

    # This delete button is displayed on the individual source page
    helper._source_visits_source_homepage()
    helper._source_chooses_to_submit_documents()
    helper._source_continues_to_submit_page()
    helper._source_submits_a_file()
    helper._source_logs_out()
    helper._journalist_logs_in()
    helper._journalist_visits_col()
    helper._journalist_uses_delete_collection_button_confirmation()


def test_journalist_uses_index_delete_collections_button_modal(
        test_journo,
        live_source_app,
        live_journalist_app,
        webdriver):

    helper = FunctionalHelper(
        driver=webdriver,
        journalist=test_journo,
        live_source_app=live_source_app,
        live_journalist_app=live_journalist_app)

    # This deletion button is displayed on the index page
    helper._source_visits_source_homepage()
    helper._source_chooses_to_submit_documents()
    helper._source_continues_to_submit_page()
    helper._source_submits_a_file()
    helper._source_logs_out()
    helper._journalist_logs_in()
    helper._journalist_uses_delete_collections_button_confirmation()


def test_journalist_interface_ui_with_modal(
        test_journo,
        live_source_app,
        live_journalist_app,
        webdriver):

    helper = FunctionalHelper(
        driver=webdriver,
        journalist=test_journo,
        live_source_app=live_source_app,
        live_journalist_app=live_journalist_app)

    helper._source_visits_source_homepage()
    helper._source_chooses_to_submit_documents()
    helper._source_continues_to_submit_page()
    helper._source_submits_a_file()
    helper._source_logs_out()
    helper._journalist_logs_in()
    helper._journalist_uses_js_filter_by_sources()
    helper._journalist_selects_all_sources_then_selects_none()
    helper._journalist_selects_the_first_source()
    helper._journalist_uses_js_buttons_to_download_unread()
    helper._journalist_delete_all_confirmation()
