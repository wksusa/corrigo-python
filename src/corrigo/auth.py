"""OAuth 2.0 authentication for the Corrigo API."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx

from corrigo.exceptions import AuthenticationError, InvalidCredentialsError

if TYPE_CHECKING:
    pass


# OAuth token endpoint
OAUTH_TOKEN_URL = "https://oauth-pro-v2.corrigo.com/OAuth/token"

# Token refresh buffer (refresh 60 seconds before expiry)
TOKEN_REFRESH_BUFFER = 60

# Default token lifetime in seconds (20 minutes)
DEFAULT_TOKEN_LIFETIME = 20 * 60


@dataclass
class Token:
    """Represents an OAuth access token."""

    access_token: str
    token_type: str
    expires_at: float  # Unix timestamp when token expires

    @property
    def is_expired(self) -> bool:
        """Check if the token is expired or about to expire."""
        return time.time() >= (self.expires_at - TOKEN_REFRESH_BUFFER)

    @property
    def authorization_header(self) -> str:
        """Get the Authorization header value."""
        return f"{self.token_type} {self.access_token}"


class CorrigoAuth:
    """
    Handles OAuth 2.0 authentication for the Corrigo API.

    Uses the client credentials flow to obtain and refresh access tokens.
    Tokens are automatically refreshed before they expire.

    Example:
        >>> auth = CorrigoAuth(client_id="your_id", client_secret="your_secret")
        >>> token = auth.get_token()
        >>> headers = {"Authorization": token.authorization_header}
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str = OAUTH_TOKEN_URL,
    ) -> None:
        """
        Initialize the authentication handler.

        Args:
            client_id: OAuth client ID from Corrigo Enterprise settings.
            client_secret: OAuth client secret from Corrigo Enterprise settings.
            token_url: OAuth token endpoint URL (defaults to production).
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_url = token_url
        self._token: Token | None = None
        self._http_client: httpx.Client | None = None

    @property
    def _client(self) -> httpx.Client:
        """Get or create the HTTP client for token requests."""
        if self._http_client is None:
            self._http_client = httpx.Client(timeout=30.0)
        return self._http_client

    def get_token(self, force_refresh: bool = False) -> Token:
        """
        Get a valid access token, refreshing if necessary.

        Args:
            force_refresh: If True, fetch a new token even if current is valid.

        Returns:
            A valid Token object.

        Raises:
            AuthenticationError: If token retrieval fails.
        """
        if force_refresh or self._token is None or self._token.is_expired:
            self._token = self._fetch_token()
        return self._token

    def _fetch_token(self) -> Token:
        """
        Fetch a new access token from the OAuth server.

        Returns:
            A new Token object.

        Raises:
            InvalidCredentialsError: If credentials are invalid.
            AuthenticationError: If token request fails.
        """
        try:
            response = self._client.post(
                self._token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 401:
                raise InvalidCredentialsError(
                    "Invalid client credentials",
                    status_code=401,
                )

            if response.status_code != 200:
                raise AuthenticationError(
                    f"Token request failed: {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()

            # Calculate expiration time
            expires_in = data.get("expires_in", DEFAULT_TOKEN_LIFETIME)
            expires_at = time.time() + expires_in

            return Token(
                access_token=data["access_token"],
                token_type=data.get("token_type", "Bearer"),
                expires_at=expires_at,
            )

        except httpx.RequestError as e:
            raise AuthenticationError(f"Token request failed: {e}") from e

    def invalidate_token(self) -> None:
        """Invalidate the current token, forcing a refresh on next request."""
        self._token = None

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    def __enter__(self) -> CorrigoAuth:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncCorrigoAuth:
    """
    Async version of OAuth 2.0 authentication for the Corrigo API.

    Example:
        >>> async with AsyncCorrigoAuth(client_id="id", client_secret="secret") as auth:
        ...     token = await auth.get_token()
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str = OAUTH_TOKEN_URL,
    ) -> None:
        """Initialize the async authentication handler."""
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_url = token_url
        self._token: Token | None = None
        self._http_client: httpx.AsyncClient | None = None

    @property
    def _client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def get_token(self, force_refresh: bool = False) -> Token:
        """Get a valid access token, refreshing if necessary."""
        if force_refresh or self._token is None or self._token.is_expired:
            self._token = await self._fetch_token()
        return self._token

    async def _fetch_token(self) -> Token:
        """Fetch a new access token from the OAuth server."""
        try:
            response = await self._client.post(
                self._token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 401:
                raise InvalidCredentialsError(
                    "Invalid client credentials",
                    status_code=401,
                )

            if response.status_code != 200:
                raise AuthenticationError(
                    f"Token request failed: {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()
            expires_in = data.get("expires_in", DEFAULT_TOKEN_LIFETIME)
            expires_at = time.time() + expires_in

            return Token(
                access_token=data["access_token"],
                token_type=data.get("token_type", "Bearer"),
                expires_at=expires_at,
            )

        except httpx.RequestError as e:
            raise AuthenticationError(f"Token request failed: {e}") from e

    def invalidate_token(self) -> None:
        """Invalidate the current token."""
        self._token = None

    async def close(self) -> None:
        """Close the async HTTP client."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> AsyncCorrigoAuth:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
