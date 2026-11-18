from dataclasses import asdict

from db import db
from flask import current_app
from journalist_app import utils
from journalist_app.api2.shared import json_version, mark_source_deleted, save_reply
from journalist_app.api2.types import (
    Event,
    EventResult,
    EventStatusCode,
    EventType,
    ItemUUID,
)
from journalist_app.sessions import Session, session
from models import Reply, Source, Submission
from redis import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound, StaleDataError
from store import NotEncrypted

# `IDEMPOTENCE_PERIOD` MUST be greater than or equal to
# `sdconfig.SecureDropConfig.SESSION_LIFETIME`.  In practice, 24 hours is the
# easiest period to reason about.
IDEMPOTENCE_PERIOD = 60 * 60 * 24  # seconds * minutes * hours = 1 day

REDIS_EVENT_PREFIX = "sd/events"


class EventHandler:
    """
    This class is the per-request context for handling events.  To add a handler
    for a new event `thing_done`, you must:

    1. define the enum value `EventType.THING_DONE` in
       `journalist_api2.types.EventType`;

    2. define its expected target and data types in
       `journalist_api2.types.EVENT_DATA_TYPES`;

    3. define the handler as a static method `handle_thing_done(event: Event)`
       in this class; and

    4. explicitly register `{"thing_done": self.handle_thing_done}` inside
      `EventHandler.process()`.

    This is belt-and-suspenders for ensuring that only the intended methods are
    exposed as callable event handlers.

    To preserve transaction separation between events, handlers MUST return with
    a clean SQLAlchemy session: in other words, having either successfully
    committed or rolled back all of their changes.
    """

    def __init__(self, session: Session, redis: Redis) -> None:
        """
        Configure the `EventHandler`.  Attributes set here are for internal use
        by the `EventHandler`; handler methods are static and do not have access
        to them, which means they cannot influence the processing of a given
        event.
        """

        self._session = session
        self._redis = redis

    def process(self, event: Event, minor: int) -> EventResult:
        """The per-event entry-point for handling a single event."""

        try:
            if self.is_duplicate(event):
                return EventResult(
                    event_id=event.id,
                    status=(EventStatusCode.AlreadyReported, None),
                )

            handler = {
                EventType.ITEM_DELETED: self.handle_item_deleted,
                EventType.REPLY_SENT: self.handle_reply_sent,
                EventType.SOURCE_DELETED: self.handle_source_deleted,
                EventType.SOURCE_STARRED: self.handle_source_starred,
                EventType.SOURCE_UNSTARRED: self.handle_source_unstarred,
                EventType.SOURCE_CONVERSATION_TRUNCATED: self.handle_source_conversation_truncated,
                EventType.SOURCE_CONVERSATION_SEEN: self.handle_source_conversation_seen,
            }[event.type]
        except KeyError:
            self.record_status(event, EventStatusCode.NotImplemented)
            return EventResult(
                event_id=event.id,
                status=(
                    EventStatusCode.NotImplemented,
                    f"no handler for event type: {event.type}",
                ),
            )

        try:
            result = handler(event, minor)

            # Enforce "handlers MUST return with a clean SQLAlchemy session" above:
            if db.session.dirty or db.session.new or db.session.deleted:
                raise RuntimeError(f"{handler} returned with a pending database transaction")

        # Catch anything not handled by the handler:
        except Exception:
            current_app.logger.error(f"unhandled exception in handler for {event}", exc_info=True)
            db.session.rollback()
            result = EventResult(
                event.id, (EventStatusCode.InternalServerError, "failed to process event")
            )

        self.record_status(event, result.status[0])
        return result

    def idempotence_key(self, event: Event) -> str:
        return f"{REDIS_EVENT_PREFIX}/{self._session.user.uuid}/{event.id}"

    def is_duplicate(self, event: Event) -> bool:
        """Returns `True` if this event is already registered (i.e., a replay)."""
        return (
            self._redis.set(
                self.idempotence_key(event),
                EventStatusCode.Processing,
                ex=IDEMPOTENCE_PERIOD,
                nx=True,
            )
            is None
        )

    def record_status(self, event: Event, status: EventStatusCode) -> None:
        """Record the event's final status for idempotence, or clear on error to permit retry."""
        if status >= EventStatusCode.BadRequest:
            self._redis.delete(self.idempotence_key(event))
        else:
            self._redis.set(self.idempotence_key(event), status, ex=IDEMPOTENCE_PERIOD)

    @staticmethod
    def handle_item_deleted(event: Event, minor: int) -> EventResult:
        item = find_item(event.target.item_uuid)
        if item is None:
            return EventResult(
                event_id=event.id,
                status=(EventStatusCode.Gone, None),
            )

        try:
            utils.delete_file_object(item)
        except (StaleDataError, ValueError):
            # `utils.delete_file_object()` is non-atomic: it guarantees database
            # deletion but not filesystem deletion.  The former is all we need
            # for consistency with the client, and the latter will be caught by
            # monitoring for "disconnected" submissions.
            pass

        return EventResult(
            event_id=event.id,
            status=(EventStatusCode.OK, None),
            items={event.target.item_uuid: None},
        )

    @staticmethod
    def handle_reply_sent(event: Event, minor: int) -> EventResult:
        try:
            source = Source.query.filter(Source.uuid == event.target.source_uuid).one()
        except NoResultFound:
            return EventResult(
                event_id=event.id,
                status=(
                    EventStatusCode.NotFound,
                    f"could not find source: {event.target.source_uuid}",
                ),
            )

        # SQLite will enforce uniqueness within Reply.uuid, but we need
        # uniqueness within the combined set of Reply.uuid and Submission.uuid.
        if find_item(event.data.uuid) is not None:
            return EventResult(
                event_id=event.id,
                status=(EventStatusCode.Conflict, "duplicate UUID"),
            )

        try:
            reply = save_reply(source, asdict(event.data))
            db.session.refresh(source)

            return EventResult(
                event_id=event.id,
                status=(EventStatusCode.OK, None),
                sources={source.uuid: source},
                items={reply.uuid: reply},
            )
        except NotEncrypted:
            db.session.rollback()
            status = (EventStatusCode.BadRequest, "reply is not encrypted")
        except IntegrityError:
            db.session.rollback()
            status = (EventStatusCode.Conflict, "duplicate UUID")
        # `save_reply()` can also raise `InvalidUUID`, but this will have been
        # caught by validation of the `ReplySentData` type before this handler
        # is ever invoked.

        return EventResult(
            event_id=event.id,
            status=status,
        )

    @staticmethod
    def handle_source_deleted(event: Event, minor: int) -> EventResult:
        try:
            source = Source.query.filter(Source.uuid == event.target.source_uuid).one()
        except NoResultFound:
            return EventResult(
                event_id=event.id,
                status=(
                    EventStatusCode.Gone,
                    None,
                ),
            )

        current_version = json_version(source.to_api_v2(minor))
        if event.target.version != current_version:
            return EventResult(
                event_id=event.id,
                status=(
                    EventStatusCode.Conflict,
                    f"outdated source: expected {current_version}, got {event.target.version}",
                ),
            )

        # Deletion via `mark_source_deleted()` is asynchronous, but if it's
        # initiated successfully we should report back to the client that
        # all of the deleted source's items have also been deleted.
        deleted_items = {item.uuid: None for item in source.collection}
        mark_source_deleted([source.filesystem_id])
        return EventResult(
            event_id=event.id,
            status=(EventStatusCode.OK, None),
            sources={event.target.source_uuid: None},
            items=deleted_items,
        )

    @staticmethod
    def handle_source_conversation_truncated(event: Event, minor: int) -> EventResult:
        """
        A `source_conversation_truncated` event involves deleting all the items
        in the source's collection with interaction counts less than or equal to
        the specified upper bound, assumed to be the last item known to the
        client.
        """

        try:
            source = Source.query.filter(Source.uuid == event.target.source_uuid).one()
        except NoResultFound:
            return EventResult(
                event_id=event.id,
                status=(
                    EventStatusCode.Gone,
                    None,
                ),
            )

        deleted: list[ItemUUID] = []
        for item in source.collection:
            if item.interaction_count <= event.data.upper_bound:
                try:
                    utils.delete_file_object(item)
                except (StaleDataError, ValueError):
                    # `utils.delete_file_object()` is non-atomic: it guarantees
                    # database deletion but not filesystem deletion.  The former
                    # is all we need for consistency with the client, and the
                    # latter will be caught by monitoring for "disconnected"
                    # submissions.
                    pass

                deleted.append(item.uuid)

        db.session.refresh(source)
        return EventResult(
            event_id=event.id,
            status=(EventStatusCode.OK, None),
            sources={source.uuid: source},
            items={item_uuid: None for item_uuid in deleted},
        )

    @staticmethod
    def handle_source_conversation_seen(event: Event, minor: int) -> EventResult:
        """
        A `source_conversation_seen` event involves marking as seen items
        in the source's collection with interaction counts less than or equal to
        the specified upper bound.
        """

        try:
            source = Source.query.filter(Source.uuid == event.target.source_uuid).one()
        except NoResultFound:
            return EventResult(
                event_id=event.id,
                status=(
                    EventStatusCode.Gone,
                    None,
                ),
            )

        user = session.get_user()
        seen_items = [
            item for item in source.collection if item.interaction_count <= event.data.upper_bound
        ]

        if seen_items:
            utils.mark_seen(seen_items, user)
            for item in seen_items:
                db.session.refresh(item)
            db.session.refresh(source)
        return EventResult(
            event_id=event.id,
            status=(EventStatusCode.OK, None),
            sources={source.uuid: source},
            items={item.uuid: item for item in seen_items},
        )

    @staticmethod
    def handle_source_starred(event: Event, minor: int) -> EventResult:
        try:
            source = Source.query.filter(Source.uuid == event.target.source_uuid).one()
        except NoResultFound:
            return EventResult(
                event_id=event.id,
                status=(
                    EventStatusCode.NotFound,
                    f"could not find source: {event.target.source_uuid}",
                ),
            )

        utils.make_star_true(source.filesystem_id)
        db.session.commit()
        db.session.refresh(source)

        return EventResult(
            event_id=event.id,
            status=(EventStatusCode.OK, None),
            sources={source.uuid: source},
        )

    @staticmethod
    def handle_source_unstarred(event: Event, minor: int) -> EventResult:
        try:
            source = Source.query.filter(Source.uuid == event.target.source_uuid).one()
        except NoResultFound:
            return EventResult(
                event_id=event.id,
                status=(
                    EventStatusCode.NotFound,
                    f"could not find source: {event.target.source_uuid}",
                ),
            )

        utils.make_star_false(source.filesystem_id)
        db.session.commit()
        db.session.refresh(source)

        return EventResult(
            event_id=event.id,
            status=(EventStatusCode.OK, None),
            sources={source.uuid: source},
        )


def find_item(item_uuid: ItemUUID) -> Submission | Reply | None:
    submission = Submission.query.filter(Submission.uuid == item_uuid).one_or_none()
    reply = Reply.query.filter(Reply.uuid == item_uuid).one_or_none()

    if submission and reply:
        # Fail if we get unlucky and hit a UUID collision between the
        # `Submission` and `Reply` tables.  This is vanishingly unlikely,
        # but SQLite can't enforce uniqueness between them.
        raise MultipleResultsFound(f"found {item_uuid} in both submissions and replies")

    return submission or reply
