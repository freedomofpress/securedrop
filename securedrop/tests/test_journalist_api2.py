import uuid
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from flask import url_for
from flask_sqlalchemy import get_debug_queries
from journalist_app import api2
from journalist_app.api2.shared import json_version
from journalist_app.api2.types import (
    VERSION_LEN,
    Event,
    EventType,
    ItemTarget,
    SourceTarget,
)
from models import Reply, Source, SourceStar, Submission, db
from sqlalchemy.orm.exc import MultipleResultsFound
from tests.utils import ascii_armor, decrypt_as_journalist
from tests.utils.api_helper import get_api_headers
from tests.utils.db_helper import init_source, submit


def filtered_queries():
    # filter out PRAGMA, instance_config loading, etc.
    return [
        q
        for q in get_debug_queries()
        if q.statement.startswith("SELECT")
        and not q.statement.startswith("SELECT instance_config.")
    ]


@contextmanager
def assert_query_count(expected_count, expect_login=True):
    """verify an API request makes the expected number of queries"""
    initial_count = len(filtered_queries())
    yield
    new_queries = filtered_queries()[initial_count:]
    # If the first API request is to look up journalists, it's part of the login flow, so skip it
    if (
        expect_login
        and len(new_queries) >= 1
        and new_queries[0].statement.startswith("SELECT journalists.")
    ):
        new_queries = new_queries[1:]

    assert len(new_queries) == expected_count, (
        f"Expected {expected_count} queries, but {len(new_queries)} were executed"
    )


def test_json_version():
    d = {"foo": "bar", "baz": "biz"}
    version1 = json_version(d)
    assert version1 == "2231968214a50f92d216048c7fc624c061372a4225e9e94aca88bdfaca162087"

    d2 = {"baz": "biz", "foo": "bar"}
    version2 = json_version(d2)
    assert version1 == version2


@pytest.mark.parametrize(
    ("endpoint", "kwargs"),
    [
        ("api2.index", {}),
        ("api2.index", {"shard_spec": "foo"}),
        # while this should be a POST request, the 403 will kick in first
        ("api2.data", {}),
    ],
)
def test_auth_required(journalist_app, endpoint, kwargs):
    """
    Verify all APIv2 endpoints require authentication
    """
    with journalist_app.test_client() as app:
        response = app.get(url_for(endpoint, **kwargs))

        assert response.status_code == 403


def test_index(journalist_app, test_files, journalist_api_token, app_storage):
    """
    Verify GET /index response and HTTP 304 behavior.
    """
    # Create a pending source and a deleted source to verify they're excluded
    with journalist_app.app_context():
        # Create a pending source (no submissions)
        pending_source, _ = init_source(app_storage)
        pending_uuid = pending_source.uuid
        assert pending_source.pending is True

        # Create source that is queued for deletion but not yet deleted
        deleted_source, _ = init_source(app_storage)
        submit(app_storage, deleted_source, 1)
        deleted_uuid = deleted_source.uuid
        assert deleted_source.pending is False
        # Mark it as deleted
        deleted_source.deleted_at = datetime.now(UTC)
        db.session.commit()

    with journalist_app.test_client() as app:
        uuid = test_files["source"].uuid
        with assert_query_count(2):
            response = app.get(
                url_for("api2.index"),
                headers=get_api_headers(journalist_api_token),
            )

        # Verify the active source is in the response
        assert response.status_code == 200
        assert uuid in response.json["sources"]
        # test_files generates 2 submissions and 1 reply, so 3 items total
        assert len(response.json["items"]) == 3
        # Verify pending and deleted sources are NOT in the response
        assert pending_uuid not in response.json["sources"]
        assert deleted_uuid not in response.json["sources"]

        with assert_query_count(2):
            response2 = app.get(
                url_for("api2.index"),
                headers={
                    **get_api_headers(journalist_api_token),
                    "If-None-Match": response.headers["ETag"],
                },
            )

        # With the etag, verify we get an empty 304
        assert response2.status_code == 304
        assert response2.calculate_content_length() == 0


def test_index_with_shard(journalist_app, test_files, journalist_api_token):
    """
    Verify GET /index/<shard_spec> with a single shard prefix: matching,
    non-matching, deeper prefixes, ETag/304, and that journalists are always
    included.
    """
    with journalist_app.test_client() as app:
        uuid = test_files["source"].uuid
        headers = get_api_headers(journalist_api_token)

        # Single-character prefix matching the source
        with assert_query_count(2):
            response = app.get(
                url_for("api2.index", shard_spec=uuid[0]),
                headers=headers,
            )
        assert response.status_code == 200
        assert uuid in response.json["sources"]
        assert len(response.json["items"]) == 3

        # ETag / 304 behavior
        with assert_query_count(2):
            response2 = app.get(
                url_for("api2.index", shard_spec=uuid[0]),
                headers={**headers, "If-None-Match": response.headers["ETag"]},
            )
        assert response2.status_code == 304
        assert response2.calculate_content_length() == 0

        # Two-character prefix matching the source
        response3 = app.get(
            url_for("api2.index", shard_spec=uuid[:2]),
            headers=headers,
        )
        assert response3.status_code == 200
        assert uuid in response3.json["sources"]

        # Two-character prefix that does NOT match
        different_prefix = "aa" if not uuid.startswith("aa") else "bb"
        response4 = app.get(
            url_for("api2.index", shard_spec=different_prefix),
            headers=headers,
        )
        assert response4.status_code == 200
        assert uuid not in response4.json["sources"]

        # Non-hex ("x") or empty prefix matches no sources but journalists are still present
        response5 = app.get(
            url_for("api2.index", shard_spec="x,,"),
            headers=headers,
        )
        assert response5.status_code == 200
        assert response5.json["sources"] == {}
        assert response5.json["items"] == {}
        assert len(response5.json["journalists"]) >= 1


def test_index_with_comma_separated_prefixes(
    journalist_app, test_files, journalist_api_token, app_storage
):
    """
    Verify that a comma-separated shard_spec (e.g. "a,b") matches sources whose
    UUIDs begin with any of the listed prefixes.
    """
    with journalist_app.app_context():
        source2, _ = init_source(app_storage)
        submit(app_storage, source2, 1)
        source2_uuid = source2.uuid

    with journalist_app.test_client() as app:
        uuid = test_files["source"].uuid
        headers = get_api_headers(journalist_api_token)

        shard_spec = f"{uuid[0]},{source2_uuid[0]}"
        response = app.get(
            url_for("api2.index", shard_spec=shard_spec),
            headers=headers,
        )
        assert response.status_code == 200
        assert uuid in response.json["sources"]
        assert source2_uuid in response.json["sources"]
        assert len(response.json["journalists"]) >= 1


def test_index_sharding_disjoint_union(
    journalist_app, test_files, journalist_api_token, app_storage
):
    """
    Verify that two disjoint shards covering the full hex namespace combine to
    equal the global index and share no sources between them.
    """
    with journalist_app.app_context():
        for _ in range(3):
            s, _ = init_source(app_storage)
            submit(app_storage, s, 1)

    with journalist_app.test_client() as app:
        headers = get_api_headers(journalist_api_token)

        global_response = app.get(url_for("api2.index"), headers=headers)
        assert global_response.status_code == 200

        shard_spec_a = ",".join("01234567")
        shard_spec_b = ",".join("89abcdef")

        resp_a = app.get(url_for("api2.index", shard_spec=shard_spec_a), headers=headers)
        resp_b = app.get(url_for("api2.index", shard_spec=shard_spec_b), headers=headers)
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200

        # Union of both shards equals the global index
        combined_sources = {**resp_a.json["sources"], **resp_b.json["sources"]}
        assert combined_sources == global_response.json["sources"]

        # Shards are disjoint
        overlap = set(resp_a.json["sources"].keys()) & set(resp_b.json["sources"].keys())
        assert overlap == set()


def test_index_with_invalid_prefix(journalist_app, test_files, journalist_api_token):
    """
    Verify that a too-long prefix is rejected with HTTP 422, whether it
    appears alone or inside a comma-separated list.
    """
    with journalist_app.test_client() as app:
        uuid = test_files["source"].uuid
        too_long = uuid[0] * 100
        headers = get_api_headers(journalist_api_token)

        # Single too-long prefix
        with assert_query_count(0):
            response = app.get(
                url_for("api2.index", shard_spec=too_long),
                headers=headers,
            )
        assert response.status_code == 422
        assert "malformed request; each prefix must be shorter than" in response.get_data(
            as_text=True
        )

        # Too-long prefix inside a comma-separated list
        response2 = app.get(
            url_for("api2.index", shard_spec=f"a,{too_long}"),
            headers=headers,
        )
        assert response2.status_code == 422
        assert "malformed request; each prefix must be shorter than" in response2.get_data(
            as_text=True
        )


def test_metadata(journalist_app, test_files, test_journo, journalist_api_token):
    """
    Verify POST /metadata response
    """
    with journalist_app.test_client() as app:
        uuid = test_files["source"].uuid
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )

        assert index.status_code == 200
        source_versions = index.json["sources"][uuid]

        # Get the full source
        with assert_query_count(1):
            response = app.post(
                url_for("api2.data"),
                json={"sources": [uuid]},
                headers=get_api_headers(journalist_api_token),
            )
        assert response.status_code == 200
        assert uuid in response.json["sources"]
        source = response.json["sources"][uuid]
        # Verify the source has the same version
        assert json_version(source) == source_versions

        # Get an item
        item_uuid = test_files["submissions"][0].uuid
        with assert_query_count(2):
            response = app.post(
                url_for("api2.data"),
                json={"items": [item_uuid]},
                headers=get_api_headers(journalist_api_token),
            )
        assert response.status_code == 200
        assert item_uuid in response.json["items"]
        # Verify no source metadata is returned
        assert len(response.json["sources"]) == 0
        # Verify the versions are the same
        assert json_version(response.json["items"][item_uuid]) == index.json["items"][item_uuid]

        # Get a journalist
        journalist_uuid = test_journo["uuid"]
        with assert_query_count(1, expect_login=False):
            response = app.post(
                url_for("api2.data"),
                json={"journalists": [journalist_uuid]},
                headers=get_api_headers(journalist_api_token),
            )
        assert response.status_code == 200
        assert journalist_uuid in response.json["journalists"]
        # Verify no source or item metadata is returned
        assert len(response.json["sources"]) == 0
        assert len(response.json["items"]) == 0
        # Verify the versions are the same
        assert (
            json_version(response.json["journalists"][journalist_uuid])
            == index.json["journalists"][journalist_uuid]
        )


def test_item_collision(journalist_app, test_files_with_uuid_collision, journalist_api_token):
    """
    Test the edge case where a ``Submission`` and a ``Reply`` have the same UUID
    in separate tables.
    """
    with journalist_app.test_client() as app:
        # Get an item:
        item_uuid = test_files_with_uuid_collision["submissions"][0].uuid
        with pytest.raises(MultipleResultsFound):  # HTTP 500 in production
            app.post(
                url_for("api2.data"),
                json={"items": [item_uuid]},
                headers=get_api_headers(journalist_api_token),
            )


# Verify POST /sources input validation


@pytest.mark.parametrize(
    "invalid_data",
    [
        "invalid json{",
        "",
        None,
    ],
)
def test_api2_metadata_validation_invalid_json(journalist_app, journalist_api_token, invalid_data):
    """Test that Flask rejects invalid JSON."""
    with journalist_app.test_client() as app:
        response = app.post(
            url_for("api2.data"),
            data=invalid_data,
            headers=get_api_headers(journalist_api_token),
        )
        assert response.status_code == 400


@pytest.mark.parametrize(
    "invalid_request",
    [
        ["not", "a", "dict"],
        "string instead of dict",
        123,
        True,
    ],
)
def test_api2_metadata_validation_non_dict_request(
    journalist_app, journalist_api_token, invalid_request
):
    """Test that non-dict request body returns 400."""
    with journalist_app.test_client() as app:
        response = app.post(
            url_for("api2.data"),
            json=invalid_request,
            headers=get_api_headers(journalist_api_token),
        )
        assert response.status_code == 422
        assert "malformed request" in response.get_data(as_text=True)


@pytest.mark.parametrize(
    "valid_request",
    [
        # Empty but valid
        {"sources": [], "items": []},
        # Only sources
        {"sources": ["uuid1", "uuid2"], "items": ["uuid1", "uuid2"]},
        # Only items
        {"sources": [], "items": ["item1", "item2"]},
        # Both with data
        {
            "sources": ["uuid1", "uuid2"],
            "items": ["item1", "item2"],
        },
    ],
)
def test_api2_metadata_validation_valid_requests(
    journalist_app, journalist_api_token, valid_request
):
    """Test that valid requests pass validation."""
    with journalist_app.test_client() as app:
        response = app.post(
            url_for("api2.data"),
            json=valid_request,
            headers=get_api_headers(journalist_api_token),
        )
        assert response.status_code == 200


def test_api2_invalid_events(
    journalist_app,
    journalist_api_token,
):
    """Test that invalid events are rejected."""
    with journalist_app.test_client() as app:
        valid = {
            "events": [
                {
                    "id": "123456",
                    "type": "reply_sent",
                    "target": {"source_uuid": "abcdef", "version": "uvwxyz"},
                }
            ]
        }

        invalid_type = deepcopy(valid)
        invalid_type["events"][0]["type"] = "foobar"
        response = app.post(
            url_for("api2.data"),
            json=invalid_type,
            headers=get_api_headers(journalist_api_token),
        )
        assert response.status_code == 400
        assert response.json["message"] == "invalid event: 'foobar' is not a valid EventType"

        invalid_target = deepcopy(valid)
        del invalid_target["events"][0]["target"]["source_uuid"]

        response = app.post(
            url_for("api2.data"),
            json=invalid_target,
            headers=get_api_headers(journalist_api_token),
        )
        assert response.status_code == 400
        assert "invalid event target" in response.json["message"]

        no_id = deepcopy(valid)
        del no_id["events"][0]["id"]

        response = app.post(
            url_for("api2.data"),
            json=no_id,
            headers=get_api_headers(journalist_api_token),
        )
        assert response.status_code == 400

        too_many = deepcopy(invalid_type)
        too_many["events"].extend([too_many["events"][0].copy() for _ in range(api2.EVENTS_MAX)])

        response = app.post(
            url_for("api2.data"),
            json=too_many,
            headers=get_api_headers(journalist_api_token),
        )
        assert response.status_code == 429
        assert "MUST NOT include more than" in response.json["message"]


def test_api2_reply_sent(
    journalist_app,
    journalist_api_token,
    test_files,
    test_journo,
):
    """Test processing of the "reply_sent" event."""
    with journalist_app.test_client() as app:
        # Fetch and decrypt the ciphertext of a reply fixture.
        source = test_files["source"]
        reply = test_files["replies"][0]
        reply_res = app.get(
            url_for("api.download_reply", source_uuid=source.uuid, reply_uuid=reply.uuid),
            headers=get_api_headers(journalist_api_token),
        )
        reply_ct = reply_res.data
        reply_pt = decrypt_as_journalist(reply_ct)

        # Fetch the current index.
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200
        source_version = index.json["sources"][source.uuid]

        # Resubmit the reply ciphertext with a new UUID.
        reply2 = {
            "uuid": str(uuid.uuid4()),
            "reply": ascii_armor(reply_ct),
        }
        event = Event(
            id="123456",
            target=SourceTarget(source_uuid=source.uuid, version=source_version),
            type=EventType.REPLY_SENT,
            data=reply2,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][event.id] == [200, None]
        assert reply2["uuid"] in response.json["items"]

        # Check that we get the same plaintext back.
        reply2_res = app.get(
            url_for("api.download_reply", source_uuid=source.uuid, reply_uuid=reply2["uuid"]),
            headers=get_api_headers(journalist_api_token),
        )
        reply2_ct = reply2_res.data
        reply2_pt = decrypt_as_journalist(reply2_ct)
        assert reply2_pt == reply_pt

        # Duplicate reply is acknowledged but not processed again:
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][event.id] == [208, None]
        assert reply2["uuid"] not in response.json["items"]


def test_api2_item_deleted(
    journalist_app,
    journalist_api_token,
    test_files,
    test_journo,
):
    """Test processing of the "item_deleted" event."""
    with journalist_app.test_client() as app:
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )

        assert index.status_code == 200

        # Delete a submission:
        submission_uuid = test_files["submissions"][0].uuid
        submission_version = index.json["items"][submission_uuid]
        event = Event(
            id="123456",
            target=ItemTarget(item_uuid=submission_uuid, version=submission_version),
            type=EventType.ITEM_DELETED,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][event.id] == [200, None]
        assert response.json["items"][event.target.item_uuid] is None
        assert (
            Submission.query.filter(Submission.uuid == event.target.item_uuid).one_or_none() is None
        )

        # Delete a reply:
        reply_uuid = test_files["replies"][0].uuid
        reply_version = index.json["items"][reply_uuid]
        event = Event(
            id="234567",
            target=ItemTarget(item_uuid=reply_uuid, version=reply_version),
            type=EventType.ITEM_DELETED,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][event.id] == [200, None]
        assert response.json["items"][event.target.item_uuid] is None
        assert Reply.query.filter(Reply.uuid == event.target.item_uuid).one_or_none() is None

        # Try to delete something that doesn't exist:
        nonexistent_event = Event(
            id="345678",
            target=ItemTarget(item_uuid=str(uuid.uuid4()), version=reply_version),
            type=EventType.ITEM_DELETED,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(nonexistent_event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][nonexistent_event.id] == [410, None]
        assert nonexistent_event.target.item_uuid not in response.json["items"]


def test_api2_source_deleted(
    journalist_app,
    journalist_api_token,
    test_files,
):
    """Test processing of the "source_deleted" event."""
    with journalist_app.test_client() as app:
        source = test_files["source"]
        source_uuid = source.uuid

        # Try deleting the source with the wrong version
        event = Event(
            id="394758",
            target=SourceTarget(source_uuid=source_uuid, version="a" * VERSION_LEN),
            type=EventType.SOURCE_DELETED,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][event.id][0] == 409
        assert "outdated source" in response.json["events"][event.id][1]

        # Verify source was NOT deleted
        assert Source.query.filter(Source.uuid == source_uuid).one_or_none() is not None

        # Now test deletion with correct version

        # Collect UUIDs of all items in the collection before deletion
        expected_item_uuids = {item.uuid for item in test_files["submissions"]}
        expected_item_uuids.update({item.uuid for item in test_files["replies"]})

        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200
        source_version = index.json["sources"][source_uuid]

        # Delete the source
        event = Event(
            id="365423",
            target=SourceTarget(source_uuid=source_uuid, version=source_version),
            type=EventType.SOURCE_DELETED,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][event.id] == [200, None]
        assert response.json["sources"][source_uuid] is None

        # Verify all items in the collection are returned as deleted
        for item_uuid in expected_item_uuids:
            assert item_uuid in response.json["items"]
            assert response.json["items"][item_uuid] is None

        # Verify source is deleted from database
        assert Source.query.filter(Source.uuid == source_uuid).one_or_none() is None

        # Try to delete a source that doesn't exist
        nonexistent_event = Event(
            id="234567",
            target=SourceTarget(source_uuid=str(uuid.uuid4()), version=source_version),
            type=EventType.SOURCE_DELETED,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(nonexistent_event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][nonexistent_event.id] == [410, None]
        assert "does-not-exist" not in response.json["sources"]


def test_api2_source_conversation_deleted(
    journalist_app,
    journalist_api_token,
    test_files,
):
    """Test processing of the "source_conversation_deleted" event."""
    with journalist_app.test_client() as app:
        source = test_files["source"]
        source_uuid = source.uuid

        # Verify source has submissions and replies
        assert len(test_files["submissions"]) > 0
        assert len(test_files["replies"]) > 0

        # Try to delete conversation with wrong version
        # (intentionally not fetching the correct version)
        event = Event(
            id="498567",
            target=SourceTarget(source_uuid=source_uuid, version="a" * VERSION_LEN),
            type=EventType.SOURCE_CONVERSATION_DELETED,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][event.id][0] == 409
        assert "outdated source" in response.json["events"][event.id][1]

        # Verify submissions and replies were NOT deleted
        for submission in test_files["submissions"]:
            assert (
                Submission.query.filter(Submission.uuid == submission.uuid).one_or_none()
                is not None
            )
        for reply in test_files["replies"]:
            assert Reply.query.filter(Reply.uuid == reply.uuid).one_or_none() is not None

        # Collect UUIDs of all items in the collection before deletion
        expected_item_uuids = {item.uuid for item in test_files["submissions"]}
        expected_item_uuids.update({item.uuid for item in test_files["replies"]})

        # Fetch the current index
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200
        source_version = index.json["sources"][source_uuid]

        # Delete the conversation
        event = Event(
            id="298374",
            target=SourceTarget(source_uuid=source_uuid, version=source_version),
            type=EventType.SOURCE_CONVERSATION_DELETED,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][event.id] == [200, None]
        # Source should still exist, so not None
        assert response.json["sources"][source_uuid] is not None

        # Verify all items in the collection are returned as deleted
        for item_uuid in expected_item_uuids:
            assert item_uuid in response.json["items"]
            assert response.json["items"][item_uuid] is None

        # Verify source still exists but submissions/replies are deleted from database
        assert Source.query.filter(Source.uuid == source_uuid).one_or_none() is not None
        for submission in test_files["submissions"]:
            assert Submission.query.filter(Submission.uuid == submission.uuid).one_or_none() is None
        for reply in test_files["replies"]:
            assert Reply.query.filter(Reply.uuid == reply.uuid).one_or_none() is None


def test_api2_source_starred(
    journalist_app,
    journalist_api_token,
    test_files,
):
    """Test processing of the "source_starred" event."""
    with journalist_app.test_client() as app:
        source = test_files["source"]
        source_id = source.id
        source_uuid = source.uuid

        # Fetch the current index
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200
        source_version = index.json["sources"][source_uuid]

        # Star the source
        event = Event(
            id="123456",
            target=SourceTarget(source_uuid=source_uuid, version=source_version),
            type=EventType.SOURCE_STARRED,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][event.id] == [200, None]
        assert source_uuid in response.json["sources"]

        # Verify the source is starred in the response
        source_data = response.json["sources"][source_uuid]
        assert source_data["is_starred"] is True

        assert SourceStar.query.filter(SourceStar.source_id == source_id).one().starred


def test_api2_source_unstarred(
    journalist_app,
    journalist_api_token,
    test_files,
):
    """Test processing of the "source_unstarred" event."""
    with journalist_app.test_client() as app:
        source = test_files["source"]
        source_id = source.id
        source_uuid = source.uuid

        # Star the source first using API v1
        app.post(
            url_for("api.add_star", source_uuid=source_uuid),
            headers=get_api_headers(journalist_api_token),
        )
        assert SourceStar.query.filter(SourceStar.source_id == source_id).one().starred is True

        # Fetch the current index
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200
        source_version = index.json["sources"][source_uuid]

        # Unstar the source
        event = Event(
            id="123456",
            target=SourceTarget(source_uuid=source_uuid, version=source_version),
            type=EventType.SOURCE_UNSTARRED,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][event.id] == [200, None]
        assert source_uuid in response.json["sources"]

        # Verify the source is not starred in the response
        source_data = response.json["sources"][source_uuid]
        assert source_data["is_starred"] is False

        assert SourceStar.query.filter(SourceStar.source_id == source_id).one().starred is False


def test_api2_item_seen(
    journalist_app,
    journalist_api_token,
    test_files,
):
    """Test processing of the "item_seen" event."""
    with journalist_app.test_client() as app:
        source = test_files["source"]
        source_uuid = source.uuid

        # Verify we have test data
        assert len(test_files["submissions"]) >= 1
        submission = test_files["submissions"][0]
        submission_uuid = submission.uuid

        # Fetch the current index
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200
        item_version = index.json["items"][submission_uuid]

        # Mark the submission as seen
        event = Event(
            id="123456",
            target=ItemTarget(item_uuid=submission_uuid, version=item_version),
            type=EventType.ITEM_SEEN,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][event.id] == [200, None]
        assert source_uuid in response.json["sources"]
        assert submission_uuid in response.json["items"]

        # Verify the submission is marked as seen in the database
        updated_submission = Submission.query.filter(Submission.uuid == submission_uuid).one()
        assert updated_submission.downloaded is True

        # Try to mark seen an item that doesn't exist
        no_such_item_event = Event(
            id="234567",
            target=ItemTarget(item_uuid=str(uuid.uuid4()), version=item_version),
            type=EventType.ITEM_SEEN,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(no_such_item_event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][no_such_item_event.id][0] == 404
        assert "could not find item" in response.json["events"][no_such_item_event.id][1]


def test_api2_item_unseen(
    journalist_app,
    journalist_api_token,
    test_files,
):
    """Test processing of the "item_unseen" event."""

    with journalist_app.test_client() as app:
        source = test_files["source"]
        source_uuid = source.uuid

        submission = test_files["submissions"][0]
        submission_uuid = submission.uuid

        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200
        current_item_version = index.json["items"][submission_uuid]

        seen_event = Event(
            id="345678",
            target=ItemTarget(item_uuid=submission_uuid, version=current_item_version),
            type=EventType.ITEM_SEEN,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(seen_event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][seen_event.id] == [200, None]

        refreshed_index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert refreshed_index.status_code == 200
        unseen_version = refreshed_index.json["items"][submission_uuid]

        unseen_event = Event(
            id="456789",
            target=ItemTarget(item_uuid=submission_uuid, version=unseen_version),
            type=EventType.ITEM_UNSEEN,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(unseen_event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][unseen_event.id] == [200, None]
        assert source_uuid in response.json["sources"]
        assert submission_uuid in response.json["items"]

        updated_submission = Submission.query.filter(Submission.uuid == submission_uuid).one()
        assert updated_submission.downloaded is False
        assert len(updated_submission.seen_files) == 0
        assert len(updated_submission.seen_messages) == 0

        no_such_item_event = Event(
            id="567890",
            target=ItemTarget(item_uuid=str(uuid.uuid4()), version=unseen_version),
            type=EventType.ITEM_UNSEEN,
        )
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(no_such_item_event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.json["events"][no_such_item_event.id][0] == 404
        assert "could not find item" in response.json["events"][no_such_item_event.id][1]


def test_api2_idempotence_period(journalist_app):
    """
    `IDEMPOTENCE_PERIOD` MUST be greater than or equal to
    `sdconfig.SecureDropConfig.SESSION_LIFETIME`.  NB. Black/Ruff insists on
    reversing the >= comparison to <=.
    """

    assert journalist_app.config["SESSION_LIFETIME"] <= api2.events.IDEMPOTENCE_PERIOD


def test_api2_event_ordering(journalist_app, journalist_api_token, test_files):
    """
    If two `item_deleted` events for the same item arrive out of order, the
    numerically later event must observe that the item is already gone by the
    time it's processed.
    """
    with journalist_app.test_client() as app:
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200

        submission_uuid = test_files["submissions"][0].uuid
        item_version = index.json["items"][submission_uuid]

        # Two `item_deleted` events targeting the same item:
        e2 = Event(
            id="3419026047977394171",
            target=ItemTarget(item_uuid=submission_uuid, version=item_version),
            type=EventType.ITEM_DELETED,
        )
        e1 = Event(
            id="3419026047977394170",  # client sends as string; server orders as integer
            target=ItemTarget(item_uuid=submission_uuid, version=item_version),
            type=EventType.ITEM_DELETED,
        )

        # Send them out of order:
        resp = app.post(
            url_for("api2.data"),
            json={"events": [asdict(e2), asdict(e1)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert resp.status_code == 200

        # Event `1` (sent second, processed first) deletes the item.
        assert resp.json["events"]["3419026047977394170"] == [200, None]

        # Event "2" (sent first, processed second) finds it missing.
        assert resp.json["events"]["3419026047977394171"][0] == 410


def test_api2_source_conversation_deleted_resubmission(
    journalist_app,
    journalist_api_token,
    test_files,
):
    """
    A rejected event (409) MUST be handled (200) if corrected and resubmitted.
    An accepted (i.e., corrected) event MUST be acknowledged (208) if
    resubmitted.
    """
    with journalist_app.test_client() as app:
        source = test_files["source"]
        source_uuid = source.uuid

        # 1. Submit with the wrong version --> Conflict (409).
        event = Event(
            id="600100",
            target=SourceTarget(source_uuid=source_uuid, version="a" * VERSION_LEN),
            type=EventType.SOURCE_CONVERSATION_DELETED,
        )
        res1 = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert res1.status_code == 200
        assert res1.json["events"][event.id][0] == 409

        # Confirm that nothing has been deleted.
        for submission in test_files["submissions"]:
            assert (
                Submission.query.filter(Submission.uuid == submission.uuid).one_or_none()
                is not None
            )
        for reply in test_files["replies"]:
            assert Reply.query.filter(Reply.uuid == reply.uuid).one_or_none() is not None

        expected_item_uuids = {item.uuid for item in test_files["submissions"]}
        expected_item_uuids.update({item.uuid for item in test_files["replies"]})

        # 2. Resubmit the same event with the correct version --> OK (200).
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200
        correct_version = index.json["sources"][source_uuid]

        corrected_event = Event(
            id=event.id,
            target=SourceTarget(source_uuid=source_uuid, version=correct_version),
            type=event.type,
        )
        res2 = app.post(
            url_for("api2.data"),
            json={"events": [asdict(corrected_event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert res2.status_code == 200
        assert res2.json["events"][corrected_event.id] == [200, None]

        # Confirm that items are returned as deleted.
        assert res2.json["sources"][source_uuid] is not None
        for item_uuid in expected_item_uuids:
            assert item_uuid in res2.json["items"]
            assert res2.json["items"][item_uuid] is None

        # Confirm that items have actually been deleted.
        for submission in test_files["submissions"]:
            assert Submission.query.filter(Submission.uuid == submission.uuid).one_or_none() is None
        for reply in test_files["replies"]:
            assert Reply.query.filter(Reply.uuid == reply.uuid).one_or_none() is None
        assert Source.query.filter(Source.uuid == source_uuid).one_or_none() is not None

        # 3. Resubmit the same event again --> Already Reported (208).
        res3 = app.post(
            url_for("api2.data"),
            json={"events": [asdict(corrected_event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert res3.status_code == 200
        assert res3.json["events"][corrected_event.id][0] == 208


def test_api2_reply_sent_then_requested_item_is_deduped(
    journalist_app,
    journalist_api_token,
    test_files,
):
    """
    When a reply is created by a `REPLY_SENT` event and the same UUID is also
    requested in the same `BatchRequest`, the request should succeed (200) and
    return the reply once.
    """
    with journalist_app.test_client() as app:
        # Fetch an existing reply so that we can resubmit it.
        source = test_files["source"]
        reply = test_files["replies"][0]
        reply_res = app.get(
            url_for("api.download_reply", source_uuid=source.uuid, reply_uuid=reply.uuid),
            headers=get_api_headers(journalist_api_token),
        )
        reply_ct = reply_res.data
        armored_ct = ascii_armor(reply_ct)

        # Get current source version to build a valid "reply_sent" event.
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200
        source_version = index.json["sources"][source.uuid]

        new_reply_uuid = str(uuid.uuid4())
        event = Event(
            id="987654321",
            target=SourceTarget(source_uuid=source.uuid, version=source_version),
            type=EventType.REPLY_SENT,
            data={"uuid": new_reply_uuid, "reply": armored_ct},
        )

        # The same batch both creates the reply (`events`) and requests it (`items`).
        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)], "items": [new_reply_uuid]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.status_code == 200
        assert response.json["events"][event.id] == [200, None]
        assert new_reply_uuid in response.json["items"]
        assert response.json["items"][new_reply_uuid] is not None


@pytest.mark.parametrize("minor", [0, 1, 2, 3])
def test_api_minor_versions(journalist_app, journalist_api_token, test_files, minor):
    """
    Verify that the API response shape changes according to the documented
    values of securedrop.journalist_app.api2.API_MINOR_VERSION.
    """
    headers = get_api_headers(journalist_api_token)
    headers["Prefer"] = f"securedrop={minor}"

    with journalist_app.test_client() as app:
        index = app.get(url_for("api2.index"), headers=headers)
        assert index.status_code == 200

        data = index.json

        # 1. `Index` and `BatchResponse` include `journalists`
        if minor < 1:
            assert "journalists" not in data
        else:
            assert "journalists" in data
            # At least one journalist should exist in the fixtures
            assert len(data["journalists"]) >= 1

        # 2. `Reply` and `Submission` objects include `interaction_count`
        item_uuid = test_files["submissions"][0].uuid
        resp = app.post(
            url_for("api2.data"),
            json={"items": [item_uuid]},
            headers=headers,
        )
        assert resp.status_code == 200

        item_obj = resp.json["items"][item_uuid]
        if minor < 2:
            assert "interaction_count" not in item_obj
        else:
            assert "interaction_count" in item_obj

        # 3. `BatchRequest` accepts `events` to process, with results returned
        #    in `BatchResponse.events`
        if minor >= 3:
            event = {
                "id": "123456",
                "type": "item_seen",
                "target": {
                    "item_uuid": test_files["submissions"][0].uuid,
                    "version": data["items"][test_files["submissions"][0].uuid],
                },
            }

            resp = app.post(url_for("api2.data"), json={"events": [event]}, headers=headers)
            assert resp.status_code == 200
            assert "events" in resp.json
            assert event["id"] in resp.json["events"]

        else:
            assert "events" not in resp.json


def test_api2_source_conversation_truncated(
    journalist_app,
    journalist_api_token,
    test_files,
):
    """
    Test processing of the "source_conversation_truncated" event.
    Items with interaction_count <= upper_bound must be deleted.
    Items with interaction_count > upper_bound must remain.
    """
    with journalist_app.test_client() as app:
        source = test_files["source"]

        # Ensure we have submissions/replies and interaction_count fields
        assert len(test_files["submissions"]) >= 1
        assert len(test_files["replies"]) >= 1

        # Fetch index to get current versions and interaction counts
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200

        # Build a map of item_uuid -> interaction_count
        item_uuids = [item.uuid for item in (test_files["submissions"] + test_files["replies"])]

        batch_resp = app.post(
            url_for("api2.data"),
            json={"items": item_uuids},
            headers=get_api_headers(journalist_api_token),
        )
        assert batch_resp.status_code == 200
        data = batch_resp.json

        initial_counts = {
            item_uuid: item["interaction_count"] for item_uuid, item in data["items"].items()
        }

        # Choose a bound that deletes some but not all items
        # Pick the median interaction_count so we get both outcomes
        sorted_counts = sorted(initial_counts.values())
        upper_bound = sorted_counts[len(sorted_counts) // 2]

        source_version = index.json["sources"][source.uuid]

        event = Event(
            id="999001",
            target=SourceTarget(source_uuid=source.uuid, version=source_version),
            type=EventType.SOURCE_CONVERSATION_TRUNCATED,
            data={"upper_bound": upper_bound},
        )

        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.status_code == 200

        status_code, msg = response.json["events"][event.id]
        # Because some deletes may fail (simulated) and some succeed, the handler
        # returns 200 if all succeed.
        # The test_files fixtures never cause delete_file_object() to raise,
        # so OK (200) is expected.
        assert status_code == 200

        # Verify item-wise results
        returned_items = response.json["items"]
        assert isinstance(returned_items, dict)

        for item_uuid, count in initial_counts.items():
            if count <= upper_bound:
                # Must be returned as deleted: {uuid: None}
                assert item_uuid in returned_items
                assert returned_items[item_uuid] is None
                # Also confirm removal in DB
                assert (
                    Submission.query.filter(Submission.uuid == item_uuid).one_or_none()
                    or Reply.query.filter(Reply.uuid == item_uuid).one_or_none()
                ) is None
            else:
                # Must not be deleted
                assert (
                    Submission.query.filter(Submission.uuid == item_uuid).one_or_none()
                    or Reply.query.filter(Reply.uuid == item_uuid).one_or_none()
                ) is not None

        # Source must still exist
        assert Source.query.filter(Source.uuid == source.uuid).one_or_none() is not None

        # Resubmission must yield "Already Reported" (208)
        res2 = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert res2.status_code == 200
        assert res2.json["events"][event.id][0] == 208


def test_api2_source_conversation_seen(
    journalist_app,
    journalist_api_token,
    test_files,
):
    """
    Test processing of the "source_conversation_seen" event.
    Items with interaction_count <= upper_bound must be marked as seen.
    Items with interaction_count > upper_bound must remain unseen.
    """
    with journalist_app.test_client() as app:
        source = test_files["source"]

        assert len(test_files["submissions"]) >= 1
        assert len(test_files["replies"]) >= 1

        # Fetch index to get current versions
        index = app.get(
            url_for("api2.index"),
            headers=get_api_headers(journalist_api_token),
        )
        assert index.status_code == 200

        # Build a map of item_uuid -> interaction_count
        item_uuids = [item.uuid for item in (test_files["submissions"] + test_files["replies"])]

        batch_resp = app.post(
            url_for("api2.data"),
            json={"items": item_uuids},
            headers=get_api_headers(journalist_api_token),
        )
        assert batch_resp.status_code == 200
        data = batch_resp.json

        initial_counts = {
            item_uuid: item["interaction_count"] for item_uuid, item in data["items"].items()
        }

        # Choose a bound that marks some but not all items as seen
        sorted_counts = sorted(initial_counts.values())
        upper_bound = sorted_counts[len(sorted_counts) // 2]

        source_version = index.json["sources"][source.uuid]

        event = Event(
            id="888001",
            target=SourceTarget(source_uuid=source.uuid, version=source_version),
            type=EventType.SOURCE_CONVERSATION_SEEN,
            data={"upper_bound": upper_bound},
        )

        response = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert response.status_code == 200
        assert response.json["events"][event.id] == [200, None]

        # Items within bound must be marked seen; items outside must not be
        for item_uuid, count in initial_counts.items():
            submission = Submission.query.filter(Submission.uuid == item_uuid).one_or_none()

            if count <= upper_bound:
                assert item_uuid in response.json["items"]
                assert response.json["items"][item_uuid] is not None
                if submission is not None:
                    assert submission.seen is True
            elif submission is not None:
                assert submission.seen is False

        # Resubmission must yield "Already Reported" (208)
        res2 = app.post(
            url_for("api2.data"),
            json={"events": [asdict(event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert res2.status_code == 200
        assert res2.json["events"][event.id][0] == 208

        # Non-existent source must yield Gone (410)
        gone_event = Event(
            id="888002",
            target=SourceTarget(source_uuid=str(uuid4()), version=source_version),
            type=EventType.SOURCE_CONVERSATION_SEEN,
            data={"upper_bound": upper_bound},
        )
        res3 = app.post(
            url_for("api2.data"),
            json={"events": [asdict(gone_event)]},
            headers=get_api_headers(journalist_api_token),
        )
        assert res3.status_code == 200
        assert res3.json["events"][gone_event.id][0] == 410
