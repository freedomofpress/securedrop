from datetime import datetime

import pytest

from actions.sources_actions import SearchSourcesAction, SearchSourcesFilters
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
            app_db_session, app_storage, number=3, pending=False
        )
        # Including some sources that haven't submitted anything yet
        SourceFactory.create_batch(
            app_db_session, app_storage, number=4, pending=True
        )
        # And some sources that were deleted
        SourceFactory.create_batch(
            app_db_session, app_storage, number=3, deleted_at=datetime.utcnow()
        )

        # When searching for all sources, then it succeeds
        returned_sources = SearchSourcesAction(db_session=app_db_session).perform()

        # And only non-deleted and non-pending sources were returned by default
        expected_source_ids = {src.id for src in some_sources}
        assert {src.id for src in returned_sources} == expected_source_ids

    def test_filter_by_is_pending(self, app_db_session, app_storage):
        # Given an app with sources that are pending
        created_pending_sources = SourceFactory.create_batch(
            app_db_session, app_storage, number=4, pending=True
        )

        # And some other sources that are NOT pending
        created_non_pending_sources = SourceFactory.create_batch(
            app_db_session, app_storage, number=3, pending=False
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
            app_db_session, app_storage, number=4, is_starred=True
        )
        # And some other sources that have never been starred
        created_non_starred_sources = SourceFactory.create_batch(
            app_db_session, app_storage, number=3, is_starred=False
        )
        # And some other sources that were starred and then un-starred
        created_starred_then_un_starred_sources = SourceFactory.create_batch(
            app_db_session, app_storage, number=3, is_starred=True
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
