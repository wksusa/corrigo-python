"""Entity-specific resource managers."""

from corrigo.api.resources.work_orders import WorkOrderResource
from corrigo.api.resources.customers import CustomerResource
from corrigo.api.resources.contacts import ContactResource
from corrigo.api.resources.employees import EmployeeResource
from corrigo.api.resources.locations import LocationResource
from corrigo.api.resources.work_zones import WorkZoneResource
from corrigo.api.resources.invoices import InvoiceResource

__all__ = [
    "WorkOrderResource",
    "CustomerResource",
    "ContactResource",
    "EmployeeResource",
    "LocationResource",
    "WorkZoneResource",
    "InvoiceResource",
]
