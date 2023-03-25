from datetime import datetime
from pathlib import Path
from typing import List

import pytest

import models
from actions.pagination import PaginationConfig
from actions.sources_actions import SearchSourcesAction, SearchSourcesFilters, DeleteSingleSourceAction
from encryption import EncryptionManager, GpgKeyNotFoundError
from journalist_app.utils import mark_seen
from tests import utils
from tests.factories.models_factories import SourceFactory
from tests.functional.db_session import get_database_session


@pytest.fixture
def app_db_session(journalist_app):
    with get_database_session(journalist_app.config["SQLALCHEMY_DATABASE_URI"]) as db_session:
        yield db_session


class TestSearchSourcesAction:
    def test(self, app_db_session, app_storage):
        # Given an app with some sources in different states
        some_sources = SourceFactory.create_batch(
            app_db_session, app_storage, records_count=3, pending=False
        )
        # Including some sources that haven't submitted anything yet
        SourceFactory.create_batch(
            app_db_session, app_storage, records_count=4, pending=True
        )
        # And some sources that were deleted
        SourceFactory.create_batch(
            app_db_session, app_storage, records_count=3, deleted_at=datetime.utcnow()
        )

        # When searching for all sources, then it succeeds
        returned_sources = SearchSourcesAction(db_session=app_db_session).perform()

        # And only non-deleted and non-pending sources were returned by default
        expected_source_ids = {src.id for src in some_sources}
        assert {src.id for src in returned_sources} == expected_source_ids

    def test_filter_by_is_pending(self, app_db_session, app_storage):
        # Given an app with sources that are pending
        created_pending_sources = SourceFactory.create_batch(
            app_db_session, app_storage, records_count=4, pending=True
        )

        # And some other sources that are NOT pending
        created_non_pending_sources = SourceFactory.create_batch(
            app_db_session, app_storage, records_count=3, pending=False
        )

        # When searching for all pending sources, then it succeeds
        returned_pending_sources = SearchSourcesAction(
            db_session=app_db_session, filters=SearchSourcesFilters(filter_by_is_pending=True),
        ).perform()

        # And the expected sources were returned
        assert {src.id for src in returned_pending_sources} == {
            src.id for src in created_pending_sources
        }

        # And when searching for all NON-pending sources, then it succeeds
        returned_non_pending_sources = SearchSourcesAction(
            db_session=app_db_session, filters=SearchSourcesFilters(filter_by_is_pending=False),
        ).perform()

        # And the expected sources were returned
        assert {src.id for src in returned_non_pending_sources} == {
            src.id for src in created_non_pending_sources
        }

    def test_filter_by_is_starred(self, app_db_session, app_storage):
        # Given an app with sources that are starred
        created_starred_sources = SourceFactory.create_batch(
            app_db_session, app_storage, records_count=4, is_starred=True
        )
        # And some other sources that have never been starred
        created_non_starred_sources = SourceFactory.create_batch(
            app_db_session, app_storage, records_count=3, is_starred=False
        )
        # And some other sources that were starred and then un-starred
        created_starred_then_un_starred_sources = SourceFactory.create_batch(
            app_db_session, app_storage, records_count=2, is_starred=True
        )
        for src in created_starred_then_un_starred_sources:
            src.star.starred = False
        app_db_session.commit()

        # When searching for all starred sources, then it succeeds
        returned_starred_sources = SearchSourcesAction(
            db_session=app_db_session, filters=SearchSourcesFilters(filter_by_is_starred=True),
        ).perform()

        # And the expected sources were returned
        assert {src.id for src in returned_starred_sources} == {
            src.id for src in created_starred_sources
        }

        # And when searching for all NON-starred sources, then it succeeds
        returned_non_starred_sources = SearchSourcesAction(
            db_session=app_db_session, filters=SearchSourcesFilters(filter_by_is_starred=False),
        ).perform()

        # And the expected sources were returned
        expected_non_starred_source_ids = set()
        expected_non_starred_source_ids.update(
            {src.id for src in created_starred_then_un_starred_sources}
        )
        expected_non_starred_source_ids.update(
            {src.id for src in created_non_starred_sources}
        )
        assert expected_non_starred_source_ids == {
            src.id for src in returned_non_starred_sources
        }

    def test_filter_by_is_deleted(self, app_db_session, app_storage):
        # Given an app with sources that are deleted
        created_deleted_sources = SourceFactory.create_batch(
            app_db_session, app_storage, records_count=4, deleted_at=datetime.utcnow()
        )

        # And some other sources that are NOT deleted
        created_non_deleted_sources = SourceFactory.create_batch(
            app_db_session, app_storage, records_count=3, deleted_at=None
        )

        # When searching for all deleted sources, then it succeeds
        returned_deleted_sources = SearchSourcesAction(
            db_session=app_db_session, filters=SearchSourcesFilters(filter_by_is_deleted=True),
        ).perform()

        # And the expected sources were returned
        assert {src.id for src in returned_deleted_sources} == {
            src.id for src in created_deleted_sources
        }

        # And when searching for all NON-deleted sources, then it succeeds
        returned_non_pending_sources = SearchSourcesAction(
            db_session=app_db_session, filters=SearchSourcesFilters(filter_by_is_deleted=False),
        ).perform()

        # And the expected sources were returned
        assert {src.id for src in returned_non_pending_sources} == {
            src.id for src in created_non_deleted_sources
        }

    def test_paginate_results_with_config(self, app_db_session, app_storage):
        # Given an app with some sources
        all_sources = SourceFactory.create_batch(app_db_session, app_storage, records_count=10)

        # When searching for the first page of all sources, then it succeeds
        first_page_of_sources = SearchSourcesAction(db_session=app_db_session).perform(
            paginate_results_with_config=PaginationConfig(page_number=0, page_size=3)
        )

        # And the expected sources were returned
        expected_source_ids = {src.id for src in all_sources[0:3]}
        assert {src.id for src in first_page_of_sources} == expected_source_ids

        # And when searching for the second page of all sources, then it succeeds
        second_page_of_sources = SearchSourcesAction(db_session=app_db_session).perform(
            paginate_results_with_config=PaginationConfig(page_number=1, page_size=3)
        )

        # And the expected sources were returned
        expected_source_ids = {src.id for src in all_sources[3:6]}
        assert {src.id for src in second_page_of_sources} == expected_source_ids


class TestDeleteSingleSourceAction:

    def test(self, app_db_session, app_storage, test_journo):
        # Given an app with some sources including one source to delete
        source = SourceFactory.create(app_db_session, app_storage)
        SourceFactory.create(app_db_session, app_storage)

        # And the source has an encryption key
        encryption_mgr = EncryptionManager.get_default()
        assert encryption_mgr.get_source_key_fingerprint(source.filesystem_id)

        # And the source has some submissions, messages and replies
        journo = test_journo["journalist"]
        all_submissions = utils.db_helper.submit(
            app_storage, source, 2, submission_type="file"
        )
        all_messages = utils.db_helper.submit(
            app_storage, source, 2, submission_type="message"
        )
        all_replies = utils.db_helper.reply(app_storage, journo, source, 2)
        assert app_db_session.query(models.Submission).filter_by(source_id=source.id).all()
        assert app_db_session.query(models.Reply).filter_by(source_id=source.id).all()

        # And the submissions, messages and replies have been seen
        mark_seen(all_submissions, journo)
        mark_seen(all_messages, journo)
        mark_seen(all_replies, journo)
        assert app_db_session.query(models.SeenFile).filter_by(journalist_id=journo.id).all()
        assert app_db_session.query(models.SeenMessage).filter_by(journalist_id=journo.id).all()
        assert app_db_session.query(models.SeenReply).filter_by(journalist_id=journo.id).all()

        # And the submissions point to existing files
        all_submissions_file_paths: List[Path] = []
        for submission in all_submissions:
            submission_file_path = Path(app_storage.path(source.filesystem_id, submission.filename))
            assert submission_file_path.exists()
            all_submissions_file_paths.append(submission_file_path)
        assert all_submissions_file_paths

        # When deleting the source, then it succeeds
        DeleteSingleSourceAction(db_session=app_db_session, source=source).perform()

        # And the source's key was deleted
        with pytest.raises(GpgKeyNotFoundError):
            encryption_mgr.get_source_key_fingerprint(source.filesystem_id)

        # And the source's submissions, replies and messages were deleted
        assert not app_db_session.query(models.Submission).filter_by(source_id=source.id).all()
        assert not app_db_session.query(models.Reply).filter_by(source_id=source.id).all()

        # And the submissions' files were deleted
        for file_path in all_submissions_file_paths:
            assert not file_path.exists()

        # And the records to track whether messages have been seen were deleted
        assert not app_db_session.query(models.SeenFile).filter_by(journalist_id=journo.id).all()
        assert not app_db_session.query(models.SeenMessage).filter_by(journalist_id=journo.id).all()
        assert not app_db_session.query(models.SeenReply).filter_by(journalist_id=journo.id).all()

        # And the source's DB record was deleted
        assert app_db_session.query(models.Source).get(source.id) is None
