from functional_test import FunctionalHelper


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
