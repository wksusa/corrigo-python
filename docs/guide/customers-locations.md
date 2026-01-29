# Customers & Locations

This guide covers managing customers, contacts, locations, and the entity hierarchy.

## Entity Hierarchy

```
WorkZone
    └── Customer
            ├── Contact
            └── Space (links to Location/Asset)
```

## Work Zones

Work zones define service delivery areas with operational parameters.

### Create a Work Zone

```python
# Work zones require the WorkZoneCreateCommand
work_zone = client.work_zones.create(
    display_as="Downtown District",
    asset_template_id=1,
    number="WZ-001",
    wo_number_prefix="DT",
    time_zone=5,  # Eastern
)
```

### Get a Work Zone

```python
wz = client.work_zones.get(10)
```

### Find by Number

```python
wz = client.work_zones.get_by_number("WZ-001")
```

!!! note
    Work zones cannot be deleted via the API.

## Customers

Customers represent client organizations that request services.

### Create a Customer

```python
customer = client.customers.create(
    name="Acme Corporation",
    work_zone_id=10,
    display_as="Acme Corp",
    tenant_code="ACME001",  # Unique identifier
    tax_exempt=False,
)
```

### Get a Customer

```python
customer = client.customers.get(100)
```

### Find by Tenant Code

```python
customer = client.customers.get_by_tenant_code("ACME001")
```

### List Customers in a Work Zone

```python
customers = client.customers.list_by_work_zone(work_zone_id=10)
```

### Update a Customer

```python
customer = client.customers.get(100)
result = client.customers.update(
    entity_id=100,
    data={
        "Entity": {
            "Id": 100,
            "ConcurrencyId": customer["ConcurrencyId"],
            "DisplayAs": "Acme Corporation Inc.",
        },
        "PropertySet": {"Properties": ["DisplayAs"]},
    },
)
```

## Contacts

Contacts are people who can request work or interact with the Customer Portal.

### Create a Contact

```python
contact = client.contacts.create(
    customer_id=100,
    first_name="John",
    last_name="Doe",
    username="jdoe",
    email="jdoe@acme.com",
    phone="555-123-4567",
    number="EMP001",  # Employee/contact number
)
```

### Get a Contact

```python
contact = client.contacts.get(200)
```

### Find by Username

```python
contact = client.contacts.get_by_username("jdoe")
```

### Find by Email

```python
contact = client.contacts.get_by_email("jdoe@acme.com")
```

### List Contacts for a Customer

```python
contacts = client.contacts.list_by_customer(customer_id=100)
```

## Employees

Employees represent internal users and service professionals.

### Create an Employee

```python
employee = client.employees.create(
    first_name="Jane",
    last_name="Tech",
    username="jtech",
    role_id=5,  # Role determines permissions
    number="TECH001",
    email="jtech@company.com",
    phone="555-987-6543",
    access_to_all_work_zones=True,
)
```

### Get an Employee

```python
employee = client.employees.get(300)
```

### Find by Username

```python
employee = client.employees.get_by_username("jtech")
```

### Find by Employee Number

```python
employee = client.employees.get_by_number("TECH001")
```

### List by Role

```python
technicians = client.employees.list_by_role(role_id=5)
```

### List Available for Assignment

```python
available = client.employees.list_available_for_assignment()
```

## Locations

Locations represent physical assets in the hierarchy.

### Asset Types

| Type ID | Name | Description |
|---------|------|-------------|
| 1 | Building | Physical building |
| 2 | Unit | Unit within a building |
| 3 | Community | Community/campus |
| 4 | Equipment | Equipment asset |
| 5 | Floor | Floor within a building |
| 6 | Space | Generic space |
| 7 | System | Building system |

### Create a Location

```python
location = client.locations.create(
    name="Main Office Building",
    model_id=1,  # Asset template
    type_id=1,   # Building
    address={
        "Street": "123 Main Street",
        "City": "Anytown",
        "State": "CA",
        "Zip": "12345",
    },
)
```

### Get a Location

```python
location = client.locations.get(400)
```

### List Buildings

```python
buildings = client.locations.list_buildings(limit=100)
```

### List Units

```python
units = client.locations.list_units(limit=100)
```

### List Equipment

```python
equipment = client.locations.list_equipment(limit=100)
```

### Search by Name

```python
results = client.locations.search_by_name("Main")
```

## Spaces

Spaces link customers to physical locations.

### Create a Space

Spaces require the SpaceCreateCommand:

```python
from corrigo.api.commands import CommandExecutor

commands = CommandExecutor(client._http)

space = commands.create_space(
    customer_id=100,
    unit_name="Suite 101",
    unit_floor_plan="FloorPlan-A",
    street_address={
        "Street": "123 Main St, Suite 101",
        "City": "Anytown",
        "State": "CA",
        "Zip": "12345",
    },
)
```

## Complete Setup Example

Here's a complete example setting up a new customer location:

```python
from corrigo import CorrigoClient
from corrigo.api.commands import CommandExecutor

client = CorrigoClient(...)
commands = CommandExecutor(client._http)

# 1. Create Work Zone (if needed)
work_zone = client.work_zones.create(
    display_as="North Region",
    asset_template_id=1,
    number="NR-001",
    wo_number_prefix="NR",
)
wz_id = work_zone["EntitySpecifier"]["Id"]

# 2. Create Customer
customer = client.customers.create(
    name="New Customer Inc",
    work_zone_id=wz_id,
    tenant_code="NC001",
)
cust_id = customer["EntitySpecifier"]["Id"]

# 3. Create Space
space = commands.create_space(
    customer_id=cust_id,
    unit_name="Main Office",
    street_address={
        "Street": "456 Business Ave",
        "City": "Commerce City",
        "State": "CA",
        "Zip": "90210",
    },
)

# 4. Create Contact
contact = client.contacts.create(
    customer_id=cust_id,
    first_name="Bob",
    last_name="Manager",
    username="bmanager",
    email="bob@newcustomer.com",
)

print(f"Setup complete for customer {cust_id}")
```
