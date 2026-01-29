"""Tests for the events module."""

import pytest

from corrigo.events import (
    EventType,
    EventPayload,
    EventRouter,
    WoNote,
    ActionLog,
    WorkOrderEvent,
    create_webhook_handler,
)


class TestEventType:
    """Tests for EventType enum."""

    def test_event_type_values(self):
        """Should have correct event type values."""
        assert EventType.WO_CREATED.value == "WoCreated"
        assert EventType.WO_COMPLETE.value == "WoComplete"
        assert EventType.WO_CANCEL.value == "WoCancel"
        assert EventType.NOTE_ADDED.value == "NoteAdded"


class TestEventPayload:
    """Tests for EventPayload model."""

    def test_parse_basic_payload(self):
        """Should parse a basic event payload."""
        data = {
            "EventType": "WoComplete",
            "WorkOrder": {
                "Id": 12345,
                "Number": "WO-001",
                "StatusId": "Completed",
            },
        }

        event = EventPayload.from_webhook(data)

        assert event.event_type == "WoComplete"
        assert event.work_order is not None
        assert event.work_order.id == 12345
        assert event.work_order.number == "WO-001"

    def test_parse_note_payload(self):
        """Should parse an event with note data."""
        data = {
            "EventType": "NoteAdded",
            "WoNote": {
                "Id": 999,
                "Body": "Test note content",
                "Creator": "jdoe",
                "Date": "2024-01-15T10:30:00Z",
                "Type": "Internal",
            },
        }

        event = EventPayload.from_webhook(data)

        assert event.event_type == "NoteAdded"
        assert event.wo_note is not None
        assert event.wo_note.id == 999
        assert event.wo_note.body == "Test note content"
        assert event.wo_note.creator == "jdoe"

    def test_parse_action_logs(self):
        """Should parse action logs in work order."""
        data = {
            "EventType": "WoComplete",
            "WorkOrder": {
                "Id": 12345,
                "ActionLogs": [
                    {
                        "Timestamp": "2024-01-15T10:00:00Z",
                        "Actor": "jtech",
                        "ActionType": "Complete",
                    },
                    {
                        "Timestamp": "2024-01-15T09:00:00Z",
                        "Actor": "jtech",
                        "ActionType": "Start",
                    },
                ],
            },
        }

        event = EventPayload.from_webhook(data)

        assert len(event.work_order.action_logs) == 2
        assert event.work_order.action_logs[0].actor == "jtech"
        assert event.work_order.action_logs[0].action_type == "Complete"

    def test_preserves_raw_data(self):
        """Should preserve the raw payload data."""
        data = {
            "EventType": "WoComplete",
            "CustomField": "custom_value",
            "NestedData": {"key": "value"},
        }

        event = EventPayload.from_webhook(data)

        assert event.raw_data["CustomField"] == "custom_value"
        assert event.raw_data["NestedData"]["key"] == "value"


class TestEventRouter:
    """Tests for EventRouter class."""

    def test_register_handler_with_decorator(self):
        """Should register handler using decorator."""
        router = EventRouter()
        called = []

        @router.on(EventType.WO_COMPLETE)
        def handle_complete(event: EventPayload):
            called.append(event.event_type)

        router.handle({"EventType": "WoComplete"})

        assert called == ["WoComplete"]

    def test_handler_receives_parsed_event(self):
        """Should pass parsed EventPayload to handler."""
        router = EventRouter()
        received_event = []

        @router.on(EventType.WO_COMPLETE)
        def handle_complete(event: EventPayload):
            received_event.append(event)

        router.handle({
            "EventType": "WoComplete",
            "WorkOrder": {"Id": 12345, "Number": "WO-001"},
        })

        assert len(received_event) == 1
        assert received_event[0].work_order.id == 12345

    def test_multiple_handlers_for_same_event(self):
        """Should call multiple handlers for same event type."""
        router = EventRouter()
        called = []

        @router.on(EventType.WO_COMPLETE)
        def handler1(event: EventPayload):
            called.append("handler1")

        @router.on(EventType.WO_COMPLETE)
        def handler2(event: EventPayload):
            called.append("handler2")

        router.handle({"EventType": "WoComplete"})

        assert "handler1" in called
        assert "handler2" in called

    def test_handlers_for_different_events(self):
        """Should only call handler for matching event type."""
        router = EventRouter()
        called = []

        @router.on(EventType.WO_COMPLETE)
        def handle_complete(event: EventPayload):
            called.append("complete")

        @router.on(EventType.WO_CANCEL)
        def handle_cancel(event: EventPayload):
            called.append("cancel")

        router.handle({"EventType": "WoComplete"})

        assert called == ["complete"]

    def test_catch_all_handler(self):
        """Should call handler registered for all events."""
        router = EventRouter()
        called = []

        @router.on()  # No specific event type = all events
        def handle_all(event: EventPayload):
            called.append(event.event_type)

        router.handle({"EventType": "WoComplete"})
        router.handle({"EventType": "WoCancel"})

        assert called == ["WoComplete", "WoCancel"]

    def test_default_handler(self):
        """Should call default handler for unhandled events."""
        router = EventRouter()
        default_called = []

        @router.on(EventType.WO_COMPLETE)
        def handle_complete(event: EventPayload):
            pass

        @router.on_default
        def handle_default(event: EventPayload):
            default_called.append(event.event_type)

        # This event type has no specific handler
        router.handle({"EventType": "WoCancel"})

        assert default_called == ["WoCancel"]

    def test_default_handler_not_called_when_handled(self):
        """Should not call default handler when event is handled."""
        router = EventRouter()
        default_called = []

        @router.on(EventType.WO_COMPLETE)
        def handle_complete(event: EventPayload):
            pass

        @router.on_default
        def handle_default(event: EventPayload):
            default_called.append(event.event_type)

        router.handle({"EventType": "WoComplete"})

        assert default_called == []

    def test_add_handler_programmatically(self):
        """Should register handler using add_handler method."""
        router = EventRouter()
        called = []

        def handler(event: EventPayload):
            called.append(event.event_type)

        router.add_handler(handler, EventType.WO_COMPLETE)
        router.handle({"EventType": "WoComplete"})

        assert called == ["WoComplete"]

    def test_string_event_type(self):
        """Should accept string event type."""
        router = EventRouter()
        called = []

        @router.on("WoComplete")
        def handle_complete(event: EventPayload):
            called.append(event.event_type)

        router.handle({"EventType": "WoComplete"})

        assert called == ["WoComplete"]


class TestCreateWebhookHandler:
    """Tests for create_webhook_handler function."""

    def test_creates_callable_handler(self):
        """Should create a callable handler function."""
        router = EventRouter()
        handler = create_webhook_handler(router)

        assert callable(handler)

    def test_handler_routes_to_router(self):
        """Should route events through the router."""
        router = EventRouter()
        called = []

        @router.on(EventType.WO_COMPLETE)
        def handle_complete(event: EventPayload):
            called.append(event.event_type)

        handler = create_webhook_handler(router)
        handler({"EventType": "WoComplete"})

        assert called == ["WoComplete"]


class TestWoNote:
    """Tests for WoNote model."""

    def test_parse_note(self):
        """Should parse note data."""
        note = WoNote(
            id=123,
            body="Test note",
            creator="jdoe",
            date="2024-01-15",
            note_type="Internal",
        )

        assert note.id == 123
        assert note.body == "Test note"


class TestActionLog:
    """Tests for ActionLog model."""

    def test_parse_action_log(self):
        """Should parse action log data."""
        log = ActionLog(
            timestamp="2024-01-15T10:00:00Z",
            actor="jtech",
            action_type="Complete",
        )

        assert log.actor == "jtech"
        assert log.action_type == "Complete"
