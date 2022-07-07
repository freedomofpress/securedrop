# -*- coding: utf-8 -*-
import pytest
from mock import MagicMock
from models import (
    InstanceConfig,
    Journalist,
    LoginThrottledException,
    Reply,
    Submission,
    get_one_or_else,
)
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from .utils import db_helper


def test_get_one_or_else_returns_one(journalist_app, test_journo):
    with journalist_app.app_context():
        # precondition: there must be one journalist
        assert Journalist.query.count() == 1

        query = Journalist.query.filter_by(username=test_journo["username"])
        selected_journo = get_one_or_else(query, MagicMock(), MagicMock())

        assert selected_journo.id == test_journo["id"]


def test_get_one_or_else_multiple_results(journalist_app, test_admin, test_journo):
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

        bad_name = test_journo["username"] + "aaaaaa"
        query = Journalist.query.filter_by(username=bad_name)

        mock_logger = MagicMock()
        mock_abort = MagicMock()
        get_one_or_else(query, mock_logger, mock_abort)

        log_line = "Found none when one was expected: " "No row was found for one()"
        mock_logger.error.assert_called_with(log_line)
        mock_abort.assert_called_with(404)


def test_throttle_login(journalist_app, test_journo):
    with journalist_app.app_context():
        journalist = test_journo["journalist"]
        for _ in range(Journalist._MAX_LOGIN_ATTEMPTS_PER_PERIOD):
            Journalist.throttle_login(journalist)
        with pytest.raises(LoginThrottledException):
            Journalist.throttle_login(journalist)


def test_submission_string_representation(journalist_app, test_source, app_storage):
    with journalist_app.app_context():
        db_helper.submit(app_storage, test_source["source"], 2)
        test_submission = Submission.query.first()
        test_submission.__repr__()


def test_reply_string_representation(journalist_app, test_journo, test_source, app_storage):
    with journalist_app.app_context():
        db_helper.reply(app_storage, test_journo["journalist"], test_source["source"], 2)
        test_reply = Reply.query.first()
        test_reply.__repr__()


def test_journalist_string_representation(journalist_app, test_journo):
    with journalist_app.app_context():
        test_journo["journalist"].__repr__()


def test_source_string_representation(journalist_app, test_source):
    with journalist_app.app_context():
        test_source["source"].__repr__()


def test_only_one_active_instance_config_can_exist(config, source_app):
    """
    Checks that attempts to add multiple active InstanceConfig records fail.

    InstanceConfig is supposed to be invalidated by setting
    valid_until to the time the config was no longer in effect. Until
    we added the partial index preventing multiple rows with a null
    valid_until, it was possible for the system to create multiple
    active records, which would cause MultipleResultsFound exceptions
    in InstanceConfig.get_current.
    """
    # create a separate session
    engine = create_engine(source_app.config["SQLALCHEMY_DATABASE_URI"])
    session = sessionmaker(bind=engine)()

    # in the separate session, create an InstanceConfig with default
    # values, but don't commit it
    conflicting_config = InstanceConfig()
    session.add(conflicting_config)

    with source_app.app_context():
        # get_current will create another InstanceConfig with default values
        InstanceConfig.get_current()

    # now the commit of the first instance should fail
    with pytest.raises(IntegrityError):
        session.commit()
