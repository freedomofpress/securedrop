from dataclasses import asdict
from datetime import UTC, datetime
from uuid import uuid4

from flask import url_for
from journalist_app.api2.types import Event, EventType, SourceTarget
from models import Source, db
from tests.utils.api_helper import get_api_headers


def test_source_conversation_seen_deleted_source_is_gone(
    journalist_app,
    journalist_api_token,
    test_files,
):
    """A stale seen event must not reintroduce a deleted source."""
    source_uuid = test_files["source"].uuid
    submission_uuid = test_files["submissions"][0].uuid
    upper_bound = test_files["source"].interaction_count

    with journalist_app.test_client() as app:
        # Capture the version while the source is still visible to the client.
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200
        source_version = index.json["sources"][source_uuid]

        # A completed request removes Flask-SQLAlchemy's scoped session, so
        # re-query the source before changing it instead of mutating the now
        # detached fixture instance.
        source = Source.query.filter(Source.uuid == source_uuid).one()
        source.deleted_at = datetime.now(UTC)
        db.session.commit()

        # The authoritative index no longer exposes the source or its items.
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200
        assert source_uuid not in index.json["sources"]
        assert submission_uuid not in index.json["items"]

        event = Event(
            id=str(uuid4().int % 10**18),
            target=SourceTarget(source_uuid=source_uuid, version=source_version),
            type=EventType.SOURCE_CONVERSATION_SEEN,
            data={"upper_bound": upper_bound},
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )

        assert response.status_code == 200
        assert response.json["events"][event.id] == [410, None]
        assert source_uuid not in response.json["sources"]
        assert submission_uuid not in response.json["items"]
