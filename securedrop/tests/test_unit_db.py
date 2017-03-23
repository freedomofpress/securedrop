#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

from flask_testing import TestCase
import mock

import journalist
from utils import db_helper, env
from db import (Journalist, Submission, Reply,
                get_one_or_else, SourceTag, SubmissionTag, SourceLabelType,
                SubmissionLabelType)


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
        with mock.patch('logger') as mock_logger:
            selected_journo = get_one_or_else(query, mock_logger, mock)
        self.assertEqual(new_journo, selected_journo)

    @mock.patch('flask.abort')
    def test_get_one_or_else_multiple_results(self, mock):
        journo_1, _ = db_helper.init_journalist()
        journo_2, _ = db_helper.init_journalist()

        with mock.patch('logger') as mock_logger:
            selected_journos = get_one_or_else(Journalist.query, mock_logger,
                                               mock)
        mock_logger.error.assert_called()  # Not specifying very long log line
        mock.assert_called_with(500)

    @mock.patch('flask.abort')
    def test_get_one_or_else_no_result_found(self, mock):
        query = Journalist.query.filter(Journalist.username == "alice")

        with mock.patch('logger') as mock_logger:
            selected_journos = get_one_or_else(query, mock_logger,
                                               mock)
        log_line = 'Found none when one was expected: No row was found for one()'
        mock_logger.error.assert_called_with(log_line)
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

    def test_submission_label_type_string_representation(self):
        journalist.create_label(SubmissionLabelType, "test")
        test_label = SubmissionLabelType.query.first()
        test_label.__repr__()

    def test_source_label_type_string_representation(self):
        journalist.create_label(SourceLabelType, "test")
        test_label = SourceLabelType.query.first()
        test_label.__repr__()

    def test_submission_tag_string_representation(self):
        source, _ = db_helper.init_source()
        submissions = db_helper.submit(source, 2)

        test_submission = Submission.query.first()

        journalist.create_label(SubmissionLabelType, "test")
        test_label = SubmissionLabelType.query.first()

        journalist.create_tag(test_submission, test_label)
        test_submission_tag = SubmissionTag.query.first()
        test_submission_tag.__repr__()

    def test_source_tag_string_representation(self):
        source, _ = db_helper.init_source()

        journalist.create_label(SourceLabelType, "test")
        test_label = SourceLabelType.query.first()

        journalist.create_tag(source, test_label)
        test_source_tag = SourceTag.query.first()
        test_source_tag.__repr__()


if __name__ == "__main__":
    unittest.main(verbosity=2)
