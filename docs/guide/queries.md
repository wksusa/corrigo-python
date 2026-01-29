# Query Builder Guide

The Corrigo SDK provides a fluent query builder for constructing complex queries.

## Basic Usage

```python
from corrigo.api.query import QueryBuilder

query = QueryBuilder("WorkOrder").build()
results = client.query("WorkOrder", query)
```

## Selecting Properties

### Select Specific Properties

```python
query = (
    QueryBuilder("WorkOrder")
    .select("Number", "StatusId", "DtCreated")
    .build()
)
```

### Select All Properties

```python
query = QueryBuilder("WorkOrder").select_all().build()
# Same as: .select("*")
```

### Nested Properties

Use dot notation to expand related objects:

```python
query = (
    QueryBuilder("WorkOrder")
    .select(
        "Number",
        "StatusId",
        "Priority.*",      # All Priority properties
        "Customer.Name",   # Just Customer name
        "Items.*",         # All Items properties
    )
    .build()
)
```

## Filtering

### Basic Conditions

```python
query = (
    QueryBuilder("WorkOrder")
    .where("StatusId", "Equal", "Open")
    .build()
)
```

### Using Operators

```python
from corrigo.models.enums import ConditionOperator

query = (
    QueryBuilder("WorkOrder")
    .where("StatusId", ConditionOperator.EQUAL, "Open")
    .where("Priority.Id", ConditionOperator.IN, 1, 2, 3)
    .build()
)
```

### Shortcut Methods

```python
query = (
    QueryBuilder("WorkOrder")
    .where_equal("StatusId", "Open")
    .where_not_equal("StatusId", "Cancelled")
    .where_greater_than("Id", 1000)
    .where_greater_or_equal("DtCreated", "2024-01-01")
    .where_less_than("Priority.Id", 5)
    .where_less_or_equal("DtDue", "2024-12-31")
    .where_like("Number", "WO-2024%")
    .where_in("StatusId", "Open", "InProgress")
    .where_not_in("StatusId", "Cancelled", "Closed")
    .where_is_null("AssignedEmployee")
    .where_is_not_null("Customer")
    .where_between("Id", 1000, 2000)
    .where_contains("Description", "HVAC")
    .build()
)
```

## Available Operators

| Operator | Method | Description |
|----------|--------|-------------|
| Equal | `where_equal()` | Exact match |
| NotEqual | `where_not_equal()` | Not equal |
| GreaterThan | `where_greater_than()` | Greater than |
| GreaterOrEqual | `where_greater_or_equal()` | Greater than or equal |
| LessThan | `where_less_than()` | Less than |
| LessOrEqual | `where_less_or_equal()` | Less than or equal |
| Like | `where_like()` | Pattern match (use % for wildcard) |
| NotLike | N/A | Pattern not match |
| In | `where_in()` | Value in list |
| NotIn | `where_not_in()` | Value not in list |
| IsNull | `where_is_null()` | Is null |
| IsNotNull | `where_is_not_null()` | Is not null |
| Between | `where_between()` | Between two values |
| Contains | `where_contains()` | Contains substring |

## Combining Conditions

### AND (Default)

```python
query = (
    QueryBuilder("WorkOrder")
    .where_equal("StatusId", "Open")
    .where_greater_or_equal("Priority.Id", 2)
    # Both conditions must match (AND)
    .build()
)
```

### OR

```python
query = (
    QueryBuilder("WorkOrder")
    .where_equal("StatusId", "Open")
    .where_equal("StatusId", "InProgress")
    .or_conditions()  # Either condition can match
    .build()
)
```

## Sorting

### Ascending (Default)

```python
query = (
    QueryBuilder("WorkOrder")
    .order_by("Number")
    .build()
)
```

### Descending

```python
query = (
    QueryBuilder("WorkOrder")
    .order_by("DtCreated", descending=True)
    .build()
)
```

## Pagination

### Limit Results

```python
query = (
    QueryBuilder("WorkOrder")
    .limit(100)  # Max 4000 per request
    .build()
)
```

### Offset for Pagination

```python
# Page 1
page1 = (
    QueryBuilder("WorkOrder")
    .limit(100)
    .offset(0)
    .build()
)

# Page 2
page2 = (
    QueryBuilder("WorkOrder")
    .limit(100)
    .offset(100)
    .build()
)
```

## Distinct Results

```python
query = (
    QueryBuilder("WorkOrder")
    .select("Customer.Name")
    .distinct()
    .build()
)
```

## Complete Example

```python
from corrigo.api.query import QueryBuilder

# Find high-priority open work orders from this year
query = (
    QueryBuilder("WorkOrder")
    .select(
        "Number",
        "StatusId",
        "DtCreated",
        "DtDue",
        "Priority.*",
        "Customer.Name",
        "Specialty.Name"
    )
    .where_in("StatusId", "Open", "InProgress")
    .where_less_or_equal("Priority.Id", 2)  # High priority
    .where_greater_or_equal("DtCreated", "2024-01-01")
    .order_by("DtDue")
    .limit(50)
    .build()
)

results = client.query("WorkOrder", query)

for entity in results.get("Entities", []):
    wo = entity.get("Data", {})
    print(f"{wo['Number']}: {wo['StatusId']} - Due: {wo.get('DtDue')}")
```

## Query Executor

For more control, use the QueryExecutor:

```python
from corrigo.api.query import QueryBuilder, QueryExecutor

builder = QueryBuilder("WorkOrder").where_equal("StatusId", "Open")
executor = QueryExecutor(client._http, builder)

# Get all results
results = executor.execute()

# Get first result only
first = executor.execute_first()

# Get count
count = executor.execute_count()

# Auto-paginate through all results
all_results = executor.execute_paginated(page_size=1000)
```

## API Limits

- **Maximum results per query**: 4000
- **Pagination**: Use `offset` and `limit` for larger result sets
- **Property expansion**: Avoid selecting too many nested properties for performance
