"""Tests for the authentication module."""

import time

import pytest
import respx
from httpx import Response

from corrigo.auth import TOKEN_REFRESH_BUFFER, CorrigoAuth, Token
from corrigo.exceptions import AuthenticationError, InvalidCredentialsError


class TestToken:
    """Tests for the Token dataclass."""

    def test_is_expired_when_expired(self):
        """Token should be expired when past expiration time."""
        token = Token(
            access_token="test",
            token_type="Bearer",
            expires_at=time.time() - 100,  # Expired 100 seconds ago
        )
        assert token.is_expired is True

    def test_is_expired_within_buffer(self):
        """Token should be expired when within refresh buffer."""
        token = Token(
            access_token="test",
            token_type="Bearer",
            expires_at=time.time() + TOKEN_REFRESH_BUFFER - 10,  # 10 seconds before buffer
        )
        assert token.is_expired is True

    def test_is_not_expired(self):
        """Token should not be expired when well before expiration."""
        token = Token(
            access_token="test",
            token_type="Bearer",
            expires_at=time.time() + 1000,  # 1000 seconds from now
        )
        assert token.is_expired is False

    def test_authorization_header(self):
        """Should return properly formatted authorization header."""
        token = Token(
            access_token="abc123",
            token_type="Bearer",
            expires_at=time.time() + 1000,
        )
        assert token.authorization_header == "Bearer abc123"


class TestCorrigoAuth:
    """Tests for the CorrigoAuth class."""

    @respx.mock
    def test_get_token_success(self):
        """Should successfully fetch a token."""
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

        auth = CorrigoAuth(
            client_id="test_id",
            client_secret="test_secret",
        )

        token = auth.get_token()

        assert token.access_token == "test_token"
        assert token.token_type == "Bearer"
        assert token.is_expired is False

    @respx.mock
    def test_get_token_caches_token(self):
        """Should cache token and not refetch if valid."""
        route = respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(
                200,
                json={
                    "access_token": "test_token",
                    "token_type": "Bearer",
                    "expires_in": 1200,
                },
            )
        )

        auth = CorrigoAuth(
            client_id="test_id",
            client_secret="test_secret",
        )

        token1 = auth.get_token()
        token2 = auth.get_token()

        assert token1 is token2
        assert route.call_count == 1

    @respx.mock
    def test_get_token_force_refresh(self):
        """Should refetch token when force_refresh is True."""
        route = respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(
                200,
                json={
                    "access_token": "test_token",
                    "token_type": "Bearer",
                    "expires_in": 1200,
                },
            )
        )

        auth = CorrigoAuth(
            client_id="test_id",
            client_secret="test_secret",
        )

        auth.get_token()
        auth.get_token(force_refresh=True)

        assert route.call_count == 2

    @respx.mock
    def test_get_token_invalid_credentials(self):
        """Should raise InvalidCredentialsError on 401."""
        respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(401, json={"error": "invalid_client"})
        )

        auth = CorrigoAuth(
            client_id="bad_id",
            client_secret="bad_secret",
        )

        with pytest.raises(InvalidCredentialsError):
            auth.get_token()

    @respx.mock
    def test_get_token_server_error(self):
        """Should raise AuthenticationError on server error."""
        respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(500, text="Internal Server Error")
        )

        auth = CorrigoAuth(
            client_id="test_id",
            client_secret="test_secret",
        )

        with pytest.raises(AuthenticationError):
            auth.get_token()

    @respx.mock
    def test_invalidate_token(self):
        """Should clear cached token."""
        route = respx.post("https://oauth-pro-v2.corrigo.com/OAuth/token").mock(
            return_value=Response(
                200,
                json={
                    "access_token": "test_token",
                    "token_type": "Bearer",
                    "expires_in": 1200,
                },
            )
        )

        auth = CorrigoAuth(
            client_id="test_id",
            client_secret="test_secret",
        )

        auth.get_token()
        auth.invalidate_token()
        auth.get_token()

        assert route.call_count == 2
