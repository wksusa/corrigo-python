"""Tests for the main CorrigoClient."""

import pytest
import respx
from httpx import Response

from corrigo import CorrigoClient
from corrigo.http import Region


@pytest.fixture
def mock_token():
    """Mock the token endpoint."""
    with respx.mock:
        respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(
                200,
                json={"access_token": "test_token", "token_type": "Bearer", "expires_in": 1200},
            )
        )
        yield


class TestCorrigoClient:
    """Tests for the CorrigoClient class."""

    def test_client_initialization(self, mock_token):
        """Should initialize client with required parameters."""
        client = CorrigoClient(
            client_id="test_id",
            client_secret="test_secret",
            company_name="TestCompany",
            base_url="https://test-api.corrigo.com",
        )

        assert client._company_name == "TestCompany"

    def test_region_string_conversion(self, mock_token):
        """Should convert string region to enum."""
        client = CorrigoClient(
            client_id="test_id",
            client_secret="test_secret",
            company_name="TestCompany",
            region="AM",
            base_url="https://test-api.corrigo.com",
        )

        assert client._region == Region.AMERICAS

    def test_region_string_case_insensitive(self, mock_token):
        """Should handle region string case insensitively."""
        client = CorrigoClient(
            client_id="test_id",
            client_secret="test_secret",
            company_name="TestCompany",
            region="apac",
            base_url="https://test-api.corrigo.com",
        )

        assert client._region == Region.APAC

    def test_work_orders_property(self, mock_token):
        """Should return WorkOrderResource from work_orders property."""
        client = CorrigoClient(
            client_id="test_id",
            client_secret="test_secret",
            company_name="TestCompany",
            base_url="https://test-api.corrigo.com",
        )

        from corrigo.api.resources.work_orders import WorkOrderResource

        assert isinstance(client.work_orders, WorkOrderResource)

    def test_customers_property(self, mock_token):
        """Should return CustomerResource from customers property."""
        client = CorrigoClient(
            client_id="test_id",
            client_secret="test_secret",
            company_name="TestCompany",
            base_url="https://test-api.corrigo.com",
        )

        from corrigo.api.resources.customers import CustomerResource

        assert isinstance(client.customers, CustomerResource)

    def test_resource_lazy_loading(self, mock_token):
        """Should lazy load resources."""
        client = CorrigoClient(
            client_id="test_id",
            client_secret="test_secret",
            company_name="TestCompany",
            base_url="https://test-api.corrigo.com",
        )

        # Resources should be None initially
        assert client._work_orders is None

        # Access property to trigger loading
        _ = client.work_orders

        # Now should be loaded
        assert client._work_orders is not None

    @respx.mock
    def test_get_method(self, mock_token):
        """Should provide low-level get method."""
        respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(
                200,
                json={"access_token": "test_token", "token_type": "Bearer", "expires_in": 1200},
            )
        )
        respx.get("https://test-api.corrigo.com/api/v1/base/WorkOrder/123").mock(
            return_value=Response(200, json={"Data": {"Id": 123}})
        )

        client = CorrigoClient(
            client_id="test_id",
            client_secret="test_secret",
            company_name="TestCompany",
            base_url="https://test-api.corrigo.com",
        )

        result = client.get("WorkOrder", 123)

        assert result["Data"]["Id"] == 123

    @respx.mock
    def test_query_method(self, mock_token):
        """Should provide low-level query method."""
        respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(
                200,
                json={"access_token": "test_token", "token_type": "Bearer", "expires_in": 1200},
            )
        )
        respx.post("https://test-api.corrigo.com/api/v1/query/WorkOrder").mock(
            return_value=Response(
                200,
                json={"Entities": [{"Data": {"Id": 1}}, {"Data": {"Id": 2}}]},
            )
        )

        client = CorrigoClient(
            client_id="test_id",
            client_secret="test_secret",
            company_name="TestCompany",
            base_url="https://test-api.corrigo.com",
        )

        result = client.query("WorkOrder", {"PropertySet": {"Properties": ["*"]}})

        assert len(result["Entities"]) == 2

    @respx.mock
    def test_execute_command_method(self, mock_token):
        """Should provide low-level execute_command method."""
        respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(
                200,
                json={"access_token": "test_token", "token_type": "Bearer", "expires_in": 1200},
            )
        )
        respx.post("https://test-api.corrigo.com/api/v1/cmd/WoCompleteCommand").mock(
            return_value=Response(200, json={"Success": True})
        )

        client = CorrigoClient(
            client_id="test_id",
            client_secret="test_secret",
            company_name="TestCompany",
            base_url="https://test-api.corrigo.com",
        )

        result = client.execute_command("WoCompleteCommand", {"WorkOrderId": 123})

        assert result["Success"] is True

    def test_context_manager(self, mock_token):
        """Should support context manager protocol."""
        with CorrigoClient(
            client_id="test_id",
            client_secret="test_secret",
            company_name="TestCompany",
            base_url="https://test-api.corrigo.com",
        ) as client:
            assert client is not None
