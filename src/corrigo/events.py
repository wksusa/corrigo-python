"""Event service integration for Corrigo webhooks.

The Corrigo Event Service sends real-time notifications when work order
events occur. This module provides utilities for handling these events.

Note: The Event Service is a premium feature that requires special licensing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """Types of events sent by the Corrigo Event Service."""

    # Work Order Status Changes
    WO_CREATED = "WoCreated"
    WO_PICKUP = "WoPickUp"
    WO_START = "WoStart"
    WO_ON_HOLD = "WoOnHold"
    WO_COMPLETE = "WoComplete"
    WO_CANCEL = "WoCancel"
    WO_REOPEN = "WoReopen"
    WO_STOP = "WoStop"

    # Work Order Updates
    WO_FLAG_CHANGE = "WoFlagChange"
    WO_ASSIGNMENT = "WoAssignment"
    WO_VERIFICATION = "WoVerification"
    WO_SCHEDULE = "WoSchedule"

    # Financial Status
    VENDOR_INVOICE_STATUS = "VendorInvoiceStatus"
    INTERNAL_COST_STATUS = "InternalCostStatus"

    # Quotes
    QUOTE_REQUESTED = "QuoteRequested"
    QUOTE_SUBMITTED = "QuoteSubmitted"
    QUOTE_APPROVED = "QuoteApproved"
    QUOTE_REJECTED = "QuoteRejected"

    # Notes
    NOTE_ADDED = "NoteAdded"
    NOTE_MODIFIED = "NoteModified"

    # Estimates
    ESTIMATE_APPROVED = "EstimateApproved"
    ESTIMATE_REJECTED = "EstimateRejected"

    # Owner
    OWNER_CHANGED = "OwnerChanged"

    # Documents
    DOCUMENT_ATTACHED = "DocumentAttached"


class WoNote(BaseModel):
    """Work order note from an event payload."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(alias="Id")
    body: str | None = Field(default=None, alias="Body")
    creator: str | None = Field(default=None, alias="Creator")
    date: str | None = Field(default=None, alias="Date")
    note_type: str | None = Field(default=None, alias="Type")


class ActionLog(BaseModel):
    """Action log entry from an event payload."""

    model_config = ConfigDict(populate_by_name=True)

    timestamp: str | None = Field(default=None, alias="Timestamp")
    actor: str | None = Field(default=None, alias="Actor")
    action_type: str | None = Field(default=None, alias="ActionType")


class WorkOrderEvent(BaseModel):
    """Work order data from an event payload."""

    model_config = ConfigDict(populate_by_name=True)

    id: int | None = Field(default=None, alias="Id")
    number: str | None = Field(default=None, alias="Number")
    status_id: str | None = Field(default=None, alias="StatusId")
    action_logs: list[ActionLog] = Field(default_factory=list, alias="ActionLogs")


class EventPayload(BaseModel):
    """
    Parsed event payload from the Corrigo Event Service.

    The exact structure depends on the event type, but common fields
    are provided as typed attributes.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    event_type: str | None = Field(default=None, alias="EventType")
    work_order: WorkOrderEvent | None = Field(default=None, alias="WorkOrder")
    wo_note: WoNote | None = Field(default=None, alias="WoNote")
    raw_data: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_webhook(cls, data: dict[str, Any]) -> EventPayload:
        """
        Parse a webhook payload into an EventPayload.

        Args:
            data: The raw webhook JSON data.

        Returns:
            Parsed EventPayload with typed fields.
        """
        return cls(raw_data=data, **data)


# Type alias for event handlers
EventHandler = Callable[[EventPayload], None]


@dataclass
class EventHandlerRegistration:
    """Registration for an event handler."""

    event_type: EventType | str | None
    handler: EventHandler


class EventRouter:
    """
    Routes incoming webhook events to registered handlers.

    Provides a simple way to handle different event types with
    dedicated handler functions.

    Example:
        >>> router = EventRouter()
        >>>
        >>> @router.on(EventType.WO_COMPLETE)
        ... def handle_completion(event: EventPayload):
        ...     print(f"Work order {event.work_order.number} completed")
        >>>
        >>> # In your webhook endpoint:
        >>> router.handle(webhook_data)
    """

    def __init__(self) -> None:
        """Initialize the event router."""
        self._handlers: list[EventHandlerRegistration] = []
        self._default_handler: EventHandler | None = None

    def on(
        self,
        event_type: EventType | str | None = None,
    ) -> Callable[[EventHandler], EventHandler]:
        """
        Decorator to register a handler for an event type.

        Args:
            event_type: The event type to handle, or None for all events.

        Returns:
            Decorator function.

        Example:
            >>> @router.on(EventType.WO_COMPLETE)
            ... def handle_complete(event):
            ...     print("Completed!")
        """

        def decorator(func: EventHandler) -> EventHandler:
            self._handlers.append(
                EventHandlerRegistration(event_type=event_type, handler=func)
            )
            return func

        return decorator

    def on_default(self, func: EventHandler) -> EventHandler:
        """
        Decorator to register a default handler for unhandled events.

        Args:
            func: The handler function.

        Returns:
            The handler function.
        """
        self._default_handler = func
        return func

    def add_handler(
        self,
        handler: EventHandler,
        event_type: EventType | str | None = None,
    ) -> None:
        """
        Register a handler programmatically.

        Args:
            handler: The handler function.
            event_type: The event type to handle, or None for all events.
        """
        self._handlers.append(
            EventHandlerRegistration(event_type=event_type, handler=handler)
        )

    def handle(self, data: dict[str, Any]) -> None:
        """
        Route an event to registered handlers.

        Args:
            data: The raw webhook payload.
        """
        event = EventPayload.from_webhook(data)
        event_type = event.event_type

        handled = False
        for registration in self._handlers:
            # Check if handler matches this event type
            if registration.event_type is None:
                # Handler for all events
                registration.handler(event)
                handled = True
            elif isinstance(registration.event_type, EventType):
                if registration.event_type.value == event_type:
                    registration.handler(event)
                    handled = True
            elif registration.event_type == event_type:
                registration.handler(event)
                handled = True

        # Call default handler if no specific handler matched
        if not handled and self._default_handler:
            self._default_handler(event)


def create_webhook_handler(router: EventRouter) -> Callable[[dict[str, Any]], None]:
    """
    Create a webhook handler function for use with web frameworks.

    Args:
        router: The EventRouter to use for routing events.

    Returns:
        A function that handles webhook payloads.

    Example with Flask:
        >>> from flask import Flask, request
        >>> app = Flask(__name__)
        >>> router = EventRouter()
        >>> handler = create_webhook_handler(router)
        >>>
        >>> @app.route('/webhook', methods=['POST'])
        >>> def webhook():
        ...     handler(request.json)
        ...     return 'OK'
    """

    def handler(data: dict[str, Any]) -> None:
        router.handle(data)

    return handler
