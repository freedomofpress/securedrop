#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import unittest

from flask_testing import TestCase
import mock
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import journalist
import crypto_util
from utils import db_helper, env
from db import (db_session, Journalist, Submission, Source, Reply,
                get_one_or_else)

logging.basicConfig()
logger = logging.getLogger(__name__)


class TestDatabase(TestCase):

    def create_app(self):
        return journalist.app

    def setUp(self):
        env.setup()

    def tearDown(self):
        env.teardown()

    @mock.patch('flask.abort')
    def test_get_one_or_else_returns_one(self, mock):
        new_journo, _ = db_helper.init_journalist()

        query = Journalist.query.filter(Journalist.username == new_journo.username)
        selected_journo = get_one_or_else(query, logger, mock)
        self.assertEqual(new_journo, selected_journo)

    @mock.patch('flask.abort')
    def test_get_one_or_else_multiple_results(self, mock):
        journo_1, _ = db_helper.init_journalist()
        journo_2, _ = db_helper.init_journalist()

        selected_journos = get_one_or_else(Journalist.query, logger, mock)
        mock.assert_called_with(500)

    @mock.patch('flask.abort')
    def test_get_one_or_else_no_result_found(self, mock):
        query = Journalist.query.filter(Journalist.username == "alice")
        selected_journos = get_one_or_else(query, logger, mock)
        mock.assert_called_with(404)

    # Check __repr__ do not throw exceptions

    def test_submission_string_representation(self):
        source, _ = db_helper.init_source()
        submissions = db_helper.submit(source, 2)

        test_submission = Submission.query.first()
        test_submission.__repr__()

    def test_reply_string_representation(self):
        journalist, _ = db_helper.init_journalist()
        source, _ = db_helper.init_source()
        replies = db_helper.reply(journalist, source, 2)
        test_reply = Reply.query.first()
        test_reply.__repr__()

    def test_journalist_string_representation(self):
        test_journalist, _ = db_helper.init_journalist()
        test_journalist.__repr__()

    def test_source_string_representation(self):
        test_source, _ = db_helper.init_source()
        test_source.__repr__()


if __name__ == "__main__":
    unittest.main(verbosity=2)
