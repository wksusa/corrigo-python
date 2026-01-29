# Installation

## Requirements

- Python 3.9 or higher
- A Corrigo Enterprise account with API access

## Install from PyPI

```bash
pip install corrigo-sdk
```

## Install with Development Dependencies

```bash
pip install corrigo-sdk[dev]
```

This includes:

- pytest - Testing framework
- respx - HTTP mocking
- mypy - Type checking
- ruff - Linting

## Install from Source

```bash
git clone https://github.com/ssbean/corrigo-sdk-python.git
cd corrigo-sdk-python
pip install -e ".[dev]"
```

## Verify Installation

```python
from corrigo import CorrigoClient, __version__

print(f"Corrigo SDK version: {__version__}")
```

## Dependencies

The SDK depends on:

| Package | Purpose |
|---------|---------|
| httpx | HTTP client |
| pydantic | Data validation |
| python-dateutil | Date handling |
| tenacity | Retry logic |

## Getting API Credentials

Before using the SDK, you need to obtain API credentials from Corrigo Enterprise:

1. Log in to Corrigo Enterprise as an administrator
2. Navigate to **Admin & Settings > Global Configuration**
3. Go to **Settings & Terminology > Integration API Settings**
4. Click **Generate Credentials** to create a new client ID and secret

!!! warning "Important"
    Credentials are displayed only once. Copy both the Client ID and Client Secret
    before closing the dialog - they cannot be retrieved later.

## Service User Setup

For API access, create a dedicated service user:

1. Create a new user account for API access
2. Assign the **WSDK** role (or any role with "Permissions - Web Services Access")
3. Use these credentials when generating API credentials
