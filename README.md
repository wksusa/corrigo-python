# Corrigo SDK for Python

A Python SDK and CLI for the Corrigo Enterprise REST API, providing easy access to facilities management and work order tracking functionality.

## Installation

```bash
# SDK only (lightweight, no CLI dependencies)
pip install corrigo

# SDK + CLI
pip install corrigo[cli]

# Development
pip install corrigo[cli,dev]
```

Or with uv:
```bash
uv sync --all-extras
uv run corrigo --help
```

## Quick Start

### SDK Usage

```python
from corrigo import CorrigoClient

# Initialize the client
with CorrigoClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    company_name="YourCompany",
    region="AM",  # AM, APAC, or EMEA
) as client:
    # Get a work order
    work_order = client.work_orders.get(12345)
    print(f"Work Order: {work_order['Number']}")

    # List open work orders
    open_orders = client.work_orders.list(status_id="Open", limit=100)

    # Get all assets for a store/customer
    assets = client.locations.list_by_customer(163)
```

### CLI Usage

```bash
# Configure credentials
corrigo config set client_id YOUR_CLIENT_ID
corrigo config set client_secret YOUR_CLIENT_SECRET
corrigo config set company_name YOUR_COMPANY_NAME

# List work orders
corrigo work-orders list --status Open

# Get work order details
corrigo work-orders get 12345

# List assets for a store
corrigo customers assets 163
```

## Features

- **OAuth 2.0 Authentication** - Automatic token management with refresh
- **Regional Support** - Americas, APAC, and EMEA endpoints
- **Dynamic Endpoint Discovery** - Automatic URL resolution per tenant
- **Fluent Query Builder** - Build complex queries with ease
- **Command Execution** - Full work order lifecycle management
- **CLI Tool** - Full-featured command-line interface
- **Type Hints** - Full type annotations for IDE support

## CLI Reference

### Configuration

```bash
# Set credentials (stored in ~/.corrigo/config.yaml)
corrigo config set client_id YOUR_CLIENT_ID
corrigo config set client_secret YOUR_CLIENT_SECRET
corrigo config set company_name YOUR_COMPANY_NAME
corrigo config set region AM

# View configuration status
corrigo config show

# Multiple profiles
corrigo config set client_id OTHER_ID --profile production
corrigo config use production

# Debug connection issues
corrigo debug
```

### Work Orders

```bash
corrigo work-orders list                    # List work orders
corrigo work-orders list --status Open      # Filter by status
corrigo work-orders list --customer 163     # Filter by customer
corrigo work-orders get 12345               # Get details
corrigo work-orders find WO-001             # Find by number
corrigo work-orders create --customer 163 --asset 48919 --task 1 --subtype 259
```

### Customers

```bash
corrigo customers list                      # List customers
corrigo customers get 163                   # Get details
corrigo customers assets 163                # List all assets for a store
```

### Locations/Assets

```bash
corrigo locations list                      # List locations
corrigo locations buildings                 # List buildings only
corrigo locations equipment                 # List equipment only
corrigo locations search "HVAC"             # Search by name
corrigo locations details 1098              # Get asset with make/model/serial
corrigo locations equipment-details 163     # List equipment with attributes
```

### Output Formats

All commands support `--output` flag:
```bash
corrigo work-orders list --output json      # JSON output
corrigo work-orders list --output table     # Table output (default)
corrigo work-orders list --output text      # Plain text
```

## SDK Reference

### Work Orders

```python
# List work orders
orders = client.work_orders.list(limit=100)
orders = client.work_orders.list(status_id="Open")
orders = client.work_orders.list_by_customer(163)

# Get single work order
wo = client.work_orders.get(12345)
wo = client.work_orders.get_by_number("WO-001")

# Create work order
wo = client.work_orders.create(
    customer_id=163,
    asset_id=48919,
    task_id=1,
    subtype_id=259,
    priority_id=2,
)

# Work order lifecycle
client.work_orders.assign(wo_id, employee_id=100)
client.work_orders.start(wo_id)
client.work_orders.complete(wo_id, comment="Done")
client.work_orders.cancel(wo_id, reason="Duplicate")
client.work_orders.hold(wo_id, reason="Waiting for parts")
client.work_orders.reopen(wo_id)
```

### Customers

```python
# List customers
customers = client.customers.list(limit=100)
customers = client.customers.list_by_work_zone(163)

# Get customer
customer = client.customers.get(163)
customer = client.customers.get_by_tenant_code("04523")

# Create customer
customer = client.customers.create(
    name="New Store",
    work_zone_id=1,
    tenant_code="12345",
)
```

### Locations/Assets

```python
# List locations
locations = client.locations.list(limit=100)
buildings = client.locations.list_buildings()
equipment = client.locations.list_equipment()

# Get all assets for a store/customer
assets = client.locations.list_by_customer(163)

# Search locations
results = client.locations.search_by_name("HVAC")

# Get asset with attributes (make, model, serial, etc.)
asset = client.locations.get_with_attributes(1098)
# Returns: {'Name': 'Dough Press 1', 'attributes': {'Model #': 'DP1300', 'Manufacturer Name': 'Proluxe'}}

# List equipment with attributes for a customer
equipment = client.locations.list_equipment_with_attributes(customer_id)
```

### Query Builder

For complex queries, use the QueryBuilder:

```python
from corrigo.api.query import QueryBuilder, QueryExecutor

# Build a complex query
builder = (
    QueryBuilder("WorkOrder")
    .select("Number", "StatusId", "Priority.*", "Customer.Name")
    .where_equal("StatusId", "Open")
    .where_greater_or_equal("DtCreated", "2024-01-01")
    .order_by("DtCreated", descending=True)
    .limit(100)
)

# Execute the query
executor = QueryExecutor(client._http, builder)
results = executor.execute()
```

## Data Model Nuances

Understanding Corrigo's data model is key to effective API usage.

### Assets and Customers

In Corrigo, assets (Locations) are linked to customers through `CommunityId`:

```python
# Location.CommunityId == Customer.Id
# To get all assets for a store:
assets = client.locations.list_by_customer(customer_id)

# This queries: Location WHERE CommunityId = customer_id
```

Asset types (`TypeId`):
| TypeId | Description |
|--------|-------------|
| Building | Physical building |
| Unit | Unit within a building |
| Community | Community/complex |
| Equipment | Specific equipment |
| Regular | General asset |
| RoomArea | Room or area |

### Work Orders and Assets

Work orders reference assets through `MainAsset`:

```python
wo = client.work_orders.get(12345)
asset_id = wo["MainAsset"]["Id"]  # The primary asset for this work order
location = wo["ShortLocation"]     # Human-readable location string
```

### Customers and Work Zones

Each customer belongs to a WorkZone:

```python
customer = client.customers.get(163)
work_zone_id = customer["WorkZone"]["Id"]  # Usually same as customer ID
```

### Equipment Attributes (Make, Model, Serial)

Detailed equipment info is stored in `AssetAttribute`, not on the Location entity directly:

```python
# Get asset with all attributes resolved
asset = client.locations.get_with_attributes(1098)
print(asset["attributes"])
# {'Model #': 'DP1300', 'Manufacturer Name': 'Proluxe'}
```

Available attribute types (defined in `AttributeDescriptor`):
| Attribute | Description |
|-----------|-------------|
| Model # | Equipment model number |
| Serial # | Serial number |
| Manufacturer Name | Make/brand |
| Voltage | Electrical voltage |
| Electrical Phase | Single/three phase |
| Date in Service | Installation date |
| Original Cost | Purchase price |
| Replacement Cost | Current replacement value |

Note: Not all equipment has attributes populated - it depends on data entry practices.

## Configuration

### Environment Variables

```bash
export CORRIGO_CLIENT_ID="your_client_id"
export CORRIGO_CLIENT_SECRET="your_client_secret"
export CORRIGO_COMPANY_NAME="YourCompany"
export CORRIGO_REGION="AM"
```

Environment variables take precedence over config file values.

### Config File

Credentials are stored in `~/.corrigo/config.yaml`:

```yaml
default_profile: default
profiles:
  default:
    client_id: your_client_id
    client_secret: your_client_secret
    company_name: YourCompany
    region: AM
  production:
    client_id: prod_client_id
    client_secret: prod_client_secret
    company_name: ProdCompany
    region: AM
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
    RateLimitError,
)

try:
    wo = client.work_orders.get(99999)
except NotFoundError:
    print("Work order not found")
except AuthenticationError:
    print("Authentication failed - check credentials")
except RateLimitError as e:
    print(f"Rate limited - retry after {e.retry_after} seconds")
except CorrigoError as e:
    print(f"API error: {e}")
```

## Troubleshooting

### Debug Connection

```bash
corrigo debug
```

This shows:
1. Credential status
2. OAuth token retrieval
3. Endpoint discovery
4. API connectivity

### Common Issues

**Endpoint discovery fails (400)**
- Check that `company_name` matches exactly (case-sensitive)

**503 Server Error**
- The discovered endpoint may be wrong
- Try a different region or contact Corrigo support

**Authentication failed**
- Verify `client_id` and `client_secret`
- Ensure OAuth credentials have appropriate permissions

## Development

```bash
# Clone the repository
git clone https://github.com/ssbean/corrigo-python.git
cd corrigo-python

# Using uv (recommended)
uv sync
uv run pytest

# Or traditional virtualenv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

MIT License - see LICENSE file for details.
