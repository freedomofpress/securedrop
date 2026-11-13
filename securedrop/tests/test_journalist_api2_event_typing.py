from uuid import uuid4

import pytest
from journalist_app.api2.types import (
    VERSION_LEN,
    Event,
    EventType,
    ItemTarget,
    ReplySentData,
    SourceConversationTruncatedData,
    SourceTarget,
)

VALID_VERSION = "a" * VERSION_LEN
VALID_SOURCE_UUID = str(uuid4())
VALID_ITEM_UUID = str(uuid4())
VALID_REPLY_UUID = str(uuid4())


def test_invalid_id_non_digit():
    """Event ID must be a digit string."""
    with pytest.raises(ValueError, match="event ID must be an integer string"):
        Event(
            id="abc123",
            target=SourceTarget(source_uuid=VALID_SOURCE_UUID, version=VALID_VERSION),
            type=EventType.SOURCE_STARRED,
        )


@pytest.mark.parametrize("event_id", [123456, 1.5, True, float("inf")])
def test_invalid_id_non_string(event_id):
    """Event ID must be a string, not a JSON number or boolean."""
    with pytest.raises(ValueError, match="event ID must be an integer string"):
        Event(
            id=event_id,
            target=SourceTarget(source_uuid=VALID_SOURCE_UUID, version=VALID_VERSION),
            type=EventType.SOURCE_STARRED,
        )


def test_wrong_target_type_item_for_source_event():
    """Source events must have SourceTarget, not ItemTarget."""
    with pytest.raises(TypeError, match="invalid event target for type source_starred"):
        Event(
            id="123456",
            target=ItemTarget(item_uuid=VALID_ITEM_UUID, version=VALID_VERSION),
            type=EventType.SOURCE_STARRED,
        )


def test_wrong_target_type_source_for_item_event():
    """Item events must have ItemTarget, not SourceTarget."""
    with pytest.raises(TypeError, match="invalid event target for type item_deleted"):
        Event(
            id="123456",
            target=SourceTarget(source_uuid=VALID_SOURCE_UUID, version=VALID_VERSION),
            type=EventType.ITEM_DELETED,
        )


def test_wrong_target_mapping_item_keys_for_source_event():
    """Source events reject mappings with item_uuid instead of source_uuid."""
    with pytest.raises(TypeError, match="invalid event target for type source_starred"):
        Event(
            id="123456",
            target={"item_uuid": VALID_ITEM_UUID, "version": VALID_VERSION},
            type=EventType.SOURCE_STARRED,
        )


def test_wrong_target_mapping_source_keys_for_item_event():
    """Item events reject mappings with source_uuid instead of item_uuid."""
    with pytest.raises(TypeError, match="invalid event target for type item_deleted"):
        Event(
            id="123456",
            target={"source_uuid": VALID_SOURCE_UUID, "version": VALID_VERSION},
            type=EventType.ITEM_DELETED,
        )


def test_target_not_mapping_wrong_type():
    """Target must be a Target subclass or Mapping."""
    with pytest.raises(TypeError, match="invalid event target for type source_starred"):
        Event(
            id="123456",
            target="not a target",  # type: ignore[arg-type]
            type=EventType.SOURCE_STARRED,
        )


def test_data_discarded_when_not_expected():
    """Data is silently discarded for events that don't expect it."""
    event = Event(
        id="123456",
        target=ItemTarget(item_uuid=VALID_ITEM_UUID, version=VALID_VERSION),
        type=EventType.ITEM_DELETED,
        data={"unexpected": "data"},
    )
    assert event.data is None


def test_wrong_event_data_subclass():
    """Providing wrong EventData subclass raises TypeError."""
    wrong_data = SourceConversationTruncatedData(upper_bound=5)
    with pytest.raises(TypeError, match="invalid event data for type reply_sent"):
        Event(
            id="123456",
            target=SourceTarget(source_uuid=VALID_SOURCE_UUID, version=VALID_VERSION),
            type=EventType.REPLY_SENT,
            data=wrong_data,
        )


def test_data_mapping_missing_required_fields():
    """Data mapping with missing required fields raises TypeError."""
    with pytest.raises(TypeError, match="invalid event data for type reply_sent"):
        Event(
            id="123456",
            target=SourceTarget(source_uuid=VALID_SOURCE_UUID, version=VALID_VERSION),
            type=EventType.REPLY_SENT,
            data={"wrong_field": "value"},
        )


def test_data_none_when_required():
    """Missing data for events that require it raises TypeError."""
    with pytest.raises(TypeError, match="invalid event data for type reply_sent"):
        Event(
            id="123456",
            target=SourceTarget(source_uuid=VALID_SOURCE_UUID, version=VALID_VERSION),
            type=EventType.REPLY_SENT,
            data=None,
        )


def test_data_unexpected_type():
    """Data of unexpected type raises TypeError."""
    with pytest.raises(TypeError, match="invalid event data for type reply_sent"):
        Event(
            id="123456",
            target=SourceTarget(source_uuid=VALID_SOURCE_UUID, version=VALID_VERSION),
            type=EventType.REPLY_SENT,
            data="not a dict or EventData",  # type: ignore[arg-type]
        )


def test_valid_event_with_data_mapping():
    """Valid event with data as mapping is normalized to EventData."""
    event = Event(
        id="123456",
        target=SourceTarget(source_uuid=VALID_SOURCE_UUID, version=VALID_VERSION),
        type=EventType.REPLY_SENT,
        data={"uuid": VALID_REPLY_UUID, "reply": "test reply content"},
    )
    assert isinstance(event.data, ReplySentData)
    assert event.data.uuid == VALID_REPLY_UUID
    assert event.data.reply == "test reply content"


def test_valid_event_with_event_data_instance():
    """Valid event with EventData instance is accepted."""
    data = ReplySentData(uuid=VALID_REPLY_UUID, reply="test reply")
    event = Event(
        id="123456",
        target=SourceTarget(source_uuid=VALID_SOURCE_UUID, version=VALID_VERSION),
        type=EventType.REPLY_SENT,
        data=data,
    )
    assert event.data is data


def test_valid_event_without_data():
    """Valid event without data when none expected."""
    event = Event(
        id="123456",
        target=ItemTarget(item_uuid=VALID_ITEM_UUID, version=VALID_VERSION),
        type=EventType.ITEM_DELETED,
    )
    assert event.data is None


def test_target_normalized_from_mapping():
    """Target mapping is normalized to correct Target subclass."""
    event = Event(
        id="123456",
        target={"source_uuid": VALID_SOURCE_UUID, "version": VALID_VERSION},
        type=EventType.SOURCE_STARRED,
    )
    assert isinstance(event.target, SourceTarget)
    assert event.target.source_uuid == VALID_SOURCE_UUID
