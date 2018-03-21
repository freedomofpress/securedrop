# -*- coding: utf-8 -*-
from flask_testing import TestCase
from mock import MagicMock

import journalist

from utils import db_helper, env
from models import (Journalist, Submission, Reply, get_one_or_else,
                    LoginThrottledException)


def test_get_one_or_else_returns_one(journalist_app, test_journo):
    with journalist_app.app_context():
        # precondition: there must be one journalist
        assert Journalist.query.count() == 1

        query = Journalist.query.filter_by(username=test_journo['username'])
        selected_journo = get_one_or_else(query, MagicMock(), MagicMock())

        assert selected_journo.id == test_journo['id']


def test_get_one_or_else_multiple_results(journalist_app,
                                          test_admin,
                                          test_journo):
    with journalist_app.app_context():
        # precondition: there must be multiple journalists
        assert Journalist.query.count() == 2

        mock_logger = MagicMock()
        mock_abort = MagicMock()

        # this is equivalent to "SELECT *" which we know returns 2
        query = Journalist.query
        get_one_or_else(query, mock_logger, mock_abort)
        # Not specifying the very long log line in `logger.error`
        mock_logger.error.assert_called()
        mock_abort.assert_called_with(500)


def test_get_one_or_else_no_result_found(journalist_app, test_journo):
    with journalist_app.app_context():
        # precondition: there must be one journalist
        assert Journalist.query.count() == 1

        bad_name = test_journo['username'] + 'aaaaaa'
        query = Journalist.query.filter_by(username=bad_name)

        mock_logger = MagicMock()
        mock_abort = MagicMock()
        get_one_or_else(query, mock_logger, mock_abort)

        log_line = ('Found none when one was expected: '
                    'No row was found for one()')
        mock_logger.error.assert_called_with(log_line)
        mock_abort.assert_called_with(404)


class TestDatabase(TestCase):

    def create_app(self):
        return journalist.app

    def setUp(self):
        env.setup()

    def tearDown(self):
        env.teardown()

    # Check __repr__ do not throw exceptions

    def test_submission_string_representation(self):
        source, _ = db_helper.init_source()
        db_helper.submit(source, 2)

        test_submission = Submission.query.first()
        test_submission.__repr__()

    def test_reply_string_representation(self):
        journalist, _ = db_helper.init_journalist()
        source, _ = db_helper.init_source()
        db_helper.reply(journalist, source, 2)
        test_reply = Reply.query.first()
        test_reply.__repr__()

    def test_journalist_string_representation(self):
        test_journalist, _ = db_helper.init_journalist()
        test_journalist.__repr__()

    def test_source_string_representation(self):
        test_source, _ = db_helper.init_source()
        test_source.__repr__()

    def test_throttle_login(self):
        journalist, _ = db_helper.init_journalist()
        for _ in range(Journalist._MAX_LOGIN_ATTEMPTS_PER_PERIOD):
            Journalist.throttle_login(journalist)
        with self.assertRaises(LoginThrottledException):
            Journalist.throttle_login(journalist)
