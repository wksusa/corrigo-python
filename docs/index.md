# Corrigo SDK for Python

A comprehensive Python SDK for the Corrigo Enterprise REST API, providing easy access to facilities management and work order tracking functionality.

## Features

- **OAuth 2.0 Authentication** - Automatic token management with refresh
- **Regional Support** - Americas, APAC, and EMEA endpoints
- **Dynamic Endpoint Discovery** - Automatic URL resolution per tenant
- **Fluent Query Builder** - Build complex queries with ease
- **Command Execution** - Full work order lifecycle management
- **Type Hints** - Full type annotations for IDE support
- **Async Support** - Async client for high-performance applications

## Quick Example

```python
from corrigo import CorrigoClient

# Initialize the client
client = CorrigoClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    company_name="YourCompany",
    region="AM",
)

# Query open work orders
open_orders = client.work_orders.list_open(limit=100)

for wo in open_orders:
    print(f"Work Order {wo['Number']}: {wo['StatusId']}")

# Complete a work order
client.work_orders.complete(12345, comment="Work finished")
```

## Installation

```bash
pip install corrigo-sdk
```

## Regional Support

| Region | Code | Endpoint |
|--------|------|----------|
| Americas | `AM` | am-ent-f2b.corrigo.com |
| APAC | `APAC` | apac-ent-f1.corrigo.com |
| EMEA | `EMEA` | az-emea-ent-f1.corrigo.com |

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

- **Base API** - CRUD operations (GET, POST, PUT, DELETE)
- **Query API** - QueryExpression-based data retrieval
- **Command API** - Specialized commands (WoCreateCommand, etc.)

## Next Steps

- [Installation Guide](getting-started/installation.md)
- [Quick Start Tutorial](getting-started/quickstart.md)
- [API Reference](api/client.md)
