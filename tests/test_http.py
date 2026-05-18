"""Tests for the HTTP client module."""

import pytest
import respx
from httpx import Response

from corrigo.auth import CorrigoAuth
from corrigo.exceptions import (
    AuthorizationError,
    ConcurrencyError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TokenExpiredError,
    ValidationError,
)
from corrigo.http import CorrigoHTTPClient, Region


@pytest.fixture
def auth():
    """Create a mock auth with pre-fetched token."""
    with respx.mock:
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
        auth = CorrigoAuth(client_id="test_id", client_secret="test_secret")
        auth.get_token()  # Pre-fetch token
        return auth


@pytest.fixture
def client(auth):
    """Create an HTTP client with fixed base URL."""
    return CorrigoHTTPClient(
        auth=auth,
        company_name="TestCompany",
        region=Region.AMERICAS,
        base_url="https://test-api.corrigo.com",
    )


class TestRegion:
    """Tests for Region enum."""

    def test_region_values(self):
        """Should have correct region values."""
        assert Region.AMERICAS.value == "AM"
        assert Region.APAC.value == "APAC"
        assert Region.EMEA.value == "EMEA"


class TestCorrigoHTTPClient:
    """Tests for the CorrigoHTTPClient class."""

    def test_base_url_from_constructor(self, client):
        """Should use base URL from constructor."""
        assert client.base_url == "https://test-api.corrigo.com"

    @respx.mock
    def test_get_request(self, client):
        """Should make GET requests correctly."""
        respx.get("https://test-api.corrigo.com/api/v1/base/WorkOrder/123").mock(
            return_value=Response(200, json={"Data": {"Id": 123, "Number": "WO-001"}})
        )

        result = client.get("/base/WorkOrder/123")

        assert result["Data"]["Id"] == 123
        assert result["Data"]["Number"] == "WO-001"

    @respx.mock
    def test_get_with_params(self, client):
        """Should include query parameters."""
        route = respx.get("https://test-api.corrigo.com/api/v1/base/WorkOrder/123").mock(
            return_value=Response(200, json={"Data": {"Id": 123}})
        )

        client.get("/base/WorkOrder/123", params={"properties": "Number,StatusId"})

        assert "properties=Number%2CStatusId" in str(route.calls[0].request.url)

    @respx.mock
    def test_post_request(self, client):
        """Should make POST requests correctly."""
        respx.post("https://test-api.corrigo.com/api/v1/base/Customer").mock(
            return_value=Response(
                200,
                json={"EntitySpecifier": {"Id": 100, "EntityType": "Customer", "ConcurrencyId": 1}},
            )
        )

        result = client.post("/base/Customer", json={"Entity": {"Name": "Test"}})

        assert result["EntitySpecifier"]["Id"] == 100

    @respx.mock
    def test_put_request(self, client):
        """Should make PUT requests correctly."""
        respx.put("https://test-api.corrigo.com/api/v1/base/Customer/100").mock(
            return_value=Response(
                200,
                json={"EntitySpecifier": {"Id": 100, "ConcurrencyId": 2}},
            )
        )

        result = client.put("/base/Customer/100", json={"Entity": {"Name": "Updated"}})

        assert result["EntitySpecifier"]["ConcurrencyId"] == 2

    @respx.mock
    def test_delete_request(self, client):
        """Should make DELETE requests correctly."""
        respx.delete("https://test-api.corrigo.com/api/v1/base/Contact/200").mock(
            return_value=Response(200, json={})
        )

        result = client.delete("/base/Contact/200")

        assert result == {}

    @respx.mock
    def test_headers_included(self, client):
        """Should include required headers."""
        route = respx.get("https://test-api.corrigo.com/api/v1/base/WorkOrder/123").mock(
            return_value=Response(200, json={"Data": {}})
        )

        client.get("/base/WorkOrder/123")

        headers = route.calls[0].request.headers
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["CompanyName"] == "TestCompany"
        assert headers["Content-Type"] == "application/json"

    # Error handling tests

    @respx.mock
    def test_401_raises_token_expired(self, client):
        """Should raise TokenExpiredError on 401."""
        # Mock token endpoint for retry attempts
        respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(
                200,
                json={"access_token": "new_token", "token_type": "Bearer", "expires_in": 1200},
            )
        )
        # All retries will get 401
        respx.get("https://test-api.corrigo.com/api/v1/base/WorkOrder/123").mock(
            return_value=Response(401, json={"error": "token_expired"})
        )

        with pytest.raises(TokenExpiredError):
            client.get("/base/WorkOrder/123")

    @respx.mock
    def test_403_raises_authorization_error(self, client):
        """Should raise AuthorizationError on 403."""
        respx.get("https://test-api.corrigo.com/api/v1/base/WorkOrder/123").mock(
            return_value=Response(403, json={"error": "access_denied"})
        )

        with pytest.raises(AuthorizationError):
            client.get("/base/WorkOrder/123")

    @respx.mock
    def test_404_raises_not_found(self, client):
        """Should raise NotFoundError on 404."""
        respx.get("https://test-api.corrigo.com/api/v1/base/WorkOrder/999").mock(
            return_value=Response(404, json={"error": "not_found"})
        )

        with pytest.raises(NotFoundError):
            client.get("/base/WorkOrder/999")

    @respx.mock
    def test_409_raises_concurrency_error(self, client):
        """Should raise ConcurrencyError on 409."""
        respx.put("https://test-api.corrigo.com/api/v1/base/Customer/100").mock(
            return_value=Response(409, json={"error": "concurrency_conflict"})
        )

        with pytest.raises(ConcurrencyError):
            client.put("/base/Customer/100", json={})

    @respx.mock
    def test_422_raises_validation_error(self, client):
        """Should raise ValidationError on 422."""
        respx.post("https://test-api.corrigo.com/api/v1/base/Customer").mock(
            return_value=Response(422, json={"errors": [{"field": "Name", "message": "required"}]})
        )

        with pytest.raises(ValidationError):
            client.post("/base/Customer", json={})

    @respx.mock
    def test_429_raises_rate_limit_error(self, client):
        """Should raise RateLimitError on 429."""
        respx.get("https://test-api.corrigo.com/api/v1/base/WorkOrder/123").mock(
            return_value=Response(429, headers={"Retry-After": "60"}, json={})
        )

        with pytest.raises(RateLimitError) as exc_info:
            client.get("/base/WorkOrder/123")

        assert exc_info.value.retry_after == 60

    @respx.mock
    def test_500_raises_server_error(self, client):
        """Should raise ServerError on 5xx."""
        respx.get("https://test-api.corrigo.com/api/v1/base/WorkOrder/123").mock(
            return_value=Response(500, json={"error": "internal_error"})
        )

        with pytest.raises(ServerError):
            client.get("/base/WorkOrder/123")

    @respx.mock
    def test_503_raises_server_error(self, client):
        """Should raise ServerError on 503."""
        respx.get("https://test-api.corrigo.com/api/v1/base/WorkOrder/123").mock(
            return_value=Response(503, json={"error": "service_unavailable"})
        )

        with pytest.raises(ServerError):
            client.get("/base/WorkOrder/123")


class TestEndpointDiscovery:
    """Tests for endpoint discovery."""

    @respx.mock
    def test_discovers_endpoint_on_first_request(self):
        """Should discover endpoint when no base_url provided."""
        # Mock token endpoint
        respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(
                200,
                json={"access_token": "token", "token_type": "Bearer", "expires_in": 1200},
            )
        )

        # Mock discovery endpoint
        respx.post("https://am-apilocator.corrigo.com/api/v1/cmd/GetCompanyWsdkUrlCommand").mock(
            return_value=Response(
                200,
                json={
                    "Url": "https://discovered-endpoint.corrigo.com",
                    "CompanyName": "TestCompany",
                    "CompanyId": 12345,
                    "CompanyVersion": "9.20",
                    "Protocol": "https",
                },
            )
        )

        auth = CorrigoAuth(client_id="test_id", client_secret="test_secret")
        client = CorrigoHTTPClient(
            auth=auth,
            company_name="TestCompany",
            region=Region.AMERICAS,
        )

        assert client.base_url == "https://discovered-endpoint.corrigo.com"

    @respx.mock
    def test_raises_network_error_on_discovery_failure(self):
        """Discovery failures must raise NetworkError, not fall back silently.

        Silent fallback to the hardcoded default endpoint caused
        DATABASE_VERSION_MISMATCH errors on tenants not on that server
        (see commit f77c4ca). The contract is now: fail loudly so callers
        can log + handle.
        """
        respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(
                200,
                json={"access_token": "token", "token_type": "Bearer", "expires_in": 1200},
            )
        )
        respx.post("https://am-apilocator.corrigo.com/api/v1/cmd/GetCompanyWsdkUrlCommand").mock(
            return_value=Response(500, json={"error": "internal_error"})
        )

        auth = CorrigoAuth(client_id="test_id", client_secret="test_secret")
        client = CorrigoHTTPClient(
            auth=auth,
            company_name="TestCompany",
            region=Region.AMERICAS,
        )

        with pytest.raises(NetworkError, match="locator returned HTTP 500"):
            _ = client.base_url
