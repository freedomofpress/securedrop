# -*- coding: utf-8 -*-
import pytest

from mock import MagicMock

from .utils import db_helper
from models import (Journalist, Submission, Reply, Source, get_one_or_else,
                    LoginThrottledException)


def test_source_public_key_setter_unimplemented(journalist_app, test_source):
    with journalist_app.app_context():
        source = Source.query.first()
        with pytest.raises(NotImplementedError):
            source.public_key = 'a curious developer tries to set a pubkey!'


def test_source_public_key_delete_unimplemented(journalist_app, test_source):
    with journalist_app.app_context():
        source = Source.query.first()
        with pytest.raises(NotImplementedError):
            del source.public_key


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


def test_throttle_login(journalist_app, test_journo):
    with journalist_app.app_context():
        journalist = test_journo['journalist']
        for _ in range(Journalist._MAX_LOGIN_ATTEMPTS_PER_PERIOD):
            Journalist.throttle_login(journalist)
        with pytest.raises(LoginThrottledException):
            Journalist.throttle_login(journalist)


def test_submission_string_representation(journalist_app, test_source):
    with journalist_app.app_context():
        db_helper.submit(test_source['source'], 2)
        test_submission = Submission.query.first()
        test_submission.__repr__()


def test_reply_string_representation(journalist_app,
                                     test_journo,
                                     test_source):
    with journalist_app.app_context():
        db_helper.reply(test_journo['journalist'],
                        test_source['source'],
                        2)
        test_reply = Reply.query.first()
        test_reply.__repr__()


def test_journalist_string_representation(journalist_app, test_journo):
    with journalist_app.app_context():
        test_journo['journalist'].__repr__()


def test_source_string_representation(journalist_app, test_source):
    with journalist_app.app_context():
        test_source['source'].__repr__()
