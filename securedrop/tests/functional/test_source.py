import pytest

from functional_test import FunctionalHelper

# The session expiration here cannot be set to -1 as it will trigger an
# exception in /create. Instead, we pick a 1-2s value to allow the account to
# be generated.
EXPIRATION_MINS = 0.03


def test_lookup_codename_hint(live_source_app, webdriver):
    helper = FunctionalHelper(
        driver=webdriver,
        live_source_app=live_source_app)

    helper._source_visits_source_homepage()
    helper._source_chooses_to_submit_documents()
    helper._source_continues_to_submit_page()
    helper._source_shows_codename()
    helper._source_hides_codename()
    helper._source_logs_out()
    helper._source_visits_source_homepage()
    helper._source_chooses_to_login()
    helper._source_proceeds_to_login()
    helper._source_sees_no_codename()


@pytest.fixture(scope='function')
def pre_create_config(config):
    config.SESSION_EXPIRATION_MINUTES = EXPIRATION_MINS


def test_source_session_timeout(live_source_app, webdriver, pre_create_config):
    helper = FunctionalHelper(
        driver=webdriver,
        live_source_app=live_source_app)

    helper._source_visits_source_homepage()
    helper._source_clicks_submit_documents_on_homepage()
    helper._source_continues_to_submit_page()
    helper._source_waits_for_session_to_timeout(EXPIRATION_MINS)
    helper._source_visits_source_homepage()
    helper._source_sees_session_timeout_message()


def test_not_found(live_source_app, webdriver):
    helper = FunctionalHelper(
        driver=webdriver,
        live_source_app=live_source_app)

    helper._source_not_found()
