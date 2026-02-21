"""Tests for MCP server foundation: lifespan, error handling, ping tool."""

from __future__ import annotations

import json

from fastmcp import Client
from fastmcp.exceptions import ToolError

from corrigo.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConcurrencyError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    RequiredFieldError,
    ServerError,
    ValidationError,
)
from corrigo.mcp.server import handle_sdk_error

# --- Error handler tests ---


class TestErrorHandler:
    def test_not_found_with_details(self) -> None:
        err = handle_sdk_error(NotFoundError("WorkOrder", 42))
        assert "WorkOrder 42 not found" in str(err)

    def test_not_found_generic(self) -> None:
        err = handle_sdk_error(NotFoundError())
        assert "not found" in str(err)

    def test_required_field(self) -> None:
        err = handle_sdk_error(RequiredFieldError("customer_id"))
        assert "customer_id" in str(err)

    def test_validation_error_with_details(self) -> None:
        err = handle_sdk_error(ValidationError("bad input", errors=[{"field": "name"}]))
        assert "Validation error" in str(err)

    def test_concurrency_error(self) -> None:
        err = handle_sdk_error(ConcurrencyError("WorkOrder", 1))
        assert "modified" in str(err)

    def test_authentication_error(self) -> None:
        err = handle_sdk_error(AuthenticationError("bad creds"))
        assert "Authentication failed" in str(err)

    def test_authorization_error(self) -> None:
        err = handle_sdk_error(AuthorizationError("forbidden"))
        assert "Permission denied" in str(err)

    def test_rate_limit_with_retry(self) -> None:
        err = handle_sdk_error(RateLimitError(retry_after=30))
        assert "30 seconds" in str(err)

    def test_rate_limit_without_retry(self) -> None:
        err = handle_sdk_error(RateLimitError())
        assert "Rate limited" in str(err)

    def test_server_error(self) -> None:
        err = handle_sdk_error(ServerError("oops"))
        assert "server error" in str(err)

    def test_network_error(self) -> None:
        err = handle_sdk_error(NetworkError("timeout"))
        assert "Network error" in str(err)

    def test_all_return_tool_error(self) -> None:
        exceptions = [
            NotFoundError("WO", 1),
            RequiredFieldError("f"),
            ValidationError("v"),
            ConcurrencyError(),
            AuthenticationError("a"),
            AuthorizationError("a"),
            RateLimitError(),
            ServerError("s"),
            NetworkError("n"),
        ]
        for exc in exceptions:
            result = handle_sdk_error(exc)
            assert isinstance(result, ToolError)


# --- Ping tool tests ---


class TestPingTool:
    async def test_ping_returns_ok(self, mcp_client: Client) -> None:
        result = await mcp_client.call_tool("ping", {})
        data = json.loads(result.data)
        assert data["status"] == "ok"
        assert data["company"] == "TestCompany"


# --- Lifespan tests ---


class TestLifespan:
    async def test_lifespan_provides_client_in_context(self, mcp_client: Client) -> None:
        """Ping tool accesses lifespan_context['client'] — if it works, context is set."""
        result = await mcp_client.call_tool("ping", {})
        data = json.loads(result.data)
        assert data["status"] == "ok"
