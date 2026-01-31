"""HTTP client for the Corrigo API with automatic endpoint discovery."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from corrigo.auth import CorrigoAuth, Token
from corrigo.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConcurrencyError,
    CorrigoError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TokenExpiredError,
    ValidationError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Region(Enum):
    """Corrigo API regions."""

    AMERICAS = "AM"
    APAC = "APAC"
    EMEA = "EMEA"


# API Locator URLs for endpoint discovery
API_LOCATOR_URLS = {
    Region.AMERICAS: "https://am-apilocator.corrigo.com/api/v1/cmd/GetCompanyWsdkUrlCommand",
    Region.APAC: "https://apac-apilocator.corrigo.com/api/v1/cmd/GetCompanyWsdkUrlCommand",
    Region.EMEA: "https://emea-apilocator.corrigo.com/api/v1/cmd/GetCompanyWsdkUrlCommand",
}

# Default regional endpoints (fallback if discovery fails)
DEFAULT_ENDPOINTS = {
    Region.AMERICAS: "https://am-ent-f2b.corrigo.com",
    Region.APAC: "https://apac-ent-f1.corrigo.com",
    Region.EMEA: "https://az-emea-ent-f1.corrigo.com",
}


@dataclass
class CompanyInfo:
    """Information about a Corrigo company/tenant."""

    url: str
    company_name: str
    company_id: int
    company_version: str
    protocol: str


class CorrigoHTTPClient:
    """
    Low-level HTTP client for the Corrigo API.

    Handles authentication, endpoint discovery, request/response processing,
    and error handling. Supports automatic token refresh and retry logic.

    Example:
        >>> auth = CorrigoAuth(client_id="id", client_secret="secret")
        >>> client = CorrigoHTTPClient(auth=auth, company_name="MyCompany", region=Region.AMERICAS)
        >>> response = client.get("/base/WorkOrder/123")
    """

    def __init__(
        self,
        auth: CorrigoAuth,
        company_name: str,
        region: Region = Region.AMERICAS,
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        """
        Initialize the HTTP client.

        Args:
            auth: Authentication handler for OAuth tokens.
            company_name: The Corrigo company/tenant name.
            region: API region (Americas, APAC, or EMEA).
            base_url: Override the base URL (skips endpoint discovery).
            timeout: Request timeout in seconds.
        """
        self._auth = auth
        self._company_name = company_name
        self._region = region
        self._base_url = base_url
        self._timeout = timeout
        self._company_info: CompanyInfo | None = None
        self._http_client: httpx.Client | None = None

    @property
    def _client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(
                timeout=self._timeout,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip, deflate",
                },
            )
        return self._http_client

    @property
    def base_url(self) -> str:
        """Get the base URL, discovering it if necessary."""
        if self._base_url:
            return self._base_url
        if self._company_info:
            return self._company_info.url
        # Discover endpoint
        self._company_info = self._discover_endpoint()
        return self._company_info.url

    def _discover_endpoint(self) -> CompanyInfo:
        """
        Discover the actual API endpoint for this company.

        Returns:
            CompanyInfo with the discovered URL and metadata.

        Raises:
            CorrigoError: If endpoint discovery fails.
        """
        locator_url = API_LOCATOR_URLS[self._region]
        token = self._auth.get_token()

        try:
            response = self._client.post(
                locator_url,
                json={"Command": {"CompanyName": self._company_name}},
                headers={
                    "Authorization": token.authorization_header,
                    "Content-Type": "application/json",
                    "CompanyName": self._company_name,
                },
            )

            if response.status_code != 200:
                logger.warning(
                    f"Endpoint discovery failed ({response.status_code}), using default"
                )
                return CompanyInfo(
                    url=DEFAULT_ENDPOINTS[self._region],
                    company_name=self._company_name,
                    company_id=0,
                    company_version="unknown",
                    protocol="https",
                )

            data = response.json()
            # Response is nested under CommandResult
            result = data.get("CommandResult", data)

            # Extract base URL from WSDL URL (e.g., http://az-am-ent-f8.corrigo.com/wsdk/... -> https://az-am-ent-f8.corrigo.com)
            raw_url = result.get("Url", "")
            if raw_url:
                from urllib.parse import urlparse
                parsed = urlparse(raw_url)
                # Use HTTPS and just the hostname
                base_url = f"https://{parsed.netloc}"
            else:
                base_url = DEFAULT_ENDPOINTS[self._region]

            return CompanyInfo(
                url=base_url,
                company_name=result.get("CompanyName", self._company_name),
                company_id=result.get("CompanyId", 0),
                company_version=result.get("CompanyVersion", "unknown"),
                protocol=result.get("Protocol", "https"),
            )

        except httpx.RequestError as e:
            logger.warning(f"Endpoint discovery failed: {e}, using default")
            return CompanyInfo(
                url=DEFAULT_ENDPOINTS[self._region],
                company_name=self._company_name,
                company_id=0,
                company_version="unknown",
                protocol="https",
            )

    def _get_headers(self, token: Token) -> dict[str, str]:
        """Build request headers."""
        return {
            "Authorization": token.authorization_header,
            "Content-Type": "application/json",
            "CompanyName": self._company_name,
        }

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """
        Process an API response, raising appropriate exceptions for errors.

        Args:
            response: The HTTP response to process.

        Returns:
            The parsed JSON response data.

        Raises:
            Various CorrigoError subclasses based on status code.
        """
        status = response.status_code

        # Try to parse response body
        try:
            data = response.json() if response.content else {}
        except ValueError:
            data = {"raw": response.text}

        if status == 200:
            return data

        if status == 401:
            self._auth.invalidate_token()
            raise TokenExpiredError(
                "Authentication token expired or invalid",
                status_code=status,
                response_data=data,
            )

        if status == 403:
            raise AuthorizationError(
                "Access denied",
                status_code=status,
                response_data=data,
            )

        if status == 404:
            raise NotFoundError(
                status_code=status,
                response_data=data,
            )

        if status == 409:
            raise ConcurrencyError(
                status_code=status,
                response_data=data,
            )

        if status == 422:
            raise ValidationError(
                "Validation failed",
                status_code=status,
                response_data=data,
            )

        if status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                retry_after=int(retry_after) if retry_after else None,
                status_code=status,
                response_data=data,
            )

        if 500 <= status < 600:
            raise ServerError(
                f"Server error: {status}",
                status_code=status,
                response_data=data,
            )

        raise CorrigoError(
            f"Request failed with status {status}",
            status_code=status,
            response_data=data,
        )

    @retry(
        retry=retry_if_exception_type((TokenExpiredError, NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Make an HTTP request to the Corrigo API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            path: API path (e.g., "/base/WorkOrder/123").
            params: Query parameters.
            json: JSON request body.
            headers: Additional headers.

        Returns:
            Parsed JSON response.

        Raises:
            CorrigoError: On API errors.
            NetworkError: On network failures.
        """
        url = f"{self.base_url}/api/v1{path}"
        token = self._auth.get_token()
        request_headers = self._get_headers(token)
        if headers:
            request_headers.update(headers)

        try:
            response = self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=request_headers,
            )
            return self._handle_response(response)

        except httpx.RequestError as e:
            raise NetworkError(f"Network error: {e}") from e

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make a GET request."""
        return self.request("GET", path, params=params, **kwargs)

    def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make a POST request."""
        return self.request("POST", path, json=json, **kwargs)

    def put(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make a PUT request."""
        return self.request("PUT", path, json=json, **kwargs)

    def delete(
        self,
        path: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", path, headers=headers, **kwargs)

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    def __enter__(self) -> CorrigoHTTPClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
