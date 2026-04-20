from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum, auto
from typing import (
    Any,
    NewType,
)
from uuid import UUID

Record = NewType("Record", dict[str, Any])
Version = NewType("Version", str)

VERSION_LEN = 64  # hex digits


# NB.  Ideally we'd have a generic UUID[T], but the semantics don't change
# before mypy 1.12, which is incompatible with our use elsewhere of sqlmypy.
ReplyUUID = NewType("ReplyUUID", str)
SourceUUID = NewType("SourceUUID", str)
ItemUUID = NewType("ItemUUID", str)
JournalistUUID = NewType("JournalistUUID", str)


EventID = NewType("EventID", str)  # int, but opaque on the wire


class EventType(StrEnum):
    REPLY_SENT = auto()
    ITEM_DELETED = auto()
    ITEM_SEEN = auto()
    ITEM_UNSEEN = auto()
    SOURCE_DELETED = auto()
    SOURCE_CONVERSATION_DELETED = auto()
    SOURCE_CONVERSATION_TRUNCATED = auto()
    SOURCE_STARRED = auto()
    SOURCE_UNSTARRED = auto()
    SOURCE_CONVERSATION_SEEN = auto()


class EventStatusCode(IntEnum):
    Processing = 102
    OK = 200
    # We already saw and processed this event
    AlreadyReported = 208
    BadRequest = 400
    # The target UUID doesn't exist (non-deletion requests)
    NotFound = 404
    # Provided version is out of date and it was a deletion request
    Conflict = 409
    # The target UUID doesn't exist and it was a deletion request
    Gone = 410
    InternalServerError = 500
    NotImplemented = 501


EventStatus = tuple[EventStatusCode, str | None]


@dataclass
class Index:
    # Source metadata, optionally filtered by shard spec:
    sources: dict[SourceUUID, Version] = field(default_factory=dict)
    items: dict[ItemUUID, Version] = field(default_factory=dict)

    # Non-source metadata (always returned):
    journalists: dict[JournalistUUID, Version] = field(default_factory=dict)


@dataclass(frozen=True)
class Target:
    """Base class for `<Resource>Target` dataclasses, to make their union usable
    at runtime.  Subclass at least with:

        <resource>_uuid: <Resource>UUID

    """

    version: Version

    def __post_init__(self) -> None:
        version = str(self.version)

        if len(version) != VERSION_LEN:
            raise ValueError(f"version must have {VERSION_LEN} hex digits")

        try:
            int(version, 16)
        except ValueError:
            raise ValueError("version must be hex-encoded")


@dataclass(frozen=True)
class SourceTarget(Target):
    source_uuid: SourceUUID

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.source_uuid:
            raise ValueError("source_uuid must be non-empty")

        try:
            UUID(str(self.source_uuid))
        except ValueError:
            raise ValueError(f"invalid source UUID: {self.source_uuid}")


@dataclass(frozen=True)
class ItemTarget(Target):
    item_uuid: ItemUUID

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.item_uuid:
            raise ValueError("item_uuid must be non-empty")

        try:
            UUID(str(self.item_uuid))
        except ValueError:
            raise ValueError(f"invalid item UUID: {self.item_uuid}")


@dataclass(frozen=True)
class EventData:
    """
    Base class for `<EventType>Data` dataclasses, to make their union usable at
    runtime.  For non-empty events, subclass and add to `EVENT_TYPES`.
    """


@dataclass(frozen=True)
class ReplySentData(EventData):
    uuid: ReplyUUID
    reply: str

    def __post_init__(self) -> None:
        try:
            UUID(str(self.uuid))
        except ValueError:
            raise ValueError(f"invalid reply UUID: {self.uuid}")

        if not self.reply:
            raise ValueError("reply must be a non-empty string")


@dataclass(frozen=True)
class SourceConversationTruncatedData(EventData):
    # An upper bound of n means "delete items with interaction counts (sparsely)
    # up to and including n".
    upper_bound: int

    def __post_init__(self) -> None:
        if self.upper_bound < 0:
            raise ValueError("upper_bound must be non-negative")


@dataclass(frozen=True)
class SourceConversationSeenData(EventData):
    # An upper bound of n means "mark as seen items with interaction counts (sparsely)
    # up to and including n".
    upper_bound: int

    def __post_init__(self) -> None:
        if self.upper_bound < 0:
            raise ValueError("upper_bound must be non-negative")


EVENT_TYPES = {
    EventType.REPLY_SENT: (SourceTarget, ReplySentData),
    EventType.ITEM_DELETED: (ItemTarget, None),
    EventType.ITEM_SEEN: (ItemTarget, None),
    EventType.SOURCE_DELETED: (SourceTarget, None),
    EventType.SOURCE_CONVERSATION_DELETED: (SourceTarget, None),
    EventType.SOURCE_CONVERSATION_TRUNCATED: (SourceTarget, SourceConversationTruncatedData),
    EventType.SOURCE_STARRED: (SourceTarget, None),
    EventType.SOURCE_UNSTARRED: (SourceTarget, None),
    EventType.SOURCE_CONVERSATION_SEEN: (SourceTarget, SourceConversationSeenData),
}


@dataclass(frozen=True)
class Event:
    id: EventID
    target: Target | Mapping[str, Any]
    type: EventType
    data: EventData | Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        # ID must be usable as an int (for snowflake ordering; see section
        # "Snowflake IDs" in `API2.md`):
        if not str(self.id).isdigit():
            raise ValueError(f"event ID must be an integer string: {self.id}")

        # Normalize type:
        if not isinstance(self.type, EventType):
            object.__setattr__(self, "type", EventType(self.type))

        # Look up the expected types for this event type:
        expected_target_type, expected_data_type = EVENT_TYPES[self.type]

        # Normalize target:
        target = self.target
        if not isinstance(target, expected_target_type):
            if not isinstance(target, Mapping):
                raise TypeError(f"invalid event target for type {self.type}: {target!r}")

            try:
                target = expected_target_type(**target)
            except (TypeError, ValueError):
                raise TypeError(f"invalid event target for type {self.type}")

            object.__setattr__(self, "target", target)

        # Normalize data:
        data = self.data
        if data is None and expected_data_type is None:
            return
        elif expected_data_type is None:
            object.__setattr__(self, "data", None)
            return

        # If it's already an `EventData` dataclass, validate it:
        if isinstance(data, EventData):
            if not isinstance(data, expected_data_type):
                raise TypeError(f"invalid event data for type {self.type}")
            return

        # If it's a mapping, try to instantiate an `EventData` dataclass:
        elif isinstance(data, Mapping):
            try:
                data_obj = expected_data_type(**data)
            except (TypeError, ValueError):
                raise TypeError(f"invalid event data for type {self.type}")
            object.__setattr__(self, "data", data_obj)

        else:
            raise TypeError(f"invalid event data for type {self.type}")


@dataclass(frozen=True)
class EventResult:
    event_id: EventID
    status: EventStatus

    # Changed sources/items, return {<uuid>: None} to indicate deletion:
    sources: dict[SourceUUID, Record | None] = field(default_factory=dict)
    items: dict[ItemUUID, Record | None] = field(default_factory=dict)


@dataclass(frozen=True)
class BatchRequest:
    # Source metadata:
    sources: set[SourceUUID] = field(default_factory=set)
    items: set[ItemUUID] = field(default_factory=set)

    # Non-source metadata:
    journalists: set[JournalistUUID] = field(default_factory=set)

    # Events submitted by the client:
    events: list[Event | Mapping[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        def _normalize_uuids(raw: Iterable[Any], wrap: Callable) -> set:
            try:
                return {wrap(x) for x in raw}
            except TypeError:
                raise TypeError("expected an iterable")

        object.__setattr__(self, "sources", _normalize_uuids(self.sources, SourceUUID))
        object.__setattr__(self, "items", _normalize_uuids(self.items, ItemUUID))
        object.__setattr__(self, "journalists", _normalize_uuids(self.journalists, JournalistUUID))

        normalized_events: list[Event | Mapping[str, Any]] = []
        for e in self.events:
            if isinstance(e, Event | Mapping):
                normalized_events.append(e)
            else:
                raise TypeError("BatchRequest.events must contain Event or Mapping instances")
        object.__setattr__(self, "events", normalized_events)


@dataclass
class BatchResponse:
    """
    In dictionaries keyed by UUID, an entry {<uuid>: None} indicates deletion.
    """

    # Source metadata:
    sources: dict[SourceUUID, Record | None] = field(default_factory=dict)
    items: dict[ItemUUID, Record | None] = field(default_factory=dict)

    # Non-source metadata:
    journalists: dict[JournalistUUID, Record | None] = field(default_factory=dict)

    # Events processed by the server:
    events: dict[EventID, EventStatus] = field(default_factory=dict)
