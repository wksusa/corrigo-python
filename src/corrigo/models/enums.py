"""Enumerations for the Corrigo API.

Note: This is a partial list based on available documentation.
Additional enum values may be discovered through API exploration.
"""

from enum import Enum, IntEnum


class EntityType(str, Enum):
    """
    Entity types available in the Corrigo API.

    Note: The API supports 100+ entity types. This is a partial list
    of the most commonly used entities.
    """

    # Core entities
    WORK_ORDER = "WorkOrder"
    WORK_ORDER_TYPE = "WorkOrderType"
    CUSTOMER = "Customer"
    CONTACT = "Contact"
    EMPLOYEE = "Employee"
    LOCATION = "Location"
    SPACE = "Space"
    WORK_ZONE = "WorkZone"

    # Financial
    INVOICE = "Invoice"
    PAYMENT = "Payment"
    BILLING_ACCOUNT = "BillingAccount"
    VENDOR_INVOICE = "VendorInvoice"

    # Assets
    ASSET_TREE = "AssetTree"
    PORTFOLIO = "Portfolio"

    # Work order related
    WO_PRIORITY = "WoPriority"
    WO_ITEM = "WoItem"
    WO_NOTE = "WoNote"
    WO_COST = "WorkOrderCost"
    TASK = "Task"

    # Other
    DOCUMENT = "Document"
    PRODUCT = "Product"
    STOCK_LOCATION = "StockLocation"
    TIMECARD = "Timecard"
    CUSTOM_FIELD = "CustomField2"
    NOTE = "Note"


class WorkOrderStatus(str, Enum):
    """Work order status values."""

    OPEN = "Open"
    IN_PROGRESS = "InProgress"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    CLOSED = "Closed"
    ATTENTION = "Attention"


class WorkOrderType(str, Enum):
    """Work order type categories (TypeCategory field)."""

    UNKNOWN = "Unknown"
    BASIC = "Basic"
    PMRM = "PMRM"  # Preventive Maintenance / Reactive Maintenance
    TURN = "Turn"
    REQUEST = "Request"


class AssetType(IntEnum):
    """Asset/Location type identifiers."""

    UNKNOWN = 0
    BUILDING = 1
    UNIT = 2
    COMMUNITY = 3
    EQUIPMENT = 4
    FLOOR = 5
    SPACE = 6
    SYSTEM = 7


class ActorType(IntEnum):
    """Actor type identifiers for contacts and employees."""

    UNKNOWN = 0
    EMPLOYEE = 1
    CONTACT = 2
    VENDOR = 3
    CUSTOMER = 4
    COMM_LEASE_SPACE = 5


class ContactAddrType(str, Enum):
    """Contact address types."""

    CONTACT = "Contact"
    EMAIL = "Email"
    PHONE = "Phone"
    MOBILE = "Mobile"
    FAX = "Fax"
    PAGER = "Pager"


class CostCategory(str, Enum):
    """Cost item categories for WorkOrderCost."""

    LABOR = "Labor"
    MATERIAL = "Material"
    EQUIPMENT = "Equipment"
    SUBCONTRACTOR = "Subcontractor"
    OTHER = "Other"
    TRAVEL = "Travel"
    TAX = "Tax"


class InvoiceState(str, Enum):
    """Invoice state values."""

    DRAFT = "Draft"
    POSTED = "Posted"
    PAID = "Paid"
    CREDIT = "Credit"


class PaymentMethod(str, Enum):
    """Payment method types."""

    CHECK = "Check"
    CASH = "Cash"
    CREDIT_CARD = "CreditCard"
    EFT = "EFT"
    ACCOUNT_CREDIT = "AccountCredit"


class ApState(str, Enum):
    """Accounts Payable (Vendor Invoice) status values."""

    SUBMITTED = "Submitted"
    DISPUTED = "Disputed"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    PAID = "Paid"


class WOActionType(str, Enum):
    """Work order action types for status changes."""

    CREATE = "Create"
    ASSIGN = "Assign"
    PICKUP = "PickUp"
    START = "Start"
    ON_HOLD = "OnHold"
    PAUSE = "Pause"
    COMPLETE = "Complete"
    CANCEL = "Cancel"
    REOPEN = "Reopen"
    STOP = "Stop"
    VERIFIED = "Verified"
    COST_STATUS = "CostStatus"
    AP_INV_STATUS = "APInvStatus"
    FLAG = "Flag"


class ConditionOperator(str, Enum):
    """
    Operators for query filter conditions.

    Used in QueryExpression.Criteria.Conditions.
    """

    EQUAL = "Equal"
    NOT_EQUAL = "NotEqual"
    GREATER_THAN = "GreaterThan"
    GREATER_OR_EQUAL = "GreaterOrEqual"
    LESS_THAN = "LessThan"
    LESS_OR_EQUAL = "LessOrEqual"
    LIKE = "Like"
    NOT_LIKE = "NotLike"
    IN = "In"
    NOT_IN = "NotIn"
    IS_NULL = "IsNull"
    IS_NOT_NULL = "IsNotNull"
    BETWEEN = "Between"
    CONTAINS = "Contains"


class FilterOperator(str, Enum):
    """Logical operators for combining filter conditions."""

    AND = "And"
    OR = "Or"


class DataRetrievalIsolationLevel(str, Enum):
    """Database isolation levels for query operations."""

    DEFAULT = "Default"
    READ_COMMITTED = "ReadCommitted"
    READ_UNCOMMITTED = "ReadUncommitted"
    SNAPSHOT = "Snapshot"
