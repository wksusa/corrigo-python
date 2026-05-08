# Work Orders

Work orders are the core entity in Corrigo, representing service requests and maintenance work items.

## Work Order Lifecycle

```
Create → Assign → Send → PickUp → Start → Complete
                                    ↓
                              On Hold / Pause
                                    ↓
                            Cancel / Reopen
```

## Getting Work Orders

### Get by ID

```python
wo = client.work_orders.get(12345)
print(f"Number: {wo['Number']}")
print(f"Status: {wo['StatusId']}")
```

### Get with Specific Properties

```python
wo = client.work_orders.get(
    12345,
    properties=[
        "Number",
        "StatusId",
        "Priority.*",      # Expand Priority object
        "Customer.Name",   # Nested property
        "Items.*",         # Expand Items collection
    ]
)
```

### Get by Work Order Number

```python
wo = client.work_orders.get_by_number("WO-2024-001")
```

## Querying Work Orders

### List Open Work Orders

```python
open_orders = client.work_orders.list_open(limit=100)
```

### List In-Progress Work Orders

```python
in_progress = client.work_orders.list_in_progress(limit=100)
```

### List by Customer

```python
customer_orders = client.work_orders.list_by_customer(
    customer_id=100,
    limit=50
)
```

### Custom Queries

```python
from corrigo.api.query import QueryBuilder, QueryExecutor

# Build a complex query
query = (
    QueryBuilder("WorkOrder")
    .select("Number", "StatusId", "DtCreated", "Priority.*")
    .where_equal("StatusId", "Open")
    .where_greater_or_equal("DtCreated", "2024-01-01")
    .where_in("Priority.Id", 1, 2, 3)
    .order_by("DtCreated", descending=True)
    .limit(100)
    .build()
)

# Execute
results = client.query("WorkOrder", query)
```

## Creating Work Orders

Work orders require specific commands due to their complex dependencies.

### Basic Creation

```python
wo = client.work_orders.create(
    customer_id=100,
    asset_id=200,       # Location/Asset ID
    task_id=300,        # Task definition
    subtype_id=1,       # Work order type
)
```

### With Auto-Assignment

```python
wo = client.work_orders.create(
    customer_id=100,
    asset_id=200,
    task_id=300,
    subtype_id=1,
    priority_id=2,
    compute_assignment=True,   # Auto-assign based on rules
    compute_schedule=True,     # Auto-schedule
)
```

### With Contact Information

```python
wo = client.work_orders.create(
    customer_id=100,
    asset_id=200,
    task_id=300,
    subtype_id=1,
    contact_address="requestor@example.com",
)
```

## Managing Work Order Status

### Assign

```python
# Assign to a specific employee
client.work_orders.assign(
    work_order_id=12345,
    employee_id=500,
    comment="Assigned to senior technician"
)

# Assign without specifying employee (uses auto-assignment rules)
client.work_orders.assign(work_order_id=12345)
```

### Send Notification

```python
# Notify the assigned service professional
client.work_orders.send(work_order_id=12345)
```

### Pick Up

```python
# Technician acknowledges the assignment
client.work_orders.pickup(
    work_order_id=12345,
    comment="On my way"
)
```

### Start

```python
# Begin work
client.work_orders.start(
    work_order_id=12345,
    comment="Starting repair"
)
```

### Complete

```python
# Finish the work
client.work_orders.complete(
    work_order_id=12345,
    comment="Replaced HVAC filter, system running normally"
)
```

### Put on Hold

```python
client.work_orders.hold(
    work_order_id=12345,
    reason="Waiting for parts",
    comment="Ordered replacement motor, ETA 3 days"
)
```

### Pause

```python
client.work_orders.pause(
    work_order_id=12345,
    comment="End of shift, will resume tomorrow"
)
```

### Cancel

`action_reason_id` is required — Corrigo's `WoCancelCommand` rejects calls
without a tenant-configured cancel-reason ID. Reason records are not exposed
via the Query API; obtain valid IDs from the Corrigo admin UI or by inspecting
prior cancels in `WoActionLog` (`TypeId = "Cancel"`).

```python
client.work_orders.cancel(
    work_order_id=12345,
    action_reason_id=1796,  # tenant-specific
    comment="Customer resolved issue themselves",
)
```

### Reopen

```python
client.work_orders.reopen(
    work_order_id=12345,
    comment="Issue reoccurred, needs follow-up"
)
```

## Flags

```python
# Set a flag on a work order
client.work_orders.flag(
    work_order_id=12345,
    flag_id=3,  # Flag ID from your system
    comment="Requires supervisor attention"
)
```

## Verification

```python
# Verify completed work (for systems with verification workflows)
client.work_orders.verify(
    work_order_id=12345,
    rating_id=5,  # Quality rating
    comment="Work verified and approved"
)
```

## Work Order Properties

| Property | Type | Description |
|----------|------|-------------|
| Id | int | Unique identifier |
| Number | string | Work order number (auto-generated) |
| StatusId | enum | Open, InProgress, Paused, Completed, Cancelled, Closed |
| TypeCategory | enum | Unknown, Basic, PMRM, Turn, Request |
| Priority | object | Priority level reference |
| Specialty | object | Service type specification |
| Customer | object | Customer reference |
| Items | array | Work order line items |
| DtCreated | datetime | Creation timestamp |
| DtDue | datetime | Due date |

## Entities That Cannot Be Deleted

Work orders cannot be deleted via the API. Use `cancel()` instead:

```python
# This will raise NotImplementedError
# client.work_orders.delete(12345)

# Use cancel instead
client.work_orders.cancel(12345, action_reason_id=1796)
```
