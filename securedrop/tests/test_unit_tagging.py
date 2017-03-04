#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import unittest

from flask import url_for
from flask_testing import TestCase
from sqlalchemy.orm.exc import NoResultFound

import crypto_util
from db import (Submission, SourceTag, SubmissionTag, SourceLabelType,
                SubmissionLabelType, KeyedLabelText)
import journalist
import utils

# Smugly seed the RNG for deterministic testing
random.seed('¯\_(ツ)_/¯')

class TestTagging(TestCase):

    # A method required by flask_testing.TestCase
    def create_app(self):
        return journalist.app

    def setUp(self):
        utils.env.setup()

        # Patch the two-factor verification to avoid intermittent errors
        utils.db_helper.mock_verify_token(self)

        # Setup test users: user & admin
        self.db_key = crypto_util.gen_db_key()
        self.user, self.user_pw = \
                utils.db_helper.init_journalist(db_key=self.db_key)
        self.admin, self.admin_pw = \
                utils.db_helper.init_journalist(db_key=self.db_key,
                                                is_admin=True)

    def tearDown(self):
        utils.env.teardown()

    def _login_admin(self):
        self._ctx.g.user = self.admin
        self._ctx.g.db_key = self.db_key

    def _login_user(self):
        self._ctx.g.user = self.user
        self._ctx.g.db_key = self.db_key

    def test_get_all_defined_source_tags(self):
        journalist.create_label(SourceLabelType, self.db_key, "test")
        test_label = SourceLabelType.query.one()
        source_tags = journalist.get_all_defined_tags(SourceLabelType)
        self.assertEquals(source_tags[0].label_text_getter(self.db_key), "test")

    def test_get_all_defined_submission_tags(self):
        journalist.create_label(SubmissionLabelType, self.db_key, "test")
        test_label = SubmissionLabelType.query.one()
        submission_tags = journalist.get_all_defined_tags(SubmissionLabelType)
        self.assertEquals(submission_tags[0].label_text_getter(self.db_key), "test")

    def test_create_new_source_label_type(self):
        self._login_admin()

        resp = self.client.post(
            url_for("admin_create_source_label_type"),
            data=dict(label_text="my label"),
            follow_redirects=True
            )

        test_label = SourceLabelType.query.one()
        self.assertEquals(test_label.label_text_getter(self.db_key), "my label")
        self.assert200(resp)  # Should redirect to admin_index
        self.assertIn("my label", resp.data)

    def test_create_source_label_type_already_exists(self):
        self._login_admin()

        journalist.create_label(SourceLabelType, self.db_key, "my test")

        resp = self.client.post(
            url_for("admin_create_source_label_type"),
            data=dict(label_text="my test"),
            follow_redirects=True
            )

        self.assertIn("Tag already exists!", resp.data)

    def test_create_source_label_type_empty_should_fail(self):
        self._login_admin()

        resp = self.client.post(
            url_for("admin_create_source_label_type"),
            data=dict(label_text=""),
            follow_redirects=True
            )

        self.assertIn("Specify the text for this label!", resp.data)

    def test_create_new_submission_label_type(self):
        self._login_admin()

        resp = self.client.post(
            url_for("admin_create_submission_label_type"),
            data=dict(label_text="my label"),
            follow_redirects=True
            )

        test_label = SubmissionLabelType.query.one()
        self.assertEquals(test_label.label_text_getter(self.db_key), "my label")
        self.assert200(resp)  # Should redirect to admin_index
        self.assertIn("my label", resp.data)

    def test_create_submission_label_type_already_exists(self):
        self._login_admin()

        journalist.create_label(SubmissionLabelType, self.db_key, "my test")

        resp = self.client.post(
            url_for("admin_create_submission_label_type"),
            data=dict(label_text="my test"),
            follow_redirects=True
            )

        self.assertIn("Tag already exists!", resp.data)

    def test_create_submission_label_type_empty_should_fail(self):
        self._login_admin()

        resp = self.client.post(
            url_for("admin_create_submission_label_type"),
            data=dict(label_text=""),
            follow_redirects=True
            )

        self.assertIn("Specify the text for this label!", resp.data)

    def test_delete_existing_source_label_type(self):
        self._login_admin()

        journalist.create_label(SourceLabelType, self.db_key, "my test")

        resp = self.client.post(
            url_for("admin_delete_source_label_type", label_id=1),
            follow_redirects=True
            )

        self.assert200(resp)  # Should redirect to admin_index
        defined_tags = SourceLabelType.query.all()
        self.assertEqual([], defined_tags)

    def test_delete_existing_submission_label_type(self):
        self._login_admin()

        journalist.create_label(SubmissionLabelType, self.db_key, "my test")

        resp = self.client.post(
            url_for("admin_delete_submission_label_type", label_id=1),
            follow_redirects=True
            )

        self.assert200(resp)  # Should redirect to admin_index
        defined_tags = SubmissionLabelType.query.all()
        self.assertEqual([], defined_tags)

    def test_create_new_source_tag(self):
        self._login_user()
        source, _ = utils.db_helper.init_source()

        journalist.create_label(SourceLabelType, self.db_key, "my label")
        test_label = SourceLabelType.query.first()

        resp = self.client.post(
            url_for("add_source_label", sid=source.filesystem_id,
                                        label_id=1),
            follow_redirects=True
            )

        test_tag = SourceTag.query.one()
        self.assertEquals(test_tag.label.label_text_getter(self.db_key), "my label")
        self.assert200(resp)  # Should redirect back to /col

    def test_delete_source_tag(self):
        self._login_user()
        source, _ = utils.db_helper.init_source()

        journalist.create_label(SourceLabelType, self.db_key, "my label")
        test_label = SourceLabelType.query.first()
        journalist.create_tag(source, self.db_key, test_label)

        resp = self.client.post(
            url_for("remove_source_label", sid=source.filesystem_id,
                                           label_id=1),
            follow_redirects=True
            )

        test_tags = SourceTag.query.all()
        self.assertEquals([], test_tags)
        self.assert200(resp)  # Should redirect back to /col

    def test_create_new_submission_tag(self):
        self._login_user()
        source, _ = utils.db_helper.init_source()
        submissions = utils.db_helper.submit(source, 2)
        submission = Submission.query.first()

        journalist.create_label(SubmissionLabelType, self.db_key, "my label")
        test_label = SubmissionLabelType.query.first()

        resp = self.client.post(
            url_for("add_submission_label",
                    sid=source.filesystem_id, filename=submission.filename,
                    label_id=1),
            follow_redirects=True
            )

        test_tag = SubmissionTag.query.one()
        self.assertEquals(test_tag.label.label_text_getter(self.db_key), "my label")
        self.assert200(resp)  # Should redirect back to /col

    def test_delete_submission_tag(self):
        self._login_user()
        source, _ = utils.db_helper.init_source()
        submissions = utils.db_helper.submit(source, 2)
        submission = Submission.query.first()

        journalist.create_label(SubmissionLabelType, self.db_key, "my label")
        test_label = SubmissionLabelType.query.first()
        journalist.create_tag(submission, self.db_key, test_label)

        resp = self.client.post(
            url_for("remove_submission_label", sid=source.filesystem_id,
                    filename=submission.filename, label_id=1),
            follow_redirects=True
            )

        test_tags = SubmissionTag.query.all()
        self.assertEquals([], test_tags)
        self.assert200(resp)  # Should redirect back to /col

    def test_get_source_tags_get_one(self):
        journalist.create_label(SourceLabelType, self.db_key, "my label")
        test_label = SourceLabelType.query.one()

        source, _ = utils.db_helper.init_source()

        journalist.create_tag(source, self.db_key, test_label)
        test_source_tag = SourceTag.query.first()

        for tag in source.tags:
            self.assertEquals(tag.label.label_text_getter(self.db_key), "my label")

    def test_filter_index_by_source_label_no_matches(self):
        self._login_user()

        source, _ = utils.db_helper.init_source()
        journalist.create_label(SourceLabelType, self.db_key, "test 1")
        journalist.create_label(SourceLabelType, self.db_key, "test 2")
        label = SourceLabelType.query.first()

        resp = self.client.get(
            url_for('index', filter=[label.id] ),
            follow_redirects=True
            )

        self.assertIn("No matching documents found!", resp.data)

    def test_filter_index_by_single_source_label_single_match(self):
        self._login_user()

        source1, _ = utils.db_helper.init_source()
        source2, _ = utils.db_helper.init_source()

        journalist.create_label(SourceLabelType, self.db_key, "test 1")
        journalist.create_label(SourceLabelType, self.db_key, "test 2")

        label = SourceLabelType.query.first()
        journalist.create_tag(source1, self.db_key, label)

        resp = self.client.get(
            url_for('index', filter=[label.id] ),
            follow_redirects=True
            )

        self.assertIn(source1.journalist_designation, resp.data)
        self.assertNotIn(source2.journalist_designation, resp.data)

    def test_filter_index_by_multiple_source_labels_single_match(self):
        self._login_user()

        source1, _ = utils.db_helper.init_source()
        source2, _ = utils.db_helper.init_source()

        journalist.create_label(SourceLabelType, self.db_key, "test 1")
        journalist.create_label(SourceLabelType, self.db_key, "test 2")

        labels = SourceLabelType.query.all()
        for label in labels:
            journalist.create_tag(source1, self.db_key, label)

        resp = self.client.get(
            url_for('index', filter=[x.id for x in labels] ),
            follow_redirects=True
            )

        self.assertIn(source1.journalist_designation, resp.data)
        self.assertNotIn(source2.journalist_designation, resp.data)

    def test_get_unselected_labels(self):
        source1, _ = utils.db_helper.init_source()
        source2, _ = utils.db_helper.init_source()

        journalist.create_label(SourceLabelType, self.db_key, "test 1")
        journalist.create_label(SourceLabelType, self.db_key, "test 2")

        label = SourceLabelType.query.first()
        journalist.create_tag(source1, self.db_key, label)

        source1_unused_tags = journalist.get_unselected_labels(source1)
        source2_unused_tags = journalist.get_unselected_labels(source2)

        self.assertEqual(len(source1_unused_tags), 1)
        self.assertEqual(len(source2_unused_tags), 2)

    def test_deleting_source_label_type_also_deletes_source_tags(self):
        source1, _ = utils.db_helper.init_source()
        journalist.create_label(SourceLabelType, self.db_key, "test 1")
        label = SourceLabelType.query.first()
        journalist.create_tag(source1, self.db_key, label)
        journalist.delete_label(SourceLabelType, label)

        self.assertEqual(len(source1.tags), 0)

    def test_source_label_text_uniqueness(self):
        journalist.create_label(SourceLabelType, self.db_key, "test")
        with self.assertRaises(SourceLabelType.LabelUniquenessError):
            journalist.create_label(SourceLabelType, self.db_key, "test")

    def test_submission_label_text_uniqueness(self):
        journalist.create_label(SubmissionLabelType, self.db_key, "test")
        with self.assertRaises(SubmissionLabelType.LabelUniquenessError):
            journalist.create_label(SubmissionLabelType, self.db_key, "test")

    def test_submission_label_text_getter(self):
        journalist.create_label(SubmissionLabelType, self.db_key, "test")
        test_label = SubmissionLabelType.query.one()
        test_label_text = test_label.label_text_getter(self.db_key)
        self.assertEqual(test_label_text, 'test')

    def test_source_label_text_getter(self):
        journalist.create_label(SourceLabelType, self.db_key, "test")
        test_label = SourceLabelType.query.one()
        test_label_text = test_label.label_text_getter(self.db_key)
        self.assertEqual(test_label_text, 'test')

    def test_source_label_filter_by_label_text(self):
        journalist.create_label(SourceLabelType, self.db_key, "test")
        SourceLabelType.query.with_transformation(
            SourceLabelType.label_text==KeyedLabelText(self.db_key, 'test')
            ).one()
        with self.assertRaises(NoResultFound):
            SourceLabelType.query.with_transformation(
                SourceLabelType.label_text==KeyedLabelText(self.db_key, 't35t')
                ).one()

    def test_submission_label_filter_by_label_text(self):
        journalist.create_label(SubmissionLabelType, self.db_key, "test")
        SubmissionLabelType.query.with_transformation(
            SubmissionLabelType.label_text==KeyedLabelText(self.db_key, 'test')
            ).one()
        with self.assertRaises(NoResultFound):
            SubmissionLabelType.query.with_transformation(
                SubmissionLabelType.label_text==KeyedLabelText(self.db_key,
                                                               't35t')
                ).one()


if __name__ == "__main__":
    unittest.main(verbosity=2)
