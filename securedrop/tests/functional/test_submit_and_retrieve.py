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


def test_submit_and_retrieve_file_happy_path(
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
    helper._journalist_checks_messages()
    helper._journalist_stars_and_unstars_single_message()
    helper._journalist_downloads_message()
    helper._journalist_sends_reply_to_source()
    helper._source_visits_source_homepage()
    helper._source_chooses_to_login()
    helper._source_proceeds_to_login()
    helper._source_deletes_a_journalist_reply()


def test_source_cancels_at_login_page(live_source_app, webdriver):
    helper = FunctionalHelper(
        driver=webdriver,
        live_source_app=live_source_app)

    helper._source_visits_source_homepage()
    helper._source_chooses_to_login()
    helper._source_hits_cancel_at_login_page()


def test_source_cancels_at_submit_page(live_source_app, webdriver):
    helper = FunctionalHelper(
        driver=webdriver,
        live_source_app=live_source_app)

    helper._source_visits_source_homepage()
    helper._source_chooses_to_submit_documents()
    helper._source_continues_to_submit_page()
    helper._source_hits_cancel_at_submit_page()
