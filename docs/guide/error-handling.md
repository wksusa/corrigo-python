# Error Handling

The Corrigo SDK provides a comprehensive exception hierarchy for handling API errors.

## Exception Hierarchy

```
CorrigoError (base)
├── AuthenticationError
│   ├── InvalidCredentialsError
│   └── TokenExpiredError
├── AuthorizationError
├── ValidationError
│   └── RequiredFieldError
├── NotFoundError
├── ConcurrencyError
├── RateLimitError
├── ServerError
└── NetworkError
```

## Basic Error Handling

```python
from corrigo.exceptions import CorrigoError

try:
    result = client.work_orders.get(12345)
except CorrigoError as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Response data: {e.response_data}")
```

## Handling Specific Errors

### Authentication Errors

```python
from corrigo.exceptions import AuthenticationError, InvalidCredentialsError, TokenExpiredError

try:
    client = CorrigoClient(
        client_id="wrong_id",
        client_secret="wrong_secret",
        company_name="TestCompany",
    )
    client.work_orders.list()
except InvalidCredentialsError:
    print("Invalid client ID or secret")
except TokenExpiredError:
    print("Token expired - this shouldn't happen with auto-refresh")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
```

### Authorization Errors

```python
from corrigo.exceptions import AuthorizationError

try:
    # Attempting an operation without permission
    result = client.work_orders.complete(12345)
except AuthorizationError:
    print("You don't have permission for this operation")
```

### Not Found Errors

```python
from corrigo.exceptions import NotFoundError

try:
    wo = client.work_orders.get(99999)
except NotFoundError as e:
    print(f"Work order not found")
    print(f"Entity type: {e.entity_type}")
    print(f"Entity ID: {e.entity_id}")
```

### Validation Errors

```python
from corrigo.exceptions import ValidationError, RequiredFieldError

try:
    # Missing required field
    customer = client.customers.create(
        name="Test",
        # work_zone_id is required but missing
    )
except RequiredFieldError as e:
    print(f"Missing required field: {e.field_name}")
except ValidationError as e:
    print(f"Validation failed: {e}")
    print(f"Errors: {e.errors}")
```

### Concurrency Errors

```python
from corrigo.exceptions import ConcurrencyError

try:
    # Another process modified this entity
    result = client.customers.update(
        entity_id=100,
        data={
            "Entity": {"Id": 100, "ConcurrencyId": 1, "Name": "Updated"},
            "PropertySet": {"Properties": ["Name"]},
        },
    )
except ConcurrencyError as e:
    print("Entity was modified by another process")
    print("Refresh the entity and try again")

    # Refresh and retry
    customer = client.customers.get(100)
    result = client.customers.update(
        entity_id=100,
        data={
            "Entity": {
                "Id": 100,
                "ConcurrencyId": customer["ConcurrencyId"],
                "Name": "Updated",
            },
            "PropertySet": {"Properties": ["Name"]},
        },
    )
```

### Rate Limit Errors

```python
import time
from corrigo.exceptions import RateLimitError

try:
    results = client.work_orders.list()
except RateLimitError as e:
    if e.retry_after:
        print(f"Rate limited. Retry after {e.retry_after} seconds")
        time.sleep(e.retry_after)
        results = client.work_orders.list()
    else:
        raise
```

### Server Errors

```python
from corrigo.exceptions import ServerError

try:
    result = client.work_orders.get(12345)
except ServerError as e:
    print(f"Server error ({e.status_code}): {e.message}")
    # Log for investigation, possibly retry later
```

### Network Errors

```python
from corrigo.exceptions import NetworkError

try:
    result = client.work_orders.get(12345)
except NetworkError as e:
    print(f"Network error: {e}")
    # Check network connectivity, retry
```

## HTTP Status Code Mapping

| Status Code | Exception |
|-------------|-----------|
| 401 | TokenExpiredError |
| 403 | AuthorizationError |
| 404 | NotFoundError |
| 409 | ConcurrencyError |
| 422 | ValidationError |
| 429 | RateLimitError |
| 5xx | ServerError |

## Error Response Data

All exceptions include the original response data:

```python
try:
    result = client.work_orders.get(99999)
except CorrigoError as e:
    # Access error details
    print(f"Message: {e.message}")
    print(f"Status Code: {e.status_code}")
    print(f"Response: {e.response_data}")
```

## Retry Logic

The SDK includes automatic retry for transient errors:

- **TokenExpiredError**: Refreshes token and retries (up to 3 times)
- **NetworkError**: Retries with exponential backoff (up to 3 times)

For other errors, implement your own retry logic:

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from corrigo.exceptions import ServerError

@retry(
    retry=lambda e: isinstance(e, ServerError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
def get_work_order_with_retry(client, wo_id):
    return client.work_orders.get(wo_id)
```

## Best Practices

1. **Catch specific exceptions** when you need to handle them differently
2. **Catch CorrigoError** as a fallback for unexpected errors
3. **Log errors** with full context for debugging
4. **Handle ConcurrencyError** by refreshing and retrying
5. **Respect rate limits** by implementing proper backoff

```python
import logging
from corrigo.exceptions import (
    CorrigoError,
    NotFoundError,
    ValidationError,
    ConcurrencyError,
)

logger = logging.getLogger(__name__)

def safe_get_work_order(client, wo_id):
    try:
        return client.work_orders.get(wo_id)
    except NotFoundError:
        logger.warning(f"Work order {wo_id} not found")
        return None
    except ValidationError as e:
        logger.error(f"Validation error: {e.errors}")
        raise
    except ConcurrencyError:
        logger.warning(f"Concurrency conflict on {wo_id}, retrying...")
        return client.work_orders.get(wo_id)
    except CorrigoError as e:
        logger.error(f"API error [{e.status_code}]: {e.message}")
        raise
```
