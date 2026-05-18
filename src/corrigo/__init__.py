"""
Corrigo SDK - Python client for the Corrigo Enterprise REST API.

A comprehensive SDK for interacting with the Corrigo facilities management
platform, supporting work orders, customers, locations, and more.
"""

from corrigo.auth import CorrigoAuth
from corrigo.client import CorrigoClient
from corrigo.events import EventPayload, EventRouter, EventType
from corrigo.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConcurrencyError,
    CorrigoError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

__version__ = "0.6.0"
__all__ = [
    "CorrigoClient",
    "CorrigoAuth",
    "EventRouter",
    "EventPayload",
    "EventType",
    "CorrigoError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "ConcurrencyError",
    "RateLimitError",
    "ServerError",
]
