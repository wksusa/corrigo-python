"""Tests for MCP resource templates."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from fastmcp import Client

from corrigo.exceptions import NotFoundError


class TestWorkOrderResources:
    async def test_get_work_order_by_id(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.work_orders.get.return_value = {
            "Id": 42,
            "Number": "WO-001",
            "StatusId": "Open",
        }
        result = await mcp_client.read_resource("corrigo://work-orders/42")
        data = json.loads(result[0].text)
        assert data["Number"] == "WO-001"
        mock_corrigo_client.work_orders.get.assert_called_once_with(42)

    async def test_get_work_order_not_found(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.work_orders.get.side_effect = NotFoundError("WorkOrder", 999)
        with pytest.raises(Exception, match="not found"):
            await mcp_client.read_resource("corrigo://work-orders/999")

    async def test_get_work_order_by_number(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.work_orders.get_by_number.return_value = {
            "Id": 42,
            "Number": "WO-001",
        }
        result = await mcp_client.read_resource("corrigo://work-orders/number/WO-001")
        data = json.loads(result[0].text)
        assert data["Id"] == 42

    async def test_get_work_order_by_number_not_found(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.work_orders.get_by_number.return_value = None
        with pytest.raises(Exception, match="not found"):
            await mcp_client.read_resource("corrigo://work-orders/number/WO-999")


class TestCustomerResources:
    async def test_get_customer(self, mcp_client: Client, mock_corrigo_client: MagicMock) -> None:
        mock_corrigo_client.customers.get.return_value = {
            "Id": 5,
            "DisplayAs": "Test Corp",
        }
        result = await mcp_client.read_resource("corrigo://customers/5")
        data = json.loads(result[0].text)
        assert data["DisplayAs"] == "Test Corp"

    async def test_get_customer_assets(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.locations.list_by_customer.return_value = [
            {"Id": 10, "Name": "Walk-in Cooler"},
            {"Id": 11, "Name": "Grill"},
        ]
        result = await mcp_client.read_resource("corrigo://customers/5/assets")
        data = json.loads(result[0].text)
        assert len(data) == 2
        assert data[0]["Name"] == "Walk-in Cooler"


class TestLocationResources:
    async def test_get_location(self, mcp_client: Client, mock_corrigo_client: MagicMock) -> None:
        mock_corrigo_client.locations.get.return_value = {
            "Id": 10,
            "Name": "Walk-in Cooler",
            "TypeId": "Equipment",
        }
        result = await mcp_client.read_resource("corrigo://locations/10")
        data = json.loads(result[0].text)
        assert data["Name"] == "Walk-in Cooler"

    async def test_get_location_attributes(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.locations.get_with_attributes.return_value = {
            "Id": 10,
            "Name": "Walk-in Cooler",
            "attributes": {"Model #": "XYZ-100", "Serial #": "SN-999"},
        }
        result = await mcp_client.read_resource("corrigo://locations/10/attributes")
        data = json.loads(result[0].text)
        assert data["attributes"]["Model #"] == "XYZ-100"
        assert data["attributes"]["Serial #"] == "SN-999"


class TestInternalOnlyResources:
    async def test_get_employee(self, mcp_client: Client, mock_corrigo_client: MagicMock) -> None:
        mock_corrigo_client.employees.get.return_value = {
            "Id": 1,
            "FirstName": "John",
            "LastName": "Doe",
        }
        result = await mcp_client.read_resource("corrigo://employees/1")
        data = json.loads(result[0].text)
        assert data["FirstName"] == "John"

    async def test_get_invoice(self, mcp_client: Client, mock_corrigo_client: MagicMock) -> None:
        mock_corrigo_client.invoices.get.return_value = {
            "Id": 100,
            "Amount": 500.00,
        }
        result = await mcp_client.read_resource("corrigo://invoices/100")
        data = json.loads(result[0].text)
        assert data["Amount"] == 500.00
