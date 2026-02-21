"""Tests for work order lifecycle and listing tools."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastmcp import Client

from corrigo.exceptions import NotFoundError


class TestCreateWorkOrder:
    async def test_create_delegates_to_sdk(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.work_orders.create.return_value = {
            "Id": 42,
            "ConcurrencyId": 1,
        }
        result = await mcp_client.call_tool(
            "create_work_order",
            {
                "customer_id": 1,
                "asset_id": 10,
                "task_id": 100,
                "subtype_id": 5,
            },
        )
        data = json.loads(result.data)
        assert data["Id"] == 42
        mock_corrigo_client.work_orders.create.assert_called_once_with(
            customer_id=1,
            asset_id=10,
            task_id=100,
            subtype_id=5,
            priority_id=None,
            contact_address=None,
            compute_assignment=False,
            compute_schedule=False,
        )

    async def test_create_with_optional_params(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.work_orders.create.return_value = {"Id": 43}
        result = await mcp_client.call_tool(
            "create_work_order",
            {
                "customer_id": 1,
                "asset_id": 10,
                "task_id": 100,
                "subtype_id": 5,
                "priority_id": 3,
                "contact_address": "test@example.com",
                "compute_assignment": True,
            },
        )
        data = json.loads(result.data)
        assert data["Id"] == 43
        mock_corrigo_client.work_orders.create.assert_called_once()
        call_kwargs = mock_corrigo_client.work_orders.create.call_args.kwargs
        assert call_kwargs["priority_id"] == 3
        assert call_kwargs["contact_address"] == "test@example.com"
        assert call_kwargs["compute_assignment"] is True


class TestUpdateWorkOrder:
    async def test_update_auto_fetches_concurrency_id(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.work_orders.get.return_value = {
            "Id": 42,
            "ConcurrencyId": 7,
        }
        mock_corrigo_client.update.return_value = {"Id": 42, "ConcurrencyId": 8}

        result = await mcp_client.call_tool(
            "update_work_order",
            {"work_order_id": 42, "updates": {"Priority": {"Id": 5}}},
        )
        data = json.loads(result.data)
        assert data["ConcurrencyId"] == 8

        # Verify it fetched current state first
        mock_corrigo_client.work_orders.get.assert_called_once_with(42)
        # Verify ConcurrencyId was included in the update
        update_call = mock_corrigo_client.update.call_args
        assert update_call.args[2]["ConcurrencyId"] == 7


class TestLifecycleTools:
    @pytest.mark.parametrize(
        "tool_name,sdk_method,extra_args",
        [
            ("assign_work_order", "assign", {"employee_id": 5}),
            ("pickup_work_order", "pickup", {}),
            ("start_work_order", "start", {}),
            ("complete_work_order", "complete", {}),
            ("cancel_work_order", "cancel", {}),
            ("hold_work_order", "hold", {}),
            ("pause_work_order", "pause", {}),
            ("reopen_work_order", "reopen", {}),
        ],
    )
    async def test_lifecycle_tool_delegates_to_sdk(
        self,
        mcp_client: Client,
        mock_corrigo_client: MagicMock,
        tool_name: str,
        sdk_method: str,
        extra_args: dict[str, Any],
    ) -> None:
        getattr(mock_corrigo_client.work_orders, sdk_method).return_value = {
            "CommandResult": "Success"
        }
        args = {"work_order_id": 42, **extra_args}
        result = await mcp_client.call_tool(tool_name, args)
        data = json.loads(result.data)
        assert data["CommandResult"] == "Success"
        getattr(mock_corrigo_client.work_orders, sdk_method).assert_called_once()

    async def test_lifecycle_tool_handles_sdk_error(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        from fastmcp.exceptions import ToolError

        mock_corrigo_client.work_orders.assign.side_effect = NotFoundError("WorkOrder", 999)
        with pytest.raises(ToolError, match="not found"):
            await mcp_client.call_tool("assign_work_order", {"work_order_id": 999})


class TestListWorkOrders:
    async def test_list_returns_envelope(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client._http.post.return_value = {
            "Entities": [
                {"Data": {"Id": 1, "Number": "WO-001"}},
                {"Data": {"Id": 2, "Number": "WO-002"}},
            ]
        }
        result = await mcp_client.call_tool("list_work_orders", {})
        data = json.loads(result.data)
        assert data["count"] == 2
        assert len(data["results"]) == 2
        assert data["has_more"] is False

    async def test_list_has_more_when_at_limit(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        # Return exactly `limit` results to signal there may be more
        entities = [{"Data": {"Id": i}} for i in range(100)]
        mock_corrigo_client._http.post.return_value = {"Entities": entities}
        result = await mcp_client.call_tool("list_work_orders", {"limit": 100})
        data = json.loads(result.data)
        assert data["has_more"] is True
        assert data["count"] == 100

    async def test_list_by_customer(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client._http.post.return_value = {
            "Entities": [{"Data": {"Id": 1, "Customer": {"Id": 5}}}]
        }
        result = await mcp_client.call_tool("list_work_orders_by_customer", {"customer_id": 5})
        data = json.loads(result.data)
        assert data["count"] == 1

    async def test_list_by_assignee(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client._http.post.return_value = {"Entities": []}
        result = await mcp_client.call_tool("list_work_orders_by_assignee", {"employee_id": 10})
        data = json.loads(result.data)
        assert data["count"] == 0
        assert data["has_more"] is False


class TestListByBrand:
    async def test_brand_resolves_customers_then_queries(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        # First call: customer list
        mock_corrigo_client.customers.list.return_value = [
            {"Id": 1, "DisplayAs": "WEN - Store 1"},
            {"Id": 2, "DisplayAs": "WEN - Store 2"},
        ]
        # Second call: WO query
        mock_corrigo_client._http.post.return_value = {"Entities": [{"Data": {"Id": 100}}]}
        result = await mcp_client.call_tool("list_work_orders_by_brand", {"brand_prefix": "WEN"})
        data = json.loads(result.data)
        assert data["count"] == 1
        mock_corrigo_client.customers.list.assert_called_once()

    async def test_brand_no_customers_raises_error(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        from fastmcp.exceptions import ToolError

        mock_corrigo_client.customers.list.return_value = []
        with pytest.raises(ToolError, match="No customers found"):
            await mcp_client.call_tool("list_work_orders_by_brand", {"brand_prefix": "NONEXISTENT"})
