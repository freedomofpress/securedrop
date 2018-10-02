from functional_test import FunctionalHelper


def test_submit_and_retrieve_message_happy_path(
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
    helper._source_submits_a_message()
    helper._source_logs_out()
    helper._journalist_logs_in()
    helper._journalist_checks_messages()
    helper._journalist_downloads_message()
