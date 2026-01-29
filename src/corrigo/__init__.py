"""
Corrigo SDK - Python client for the Corrigo Enterprise REST API.

A comprehensive SDK for interacting with the Corrigo facilities management
platform, supporting work orders, customers, locations, and more.
"""

from corrigo.client import CorrigoClient
from corrigo.auth import CorrigoAuth
from corrigo.events import EventRouter, EventPayload, EventType
from corrigo.exceptions import (
    CorrigoError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    ConcurrencyError,
    RateLimitError,
    ServerError,
)

__version__ = "0.1.0"
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
