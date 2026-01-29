# Quick Start

This guide will help you get started with the Corrigo SDK in just a few minutes.

## Initialize the Client

```python
from corrigo import CorrigoClient

client = CorrigoClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    company_name="YourCompany",
    region="AM",  # Americas, APAC, or EMEA
)
```

## Get a Work Order

```python
# Get by ID
work_order = client.work_orders.get(12345)
print(f"Work Order: {work_order['Number']}")
print(f"Status: {work_order['StatusId']}")

# Get with specific properties
work_order = client.work_orders.get(
    12345,
    properties=["Number", "StatusId", "Priority.*", "Customer.Name"]
)
```

## Query Work Orders

```python
# List open work orders
open_orders = client.work_orders.list_open(limit=100)

# List with filters
orders = client.work_orders.list(
    status_id="InProgress",
    limit=50
)

# Use the query builder for complex queries
from corrigo.api.query import QueryBuilder

results = (
    QueryBuilder("WorkOrder")
    .select("Number", "StatusId", "DtCreated")
    .where_equal("StatusId", "Open")
    .where_greater_or_equal("DtCreated", "2024-01-01")
    .order_by("DtCreated", descending=True)
    .limit(100)
    .build()
)

response = client.query("WorkOrder", results)
```

## Create a Work Order

```python
# Create a new work order
new_wo = client.work_orders.create(
    customer_id=100,
    asset_id=200,
    task_id=300,
    subtype_id=1,
    priority_id=2,
    compute_assignment=True,  # Auto-assign
)

print(f"Created: {new_wo['WorkOrder']['Number']}")
```

## Work Order Lifecycle

```python
work_order_id = 12345

# Assign to a technician
client.work_orders.assign(work_order_id, employee_id=500)

# Send notification
client.work_orders.send(work_order_id)

# Technician picks up the work
client.work_orders.pickup(work_order_id)

# Start work
client.work_orders.start(work_order_id)

# Complete the work
client.work_orders.complete(work_order_id, comment="Work completed successfully")
```

## Working with Customers

```python
# Get a customer
customer = client.customers.get(100)

# Create a customer
new_customer = client.customers.create(
    name="Acme Corporation",
    work_zone_id=10,
    tenant_code="ACME001",
)

# List customers in a work zone
customers = client.customers.list_by_work_zone(work_zone_id=10)
```

## Working with Contacts

```python
# Create a contact
contact = client.contacts.create(
    customer_id=100,
    first_name="John",
    last_name="Doe",
    username="jdoe",
    email="jdoe@example.com",
)

# Find by email
contact = client.contacts.get_by_email("jdoe@example.com")
```

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
    print("Authentication failed - check credentials")
except CorrigoError as e:
    print(f"API error: {e}")
```

## Using Context Manager

```python
with CorrigoClient(
    client_id="your_id",
    client_secret="your_secret",
    company_name="YourCompany",
) as client:
    orders = client.work_orders.list_open()
    # Client is automatically closed when done
```

## Next Steps

- [Authentication Guide](authentication.md) - Deep dive into OAuth setup
- [Work Orders Guide](../guide/work-orders.md) - Complete work order management
- [Query Guide](../guide/queries.md) - Advanced query techniques
