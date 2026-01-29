# Authentication

The Corrigo SDK uses OAuth 2.0 with the client credentials flow for authentication.

## How It Works

1. The SDK exchanges your client ID and secret for an access token
2. Tokens are automatically cached and refreshed before expiration
3. All API requests include the token in the Authorization header

## Basic Setup

```python
from corrigo import CorrigoClient

client = CorrigoClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    company_name="YourCompany",
    region="AM",
)
```

## Using Environment Variables

For security, store credentials in environment variables:

```bash
export CORRIGO_CLIENT_ID="your_client_id"
export CORRIGO_CLIENT_SECRET="your_client_secret"
export CORRIGO_COMPANY_NAME="YourCompany"
export CORRIGO_REGION="AM"
```

```python
import os
from corrigo import CorrigoClient

client = CorrigoClient(
    client_id=os.environ["CORRIGO_CLIENT_ID"],
    client_secret=os.environ["CORRIGO_CLIENT_SECRET"],
    company_name=os.environ["CORRIGO_COMPANY_NAME"],
    region=os.environ.get("CORRIGO_REGION", "AM"),
)
```

## Low-Level Authentication

For advanced use cases, you can use the authentication classes directly:

```python
from corrigo.auth import CorrigoAuth

auth = CorrigoAuth(
    client_id="your_client_id",
    client_secret="your_client_secret",
)

# Get a token
token = auth.get_token()
print(f"Token: {token.access_token}")
print(f"Expires at: {token.expires_at}")
print(f"Is expired: {token.is_expired}")

# Force refresh
new_token = auth.get_token(force_refresh=True)

# Invalidate cached token
auth.invalidate_token()
```

## Token Lifecycle

- **Expiration**: Tokens expire every 20 minutes
- **Auto-refresh**: The SDK refreshes tokens 60 seconds before expiration
- **Caching**: Tokens are cached to minimize authentication requests
- **Thread-safe**: Token management is safe for concurrent use

## OAuth Token Endpoint

The SDK uses the production OAuth endpoint:

```
https://oauth-pro-v2.corrigo.com/OAuth/token
```

## Regional Endpoints

Different regions use different API locator endpoints for URL discovery:

| Region | Locator URL |
|--------|-------------|
| Americas | `https://am-apilocator.corrigo.com/api/v1/cmd/GetCompanyWsdkUrlCommand` |
| APAC | `https://apac-apilocator.corrigo.com/api/v1/cmd/GetCompanyWsdkUrlCommand` |
| EMEA | `https://emea-apilocator.corrigo.com/api/v1/cmd/GetCompanyWsdkUrlCommand` |

## Endpoint Discovery

The SDK automatically discovers the correct API endpoint for your company:

```python
from corrigo.http import CorrigoHTTPClient, Region
from corrigo.auth import CorrigoAuth

auth = CorrigoAuth(client_id="...", client_secret="...")
client = CorrigoHTTPClient(
    auth=auth,
    company_name="YourCompany",
    region=Region.AMERICAS,
)

# The base URL is discovered automatically
print(f"Discovered URL: {client.base_url}")
```

## Skipping Discovery

If you know your endpoint URL, you can skip discovery:

```python
client = CorrigoClient(
    client_id="your_id",
    client_secret="your_secret",
    company_name="YourCompany",
    base_url="https://your-specific-endpoint.corrigo.com",
)
```

## Async Authentication

For async applications:

```python
from corrigo.auth import AsyncCorrigoAuth

async with AsyncCorrigoAuth(
    client_id="your_id",
    client_secret="your_secret",
) as auth:
    token = await auth.get_token()
    print(f"Token: {token.access_token}")
```

## Troubleshooting

### Invalid Credentials Error

```python
from corrigo.exceptions import InvalidCredentialsError

try:
    client = CorrigoClient(...)
    client.work_orders.list()
except InvalidCredentialsError:
    print("Check your client_id and client_secret")
```

### Token Expired Error

The SDK handles token refresh automatically, but if you see this error:

```python
from corrigo.exceptions import TokenExpiredError

try:
    result = client.work_orders.get(123)
except TokenExpiredError:
    # This shouldn't happen with auto-refresh
    # But you can force a token refresh
    client._auth.invalidate_token()
    result = client.work_orders.get(123)
```
