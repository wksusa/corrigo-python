"""Shared fixtures for MCP server tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client


@pytest.fixture
def mock_corrigo_client() -> MagicMock:
    """Create a mock CorrigoClient with all resource properties."""
    client = MagicMock()
    client._company_name = "TestCompany"
    client._region = "AM"

    # Resource managers
    client.work_orders = MagicMock()
    client.customers = MagicMock()
    client.contacts = MagicMock()
    client.employees = MagicMock()
    client.locations = MagicMock()
    client.invoices = MagicMock()

    # Low-level methods
    client.get = MagicMock(return_value={})
    client.create = MagicMock(return_value={"Id": 1, "ConcurrencyId": 1})
    client.update = MagicMock(return_value={"Id": 1, "ConcurrencyId": 2})
    client.query = MagicMock(return_value={"Entities": []})

    # Make _http.post return empty entities (for lifespan descriptor cache query)
    client._http = MagicMock()
    client._http.post.return_value = {"Entities": []}

    return client


@pytest.fixture
async def mcp_client(
    monkeypatch: pytest.MonkeyPatch,
    mock_corrigo_client: MagicMock,
) -> Any:
    """Create an MCP Client connected to the production server with mocked SDK.

    This uses the real production server (with all tools/resources/prompts registered)
    but mocks the CorrigoClient so no real API calls are made.
    """
    monkeypatch.setenv("CORRIGO_CLIENT_ID", "test_id")
    monkeypatch.setenv("CORRIGO_CLIENT_SECRET", "test_secret")
    monkeypatch.setenv("CORRIGO_COMPANY_NAME", "TestCompany")
    monkeypatch.setenv("CORRIGO_REGION", "AM")

    # Import here to ensure tool/resource/prompt modules are loaded (side-effect registration)
    import corrigo.mcp.prompts  # noqa: F401
    import corrigo.mcp.resources  # noqa: F401
    import corrigo.mcp.tools  # noqa: F401
    from corrigo.mcp.server import mcp

    with patch("corrigo.mcp.server.CorrigoClient", return_value=mock_corrigo_client):
        async with Client(mcp) as client:
            yield client
