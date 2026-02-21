"""Tests for MCP prompt templates."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastmcp import Client

from corrigo.exceptions import NetworkError


class TestTriageWorkOrder:
    async def test_returns_structured_message(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.work_orders.get.return_value = {
            "Id": 42,
            "Number": "WO-001",
            "StatusId": "Open",
            "Customer": {"Id": 5},
        }
        mock_corrigo_client.customers.get.return_value = {
            "Id": 5,
            "DisplayAs": "Test Corp",
        }
        result = await mcp_client.get_prompt("triage_work_order", arguments={"work_order_id": 42})
        assert len(result.messages) == 1
        content = result.messages[0].content.text
        assert "WO-001" in content
        assert "Test Corp" in content

    async def test_partial_failure_still_works(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.work_orders.get.return_value = {
            "Id": 42,
            "Customer": {"Id": 5},
        }
        mock_corrigo_client.customers.get.side_effect = NetworkError("timeout")
        result = await mcp_client.get_prompt("triage_work_order", arguments={"work_order_id": 42})
        content = result.messages[0].content.text
        assert "Could not load customer" in content


class TestDiagnoseWorkOrder:
    async def test_includes_equipment_attributes(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.work_orders.get.return_value = {
            "Id": 42,
            "Items": [{"Asset": {"Id": 10}}],
            "Customer": {"Id": 5},
        }
        mock_corrigo_client.locations.get_with_attributes.return_value = {
            "Name": "Walk-in Cooler",
            "attributes": {"Model #": "XYZ-100"},
        }
        mock_corrigo_client.customers.get.return_value = {"Id": 5, "DisplayAs": "Corp"}

        result = await mcp_client.get_prompt("diagnose_work_order", arguments={"work_order_id": 42})
        content = result.messages[0].content.text
        assert "Walk-in Cooler" in content
        assert "XYZ-100" in content


class TestCustomerOverview:
    async def test_includes_customer_and_assets(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.customers.get.return_value = {
            "Id": 5,
            "DisplayAs": "Test Corp",
        }
        mock_corrigo_client.locations.list_by_customer.return_value = [
            {"Id": 10, "Name": "Cooler"},
        ]
        mock_corrigo_client.work_orders.list_by_customer.return_value = [
            {"Id": 1, "Number": "WO-001"},
        ]
        result = await mcp_client.get_prompt("customer_overview", arguments={"customer_id": 5})
        content = result.messages[0].content.text
        assert "Test Corp" in content
        assert "Cooler" in content


class TestWorkOrderStatus:
    async def test_returns_only_safe_fields(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.work_orders.get.return_value = {
            "Id": 42,
            "Number": "WO-001",
            "StatusId": "InProgress",
            "DtCreated": "2024-01-01",
            "InternalNotes": "SECRET NOTES",
            "TotalCost": 5000.00,
        }
        result = await mcp_client.get_prompt("work_order_status", arguments={"work_order_id": 42})
        content = result.messages[0].content.text
        assert "WO-001" in content
        assert "InProgress" in content
        # Should NOT include internal or cost data
        assert "SECRET NOTES" not in content
        assert "5000" not in content


class TestReportIssue:
    async def test_includes_customer_and_equipment(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.customers.get.return_value = {
            "Id": 5,
            "DisplayAs": "Store 1234",
        }
        mock_corrigo_client.locations.list_by_customer.return_value = [
            {"Id": 10, "Name": "Walk-in Cooler", "TypeId": "Equipment"},
            {"Id": 11, "Name": "Main Building", "TypeId": "Building"},
        ]
        result = await mcp_client.get_prompt(
            "report_issue",
            arguments={
                "customer_id": 5,
                "description": "Cooler not working",
            },
        )
        content = result.messages[0].content.text
        assert "Store 1234" in content
        assert "Walk-in Cooler" in content
        assert "create_work_order" in content

    async def test_suggests_create_wo_params(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        mock_corrigo_client.customers.get.return_value = {"Id": 5, "DisplayAs": "X"}
        mock_corrigo_client.locations.list_by_customer.return_value = []
        result = await mcp_client.get_prompt(
            "report_issue",
            arguments={"customer_id": 5, "description": "Issue"},
        )
        content = result.messages[0].content.text
        assert "customer_id: 5" in content


class TestTroubleshootEquipment:
    async def test_full_context(self, mcp_client: Client, mock_corrigo_client: MagicMock) -> None:
        mock_corrigo_client.locations.get_with_attributes.return_value = {
            "Name": "Walk-in Cooler",
            "TypeId": "Equipment",
            "ParentName": "Store 1234",
            "attributes": {"Model #": "XYZ-100", "Serial #": "SN-999"},
        }
        result = await mcp_client.get_prompt(
            "troubleshoot_equipment", arguments={"equipment_id": 42}
        )
        content = result.messages[0].content.text
        assert "Walk-in Cooler" in content
        assert "XYZ-100" in content
        assert "troubleshooting steps" in content

    async def test_graceful_degradation_no_attributes(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        """Attributes fail but prompt still works with basic equipment data."""
        mock_corrigo_client.locations.get_with_attributes.side_effect = NetworkError("timeout")
        mock_corrigo_client.locations.get.return_value = {
            "Name": "Walk-in Cooler",
            "TypeId": "Equipment",
        }
        result = await mcp_client.get_prompt(
            "troubleshoot_equipment", arguments={"equipment_id": 42}
        )
        content = result.messages[0].content.text
        assert "Walk-in Cooler" in content
        assert "Could not load" in content

    async def test_graceful_degradation_equipment_not_found(
        self, mcp_client: Client, mock_corrigo_client: MagicMock
    ) -> None:
        """Equipment not found — still returns generic troubleshooting prompt."""
        mock_corrigo_client.locations.get_with_attributes.side_effect = NetworkError("timeout")
        mock_corrigo_client.locations.get.side_effect = NetworkError("timeout")
        result = await mcp_client.get_prompt(
            "troubleshoot_equipment", arguments={"equipment_id": 999}
        )
        content = result.messages[0].content.text
        assert "Could not load equipment details" in content
        assert "troubleshooting" in content
