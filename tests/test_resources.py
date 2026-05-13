"""Tests for entity resource managers."""

import pytest
import respx
from httpx import Response

from corrigo.auth import CorrigoAuth
from corrigo.http import CorrigoHTTPClient, Region
from corrigo.api.resources.work_orders import WorkOrderResource
from corrigo.api.resources.customers import CustomerResource
from corrigo.api.resources.contacts import ContactResource
from corrigo.api.resources.employees import EmployeeResource
from corrigo.api.resources.locations import LocationResource


@pytest.fixture
def auth():
    """Create a mock auth."""
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


class TestWorkOrderResource:
    """Tests for WorkOrderResource."""

    @respx.mock
    def test_get_work_order(self, http_client):
        """Should get a work order by ID."""
        respx.get("https://test-api.corrigo.com/api/v1/base/WorkOrder/123").mock(
            return_value=Response(
                200,
                json={"Data": {"Id": 123, "Number": "WO-001", "StatusId": "Open"}},
            )
        )

        resource = WorkOrderResource(http_client)
        result = resource.get(123)

        assert result["Id"] == 123
        assert result["Number"] == "WO-001"

    @respx.mock
    def test_create_work_order(self, http_client):
        """Should create a work order via command."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/WoCreateCommand").mock(
            return_value=Response(
                200,
                json={"WorkOrder": {"Id": 999, "Number": "WO-999"}},
            )
        )

        resource = WorkOrderResource(http_client)
        result = resource.create(
            customer_id=100,
            asset_id=200,
            task_id=300,
            subtype_id=1,
        )

        assert result["WorkOrder"]["Id"] == 999

    @respx.mock
    def test_complete_work_order(self, http_client):
        """Should complete a work order."""
        respx.post("https://test-api.corrigo.com/api/v1/cmd/WoCompleteCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        resource = WorkOrderResource(http_client)
        result = resource.complete(123, comment="Done")

        assert result["Success"] is True

    @respx.mock
    def test_list_open_work_orders(self, http_client):
        """Should list open work orders."""
        respx.post("https://test-api.corrigo.com/api/v1/query/WorkOrder").mock(
            return_value=Response(
                200,
                json={
                    "Entities": [
                        {"Data": {"Id": 1, "StatusId": "Open"}},
                        {"Data": {"Id": 2, "StatusId": "Open"}},
                    ]
                },
            )
        )

        resource = WorkOrderResource(http_client)
        results = resource.list_open(limit=10)

        assert len(results) == 2

    @respx.mock
    def test_get_by_number_exact(self, http_client):
        """Should find a work order by its full 9-digit number."""
        respx.post("https://test-api.corrigo.com/api/v1/query/WorkOrder").mock(
            return_value=Response(
                200,
                json={"Entities": [{"Data": {"Id": 42, "Number": "072460001"}}]},
            )
        )

        resource = WorkOrderResource(http_client)
        result = resource.get_by_number("072460001")

        assert result is not None
        assert result["Id"] == 42

    @respx.mock
    def test_get_by_number_pads_leading_zero(self, http_client):
        """Should zero-pad a short number and still find the work order.

        Callers (e.g. voice agents) often omit the leading zero when reading a
        work order number aloud — '72460001' instead of '072460001'.
        """
        respx.post("https://test-api.corrigo.com/api/v1/query/WorkOrder").mock(
            return_value=Response(
                200,
                json={"Entities": [{"Data": {"Id": 42, "Number": "072460001"}}]},
            )
        )

        resource = WorkOrderResource(http_client)
        result = resource.get_by_number("72460001")  # missing leading zero

        assert result is not None
        assert result["Id"] == 42

    @respx.mock
    def test_get_by_number_returns_none_when_not_found(self, http_client):
        """Should return None when no matching work order exists."""
        respx.post("https://test-api.corrigo.com/api/v1/query/WorkOrder").mock(
            return_value=Response(200, json={"Entities": []})
        )

        resource = WorkOrderResource(http_client)
        result = resource.get_by_number("000000001")

        assert result is None

    def test_delete_raises_not_implemented(self, http_client):
        """Should raise NotImplementedError for delete."""
        resource = WorkOrderResource(http_client)

        with pytest.raises(NotImplementedError):
            resource.delete(123)

    @respx.mock
    def test_list_on_hold_returns_all_when_no_reason(self, http_client):
        """Should return all OnHold WOs with LastAction.Reason populated when reason_id is None."""
        respx.post("https://test-api.corrigo.com/api/v1/query/WorkOrder").mock(
            return_value=Response(
                200,
                json={
                    "Entities": [
                        {
                            "Data": {
                                "Id": 1,
                                "StatusId": "OnHold",
                                "LastAction": {"Reason": {"Id": 1283, "DisplayAs": "Request Needs District Leader Approval"}},
                            }
                        },
                        {
                            "Data": {
                                "Id": 2,
                                "StatusId": "OnHold",
                                "LastAction": {"Reason": {"Id": 1284, "DisplayAs": "Awaiting Parts"}},
                            }
                        },
                    ]
                },
            )
        )

        resource = WorkOrderResource(http_client)
        results = resource.list_on_hold()

        assert len(results) == 2
        assert results[0]["LastAction"]["Reason"]["Id"] == 1283
        assert results[1]["LastAction"]["Reason"]["Id"] == 1284

    @respx.mock
    def test_list_on_hold_filters_by_reason_id(self, http_client):
        """Should filter client-side to WOs whose LastAction.Reason.Id matches reason_id."""
        respx.post("https://test-api.corrigo.com/api/v1/query/WorkOrder").mock(
            return_value=Response(
                200,
                json={
                    "Entities": [
                        {"Data": {"Id": 1, "StatusId": "OnHold", "LastAction": {"Reason": {"Id": 1283}}}},
                        {"Data": {"Id": 2, "StatusId": "OnHold", "LastAction": {"Reason": {"Id": 1284}}}},
                        {"Data": {"Id": 3, "StatusId": "OnHold", "LastAction": {"Reason": {"Id": 1283}}}},
                        {"Data": {"Id": 4, "StatusId": "OnHold"}},  # no LastAction at all
                    ]
                },
            )
        )

        resource = WorkOrderResource(http_client)
        results = resource.list_on_hold(reason_id=1283)

        assert [wo["Id"] for wo in results] == [1, 3]


class TestCustomerResource:
    """Tests for CustomerResource."""

    @respx.mock
    def test_get_customer(self, http_client):
        """Should get a customer by ID."""
        respx.get("https://test-api.corrigo.com/api/v1/base/Customer/100").mock(
            return_value=Response(
                200,
                json={"Data": {"Id": 100, "Name": "Test Customer"}},
            )
        )

        resource = CustomerResource(http_client)
        result = resource.get(100)

        assert result["Id"] == 100
        assert result["Name"] == "Test Customer"

    @respx.mock
    def test_create_customer(self, http_client):
        """Should create a customer."""
        respx.post("https://test-api.corrigo.com/api/v1/base/Customer").mock(
            return_value=Response(
                200,
                json={"EntitySpecifier": {"Id": 101, "EntityType": "Customer", "ConcurrencyId": 1}},
            )
        )

        resource = CustomerResource(http_client)
        result = resource.create(
            name="New Customer",
            work_zone_id=10,
            tenant_code="CUST001",
        )

        assert result["EntitySpecifier"]["Id"] == 101

    @respx.mock
    def test_list_by_work_zone(self, http_client):
        """Should list customers by work zone."""
        respx.post("https://test-api.corrigo.com/api/v1/query/Customer").mock(
            return_value=Response(
                200,
                json={
                    "Entities": [
                        {"Data": {"Id": 1, "Name": "Cust 1"}},
                        {"Data": {"Id": 2, "Name": "Cust 2"}},
                    ]
                },
            )
        )

        resource = CustomerResource(http_client)
        results = resource.list_by_work_zone(work_zone_id=10)

        assert len(results) == 2


class TestContactResource:
    """Tests for ContactResource."""

    @respx.mock
    def test_create_contact(self, http_client):
        """Should create a contact."""
        respx.post("https://test-api.corrigo.com/api/v1/base/Contact").mock(
            return_value=Response(
                200,
                json={"EntitySpecifier": {"Id": 200, "EntityType": "Contact", "ConcurrencyId": 1}},
            )
        )

        resource = ContactResource(http_client)
        result = resource.create(
            customer_id=100,
            last_name="Doe",
            username="jdoe",
            first_name="John",
            email="jdoe@example.com",
        )

        assert result["EntitySpecifier"]["Id"] == 200

    @respx.mock
    def test_get_by_email(self, http_client):
        """Should find contact by email."""
        respx.post("https://test-api.corrigo.com/api/v1/query/Contact").mock(
            return_value=Response(
                200,
                json={"Entities": [{"Data": {"Id": 200, "Username": "jdoe"}}]},
            )
        )

        resource = ContactResource(http_client)
        result = resource.get_by_email("jdoe@example.com")

        assert result["Id"] == 200


class TestEmployeeResource:
    """Tests for EmployeeResource."""

    @respx.mock
    def test_create_employee(self, http_client):
        """Should create an employee."""
        respx.post("https://test-api.corrigo.com/api/v1/base/Employee").mock(
            return_value=Response(
                200,
                json={"EntitySpecifier": {"Id": 300, "EntityType": "Employee", "ConcurrencyId": 1}},
            )
        )

        resource = EmployeeResource(http_client)
        result = resource.create(
            first_name="Jane",
            last_name="Tech",
            username="jtech",
            role_id=5,
        )

        assert result["EntitySpecifier"]["Id"] == 300

    @respx.mock
    def test_list_by_role(self, http_client):
        """Should list employees by role."""
        respx.post("https://test-api.corrigo.com/api/v1/query/Employee").mock(
            return_value=Response(
                200,
                json={
                    "Entities": [
                        {"Data": {"Id": 1, "FirstName": "Alice"}},
                        {"Data": {"Id": 2, "FirstName": "Bob"}},
                    ]
                },
            )
        )

        resource = EmployeeResource(http_client)
        results = resource.list_by_role(role_id=5)

        assert len(results) == 2


class TestLocationResource:
    """Tests for LocationResource."""

    @respx.mock
    def test_list_buildings(self, http_client):
        """Should list building locations."""
        respx.post("https://test-api.corrigo.com/api/v1/query/Location").mock(
            return_value=Response(
                200,
                json={
                    "Entities": [
                        {"Data": {"Id": 1, "Name": "Building A", "TypeId": 1}},
                        {"Data": {"Id": 2, "Name": "Building B", "TypeId": 1}},
                    ]
                },
            )
        )

        resource = LocationResource(http_client)
        results = resource.list_buildings()

        assert len(results) == 2

    @respx.mock
    def test_search_by_name(self, http_client):
        """Should search locations by name."""
        respx.post("https://test-api.corrigo.com/api/v1/query/Location").mock(
            return_value=Response(
                200,
                json={"Entities": [{"Data": {"Id": 1, "Name": "Main Building"}}]},
            )
        )

        resource = LocationResource(http_client)
        results = resource.search_by_name("Main")

        assert len(results) == 1
        assert results[0]["Name"] == "Main Building"
