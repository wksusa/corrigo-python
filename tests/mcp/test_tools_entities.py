"""Tests for entity CRUD and query tools."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError


class TestCreateCustomer:
    async def test_create_delegates_to_sdk(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.customers.create.return_value = {"Id": 10, "ConcurrencyId": 1}
        result = await mcp_client.call_tool(
            "create_customer",
            {"name": "Test Corp", "work_zone_id": 1},
        )
        data = json.loads(result.data)
        assert data["Id"] == 10
        mock_corrigo_client.customers.create.assert_called_once()


class TestUpdateCustomer:
    async def test_update_auto_fetches_concurrency_id(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.customers.get.return_value = {"Id": 10, "ConcurrencyId": 3}
        mock_corrigo_client.update.return_value = {"Id": 10, "ConcurrencyId": 4}

        result = await mcp_client.call_tool(
            "update_customer",
            {"customer_id": 10, "updates": {"DisplayAs": "New Name"}},
        )
        data = json.loads(result.data)
        assert data["ConcurrencyId"] == 4
        mock_corrigo_client.customers.get.assert_called_once_with(10)
        update_args = mock_corrigo_client.update.call_args.args
        assert update_args[2]["ConcurrencyId"] == 3


class TestCreateContact:
    async def test_create_delegates_to_sdk(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.contacts.create.return_value = {"Id": 20}
        result = await mcp_client.call_tool(
            "create_contact",
            {
                "customer_id": 1,
                "last_name": "Smith",
                "username": "jsmith",
                "email": "j@example.com",
            },
        )
        data = json.loads(result.data)
        assert data["Id"] == 20


class TestCreateEmployee:
    async def test_create_delegates_to_sdk(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.employees.create.return_value = {"Id": 30}
        result = await mcp_client.call_tool(
            "create_employee",
            {
                "first_name": "John",
                "last_name": "Doe",
                "username": "jdoe",
                "role_id": 5,
            },
        )
        data = json.loads(result.data)
        assert data["Id"] == 30


class TestCreateLocation:
    async def test_create_delegates_to_sdk(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.locations.create.return_value = {"Id": 40}
        result = await mcp_client.call_tool(
            "create_location",
            {"name": "Walk-in Cooler", "model_id": 1},
        )
        data = json.loads(result.data)
        assert data["Id"] == 40


class TestQueryEntities:
    async def test_basic_query(self, mcp_client: Client, mock_corrigo_client: MagicMock) -> None:
        mock_corrigo_client._http.post.return_value = {
            "Entities": [{"Data": {"Id": 1, "Name": "Test"}}]
        }
        result = await mcp_client.call_tool(
            "query_entities",
            {"entity_type": "Customer"},
        )
        data = json.loads(result.data)
        assert data["entity_type"] == "Customer"
        assert data["count"] == 1

    async def test_query_with_equality_filter(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client._http.post.return_value = {"Entities": []}
        result = await mcp_client.call_tool(
            "query_entities",
            {"entity_type": "WorkOrder", "filters": {"StatusId": "Open"}},
        )
        data = json.loads(result.data)
        assert data["count"] == 0

    async def test_query_with_like_filter(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client._http.post.return_value = {"Entities": []}
        await mcp_client.call_tool(
            "query_entities",
            {"entity_type": "Location", "filters": {"Name__like": "%cooler%"}},
        )
        # Verify the query was built with LIKE operator
        call_args = mock_corrigo_client._http.post.call_args
        query = call_args.kwargs.get("json") or call_args[1].get("json", {})
        conditions = query.get("QueryExpression", {}).get("Criteria", {}).get("Conditions", [])
        assert any(c.get("Operator") == "Like" for c in conditions)

    async def test_invalid_entity_type_raises_error(
        self,
        mcp_client: Client,
        mock_corrigo_client: MagicMock,  # noqa: ARG002
    ) -> None:
        with pytest.raises(ToolError, match="Unknown entity type"):
            await mcp_client.call_tool(
                "query_entities",
                {"entity_type": "FakeEntity"},
            )


class TestSearchLocations:
    async def test_search_returns_results(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.locations.search_by_name.return_value = [
            {"Id": 1, "Name": "Walk-in Cooler"},
        ]
        result = await mcp_client.call_tool("search_locations", {"name": "cooler"})
        data = json.loads(result.data)
        assert data["count"] == 1
        assert data["results"][0]["Name"] == "Walk-in Cooler"

    async def test_search_no_results_includes_suggestion(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.locations.search_by_name.return_value = []
        result = await mcp_client.call_tool("search_locations", {"name": "nonexistent"})
        data = json.loads(result.data)
        assert data["count"] == 0
        assert "suggestion" in data
