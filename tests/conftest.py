"""Pytest configuration and fixtures for Corrigo SDK tests."""

import pytest
import respx
from httpx import Response

from corrigo.auth import CorrigoAuth
from corrigo.http import CorrigoHTTPClient, Region
from corrigo.client import CorrigoClient


@pytest.fixture
def mock_token_response() -> dict:
    """Mock OAuth token response."""
    return {
        "access_token": "test_access_token_12345",
        "token_type": "Bearer",
        "expires_in": 1200,
    }


@pytest.fixture
def mock_auth(mock_token_response: dict) -> CorrigoAuth:
    """Create a CorrigoAuth instance with mocked token endpoint."""
    with respx.mock:
        respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        auth = CorrigoAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        # Pre-fetch token so it's cached
        auth.get_token()
        return auth


@pytest.fixture
def mock_http_client(mock_auth: CorrigoAuth) -> CorrigoHTTPClient:
    """Create a CorrigoHTTPClient instance with mocked auth."""
    return CorrigoHTTPClient(
        auth=mock_auth,
        company_name="TestCompany",
        region=Region.AMERICAS,
        base_url="https://test-api.corrigo.com",  # Use fixed URL to skip discovery
    )


@pytest.fixture
def mock_client() -> CorrigoClient:
    """Create a CorrigoClient instance with mocked endpoints."""
    with respx.mock:
        # Mock token endpoint
        respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(
                200,
                json={
                    "access_token": "test_token",
                    "token_type": "Bearer",
                    "expires_in": 1200,
                },
            )
        )

        client = CorrigoClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
            company_name="TestCompany",
            base_url="https://test-api.corrigo.com",
        )
        return client


# Sample entity data fixtures


@pytest.fixture
def sample_work_order() -> dict:
    """Sample work order data."""
    return {
        "Id": 12345,
        "Number": "WO-001",
        "StatusId": "Open",
        "TypeCategory": "Request",
        "ConcurrencyId": 1,
        "Customer": {"Id": 100, "Name": "Test Customer"},
        "Priority": {"Id": 1, "Name": "Normal"},
    }


@pytest.fixture
def sample_customer() -> dict:
    """Sample customer data."""
    return {
        "Id": 100,
        "Name": "Test Customer",
        "DisplayAs": "Test Customer",
        "ConcurrencyId": 1,
        "WorkZone": {"Id": 10},
        "TaxExempt": False,
    }


@pytest.fixture
def sample_contact() -> dict:
    """Sample contact data."""
    return {
        "Id": 200,
        "FirstName": "John",
        "LastName": "Doe",
        "Username": "jdoe",
        "ConcurrencyId": 1,
        "CustomerId": 100,
    }


@pytest.fixture
def sample_employee() -> dict:
    """Sample employee data."""
    return {
        "Id": 300,
        "FirstName": "Jane",
        "LastName": "Tech",
        "Username": "jtech",
        "ConcurrencyId": 1,
        "Role": {"Id": 5},
        "ActorTypeId": 1,
    }
