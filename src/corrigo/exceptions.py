"""Custom exceptions for the Corrigo SDK."""

from typing import Any


class CorrigoError(Exception):
    """Base exception for all Corrigo SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(CorrigoError):
    """Raised when authentication fails (invalid credentials, expired token)."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when client credentials are invalid."""

    pass


class TokenExpiredError(AuthenticationError):
    """Raised when the OAuth token has expired."""

    pass


class AuthorizationError(CorrigoError):
    """Raised when the user lacks permission for an operation."""

    pass


class ValidationError(CorrigoError):
    """Raised when request data fails validation."""

    def __init__(
        self,
        message: str,
        errors: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.errors = errors or []


class RequiredFieldError(ValidationError):
    """Raised when a required field is missing."""

    def __init__(self, field_name: str, **kwargs: Any) -> None:
        super().__init__(f"Required field missing: {field_name}", **kwargs)
        self.field_name = field_name


class NotFoundError(CorrigoError):
    """Raised when a requested entity does not exist."""

    def __init__(
        self,
        entity_type: str | None = None,
        entity_id: int | str | None = None,
        **kwargs: Any,
    ) -> None:
        message = "Entity not found"
        if entity_type and entity_id:
            message = f"{entity_type} with ID {entity_id} not found"
        elif entity_type:
            message = f"{entity_type} not found"
        super().__init__(message, **kwargs)
        self.entity_type = entity_type
        self.entity_id = entity_id


class ConcurrencyError(CorrigoError):
    """Raised when an optimistic concurrency conflict occurs."""

    def __init__(
        self,
        entity_type: str | None = None,
        entity_id: int | str | None = None,
        **kwargs: Any,
    ) -> None:
        message = "Concurrency conflict: entity was modified by another process"
        if entity_type and entity_id:
            message = f"Concurrency conflict on {entity_type} {entity_id}"
        super().__init__(message, **kwargs)
        self.entity_type = entity_type
        self.entity_id = entity_id


class RateLimitError(CorrigoError):
    """Raised when API rate limits are exceeded."""

    def __init__(
        self,
        retry_after: int | None = None,
        **kwargs: Any,
    ) -> None:
        message = "Rate limit exceeded"
        if retry_after:
            message = f"Rate limit exceeded. Retry after {retry_after} seconds"
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(CorrigoError):
    """Raised when the Corrigo server returns a 5xx error."""

    pass


class NetworkError(CorrigoError):
    """Raised when a network-level error occurs."""

    pass
