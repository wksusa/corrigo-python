"""Tests for the command executor module."""

import pytest
import respx
from httpx import Response

from corrigo.api.commands import CommandExecutor
from corrigo.auth import CorrigoAuth
from corrigo.http import CorrigoHTTPClient, Region


@pytest.fixture
def auth():
    """Create a mock auth with pre-fetched token."""
    with respx.mock:
        respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(
                200,
                json={"access_token": "test_token", "token_type": "Bearer", "expires_in": 1200},
            )
        )
        auth = CorrigoAuth(client_id="test_id", client_secret="test_secret")
        auth.get_token()
        return auth


@pytest.fixture
def http_client(auth):
    """Create an HTTP client."""
    return CorrigoHTTPClient(
        auth=auth,
        company_name="TestCompany",
        region=Region.AMERICAS,
        base_url="https://test-api.corrigo.com",
    )


@pytest.fixture
def executor(http_client):
    """Create a command executor."""
    return CommandExecutor(http_client)


class TestCommandExecutor:
    """Tests for the CommandExecutor class."""

    @respx.mock
    def test_execute_generic_command(self, executor):
        """Should execute a generic command."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/TestCommand").mock(
            return_value=Response(200, json={"Result": "success"})
        )

        result = executor.execute("TestCommand", Param1="value1", Param2=123)

        assert result["Result"] == "success"

    @respx.mock
    def test_create_work_order(self, executor):
        """Should create a work order via WoCreateCommand."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/WoCreateCommand").mock(
            return_value=Response(
                200,
                json={
                    "WorkOrder": {
                        "Id": 12345,
                        "Number": "WO-001",
                        "StatusId": "Open",
                    }
                },
            )
        )

        work_order = {
            "Customer": {"Id": 100},
            "SubType": {"Id": 1},
            "Items": [{"Asset": {"Id": 200}, "Task": {"Id": 300}}],
        }

        result = executor.create_work_order(
            work_order=work_order,
            compute_assignment=True,
            compute_schedule=False,
        )

        assert result["WorkOrder"]["Id"] == 12345
        assert result["WorkOrder"]["Number"] == "WO-001"

    @respx.mock
    def test_assign_work_order(self, executor):
        """Should assign a work order via WoAssignCommand."""
        route = respx.post("https://test-api.corrigo.com/api/v1/cmd/WoAssignCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        result = executor.assign_work_order(
            work_order_id=12345,
            employee_id=500,
            comment="Assigning to technician",
        )

        assert result["Success"] is True

        # Verify request body
        request_body = route.calls[0].request.content
        assert b"12345" in request_body
        assert b"500" in request_body

    @respx.mock
    def test_pickup_work_order(self, executor):
        """Should pick up a work order via WoPickUpCommand."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/WoPickUpCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        result = executor.pickup_work_order(work_order_id=12345)

        assert result["Success"] is True

    @respx.mock
    def test_start_work_order(self, executor):
        """Should start a work order via WoStartCommand."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/WoStartCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        result = executor.start_work_order(work_order_id=12345, comment="Starting work")

        assert result["Success"] is True

    @respx.mock
    def test_complete_work_order(self, executor):
        """Should complete a work order via WoCompleteCommand."""
        route = respx.post("https://test-api.corrigo.com/api/v1/cmd/WoCompleteCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        result = executor.complete_work_order(
            work_order_id=12345,
            comment="Work completed successfully",
            completion_note_option=2,
        )

        assert result["Success"] is True

        # Verify completion note option included
        request_body = route.calls[0].request.content
        assert b"CompletionNoteOption" in request_body

    @respx.mock
    def test_cancel_work_order(self, executor):
        """Should cancel a work order via WoCancelCommand with ActionReasonId."""
        route = respx.post("https://test-api.corrigo.com/api/v1/cmd/WoCancelCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        result = executor.cancel_work_order(
            work_order_id=12345,
            action_reason_id=1796,
            comment="Cancelling per customer",
        )

        assert result["Success"] is True

        # The tenant rejects free-text Reason; verify we send ActionReasonId instead.
        request_body = route.calls[0].request.content
        assert b"ActionReasonId" in request_body
        assert b"1796" in request_body
        assert b'"Reason"' not in request_body

    @respx.mock
    def test_reopen_work_order(self, executor):
        """Should reopen a work order via WoReopenCommand."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/WoReopenCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        result = executor.reopen_work_order(work_order_id=12345, comment="Reopening")

        assert result["Success"] is True

    @respx.mock
    def test_hold_work_order(self, executor):
        """Should put a work order on hold via WoOnHoldCommand."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/WoOnHoldCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        result = executor.hold_work_order(
            work_order_id=12345,
            reason="Waiting for parts",
        )

        assert result["Success"] is True

    @respx.mock
    def test_pause_work_order(self, executor):
        """Should pause a work order via WoPauseCommand."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/WoPauseCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        result = executor.pause_work_order(work_order_id=12345)

        assert result["Success"] is True

    @respx.mock
    def test_flag_work_order(self, executor):
        """Should flag a work order via WoFlagCommand."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/WoFlagCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        result = executor.flag_work_order(work_order_id=12345, flag_id=3)

        assert result["Success"] is True

    @respx.mock
    def test_send_work_order(self, executor):
        """Should send work order notification via SendWorkOrderCommand."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/SendWorkOrderCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        result = executor.send_work_order(work_order_id=12345)

        assert result["Success"] is True

    @respx.mock
    def test_verify_work(self, executor):
        """Should verify work via VerifyWorkCommand."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/VerifyWorkCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        result = executor.verify_work(
            work_order_id=12345,
            rating_id=5,
            comment="Excellent work",
        )

        assert result["Success"] is True

    @respx.mock
    def test_create_work_zone(self, executor):
        """Should create a work zone via WorkZoneCreateCommand."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/WorkZoneCreateCommand").mock(
            return_value=Response(
                200,
                json={"EntitySpecifier": {"Id": 10, "EntityType": "WorkZone", "ConcurrencyId": 1}},
            )
        )

        work_zone = {
            "DisplayAs": "Test Zone",
            "Number": "ZONE-001",
            "WoNumberPrefix": "TZ",
        }

        result = executor.create_work_zone(
            work_zone=work_zone,
            asset_template_id=1,
            skip_default_settings=False,
        )

        assert result["EntitySpecifier"]["Id"] == 10

    @respx.mock
    def test_create_space(self, executor):
        """Should create a space via SpaceCreateCommand."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/SpaceCreateCommand").mock(
            return_value=Response(
                200,
                json={"EntitySpecifier": {"Id": 50, "EntityType": "Space", "ConcurrencyId": 1}},
            )
        )

        result = executor.create_space(
            customer_id=100,
            unit_name="Unit 101",
            unit_floor_plan="FloorPlan A",
        )

        assert result["EntitySpecifier"]["Id"] == 50

    @respx.mock
    def test_change_ap_status(self, executor):
        """Should change AP status via ApStatusChangeCommand."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/ApStatusChangeCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        result = executor.change_ap_status(
            work_order_id=12345,
            vendor_invoice_status_id=2,
            comment="Approving invoice",
        )

        assert result["Success"] is True

    @respx.mock
    def test_get_company_url(self, executor):
        """Should get company URL via GetCompanyWsdkUrlCommand."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/GetCompanyWsdkUrlCommand").mock(
            return_value=Response(
                200,
                json={
                    "Url": "https://company-endpoint.corrigo.com",
                    "CompanyName": "TestCompany",
                    "CompanyId": 12345,
                    "CompanyVersion": "9.20",
                    "Protocol": "https",
                },
            )
        )

        result = executor.get_company_url(company_name="TestCompany")

        assert result["Url"] == "https://company-endpoint.corrigo.com"
        assert result["CompanyId"] == 12345
