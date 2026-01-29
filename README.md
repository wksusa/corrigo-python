# Corrigo SDK for Python

A Python SDK for the Corrigo Enterprise REST API, providing easy access to facilities management and work order tracking functionality.

## Installation

```bash
pip install corrigo-sdk
```

For development:
```bash
pip install corrigo-sdk[dev]
```

## Quick Start

```python
from corrigo import CorrigoClient

# Initialize the client
client = CorrigoClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    company_name="YourCompany",
    region="AM",  # Americas, APAC, or EMEA
)

# Get a work order
work_order = client.work_orders.get(12345)
print(f"Work Order: {work_order['Number']}")

# Query work orders
open_orders = client.work_orders.list(status_id="Open", limit=100)

# Create a work order
new_wo = client.work_orders.create(
    customer_id=100,
    asset_id=200,
    task_id=300,
    subtype_id=1,
    priority_id=2,
)

# Complete a work order
client.work_orders.complete(12345, comment="Work completed successfully")
```

## Features

- **OAuth 2.0 Authentication** - Automatic token management with refresh
- **Regional Support** - Americas, APAC, and EMEA endpoints
- **Dynamic Endpoint Discovery** - Automatic URL resolution per tenant
- **Fluent Query Builder** - Build complex queries with ease
- **Command Execution** - Full work order lifecycle management
- **Type Hints** - Full type annotations for IDE support
- **Async Support** - Async client for high-performance applications

## API Coverage

### Entities
- WorkOrder
- Customer
- Contact
- Employee
- Location
- WorkZone
- Invoice
- And more...

### Operations
- CRUD operations via Base API
- QueryExpression queries via Query API
- Commands via Command API (WoCreate, WoComplete, etc.)

## Query Builder

```python
from corrigo.api.query import QueryBuilder

# Build a complex query
results = (
    QueryBuilder("WorkOrder")
    .select("Number", "StatusId", "Priority.*", "Customer.Name")
    .where_equal("StatusId", "Open")
    .where_greater_or_equal("DtCreated", "2024-01-01")
    .order_by("DtCreated", descending=True)
    .limit(100)
    .build()
)
```

## Work Order Lifecycle

```python
# Create
wo = client.work_orders.create(...)

# Assign
client.work_orders.assign(wo["Id"], employee_id=100)

# Send notification
client.work_orders.send(wo["Id"])

# Start work
client.work_orders.start(wo["Id"])

# Complete
client.work_orders.complete(wo["Id"], comment="Done")
```

## Configuration

### Environment Variables

```bash
export CORRIGO_CLIENT_ID="your_client_id"
export CORRIGO_CLIENT_SECRET="your_client_secret"
export CORRIGO_COMPANY_NAME="YourCompany"
export CORRIGO_REGION="AM"
```

### Regional Endpoints

| Region | Code | Description |
|--------|------|-------------|
| Americas | AM | North and South America |
| APAC | APAC | Asia Pacific |
| EMEA | EMEA | Europe, Middle East, Africa |

## Error Handling

```python
from corrigo.exceptions import (
    CorrigoError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
)

try:
    wo = client.work_orders.get(99999)
except NotFoundError:
    print("Work order not found")
except AuthenticationError:
    print("Authentication failed")
except CorrigoError as e:
    print(f"API error: {e}")
```

## Development

```bash
# Clone the repository
git clone https://github.com/ssbean/corrigo-sdk-python.git
cd corrigo-sdk-python

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run type checking
mypy src/corrigo

# Run linting
ruff check src/corrigo
```

## License

MIT License - see LICENSE file for details.
