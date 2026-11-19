"""
This module contains helper functions factored out of the v1 Journalist API
(journalist_app.api) and shared with the v2 Journalist API (journalist_app.api2)
"""

import hashlib
import os
from collections.abc import Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import UUID

from db import db
from flask import abort, json, request
from journalist_app.api2.types import Index, Version
from journalist_app.sessions import session
from models import (
    EagerQuery,
    InvalidUUID,
    Reply,
    SeenReply,
    Source,
    eager_query,
)
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from store import Storage

PREFIX_MAX_LEN = inspect(Source).columns["uuid"].type.length

# A ``shard_spec`` is expanded into one ``LIKE`` per prefix, joined with
# ``or_()``.  SQLite compiles each ``OR`` into another level of expression, so a
# spec of a thousand prefixes makes the query fail with "Expression tree is too
# large (maximum depth 1000)" -- a 500 for an otherwise well-formed request.
# The reference client shards into 16 (one per hex digit); 64 leaves plenty of
# room for a client that chooses finer sharding while keeping the query well
# below SQLite's limit.
PREFIXES_MAX = 64

# Magic numbers to avoid having to define an `IntEnum` somewhere that can be
# imported from `securedrop.models`:
#
# 0. Initial implementation
# 1. `Index` and `BatchResponse` include `journalists`
# 2. `Reply` and `Submission` objects include `interaction_count`
# 3. `BatchRequest` accepts `events` to process, with results returned in
#    `BatchResponse.events`
# 4. `/api/v1/token` provides sync hints for client-specified sharding of
#    `Index`
#
# When you add a new version here, make sure to add it to
# `tests.test_journalist_api2.test_api_minor_versions()` too.
API_MINOR_VERSION = 4  # 2.x


def get_request_minor_version(strict: bool = False) -> int:
    """
    By default, returns the value of x in the header ``Prefer: securedrop=x`` if
    it is present and within the range ``[0, API_MINOR_VERSION]``; otherwise
    returns ``API_MINOR_VERSION``.

    In ``strict`` mode, returns -1 if this header is missing, indicating a
    pre-v2 client that cannot negotiate minor-version compatibility.
    """
    if strict and "Prefer" not in request.headers:
        return -1

    try:
        prefer = request.headers.get("Prefer", f"securedrop={API_MINOR_VERSION}")
        minor_version = int(prefer.split("=")[1])
        if 0 <= minor_version <= API_MINOR_VERSION:
            return minor_version
        else:
            return API_MINOR_VERSION
    except (IndexError, ValueError):
        return API_MINOR_VERSION


def json_version(d: Mapping) -> Version:
    """
    Calculate the version (BLAKE2s digest) of the normalized JSON representation
    of the dictionary ``d``.

    We use BLAKE2s here because SHA-256 is too slow (we don't care about
    cryptographic security) and CRC-32 is too collision-prone (we're not merely
    checksumming for transmission integrity).
    """
    s = json.dumps(d, separators=[",", ":"], sort_keys=True)
    b = s.encode("utf-8")
    return Version(hashlib.blake2s(b).hexdigest())


def get_index_dict(minor: int, prefixes: list[str] | None = None) -> dict:
    """
    APIv2-facing interface for getting the index for the specified minor version
    and (if specified) prefixes.
    """
    index = Index()

    source_query: EagerQuery = eager_query("Source")
    if prefixes:
        if len(prefixes) > PREFIXES_MAX:
            abort(
                422,
                f"malformed request; a shard_spec MUST NOT contain more than "
                f"{PREFIXES_MAX} prefixes",
            )

        for prefix in prefixes:
            if len(prefix) >= PREFIX_MAX_LEN:
                abort(
                    422,
                    f"malformed request; each prefix must be shorter than {PREFIX_MAX_LEN} "
                    f"characters",
                )

        source_query = source_query.filter(
            or_(*(Source.uuid.startswith(prefix) for prefix in prefixes))
        )

    for source in source_query.all():
        index.sources[source.uuid] = json_version(source.to_api_v2(minor))
        for item in source.collection:
            index.items[item.uuid] = json_version(item.to_api_v2(minor))

    journalist_query: EagerQuery = eager_query("Journalist")
    for journalist in journalist_query.all():
        index.journalists[journalist.uuid] = json_version(journalist.to_api_v2(minor))

    # We want to enforce the *current* shape of `Index`, so we should wait until
    # we have the dictionary representation to delete top-level keys unsupported
    # by the current minor version.
    index_dict = asdict(index)
    if minor < 1:
        del index_dict["journalists"]

    return index_dict


def get_index_hints() -> dict:
    """
    APIv1-facing interface for getting *only* the hints of the current index,
    without negotiation of either the minor version or sharding.
    """
    minor = API_MINOR_VERSION
    index_dict = get_index_dict(minor)

    return {
        "version": json_version(index_dict),
        "sources": len(index_dict["sources"]),
        "items": len(index_dict["items"]),
    }


def save_reply(source: Source, data: dict) -> Reply:
    source.interaction_count += 1
    filename = Storage.get_default().save_pre_encrypted_reply(
        source.filesystem_id,
        source.interaction_count,
        source.journalist_filename,
        data["reply"],
    )

    # We only save the stored reply's basename and not the whole storage path
    filename = os.path.basename(filename)

    reply = Reply(session.get_user(), source, filename, Storage.get_default())

    reply_uuid = data.get("uuid")
    if reply_uuid is not None:
        try:
            UUID(reply_uuid)
            reply.uuid = reply_uuid
        except ValueError:
            raise InvalidUUID

    try:
        db.session.add(reply)
        seen_reply = SeenReply(reply=reply, journalist=session.get_user())
        db.session.add(seen_reply)
        db.session.add(source)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        raise e

    return reply


def mark_source_deleted(cols_selected: list[str]) -> None:
    now = datetime.now(UTC)
    sources = Source.query.filter(Source.filesystem_id.in_(cols_selected))
    sources.update({Source.deleted_at: now}, synchronize_session="fetch")
    db.session.commit()
