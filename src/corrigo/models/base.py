"""Base models and common structures for Corrigo entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class CorrigoEntity(BaseModel):
    """
    Base class for all Corrigo entity models.

    All entities share common fields for identification and concurrency control.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        extra="allow",  # Allow extra fields from API
    )

    id: int | None = Field(default=None, alias="Id")
    concurrency_id: int | None = Field(default=None, alias="ConcurrencyId")
    is_new: bool | None = Field(default=None, alias="IsNew")
    is_removed: bool | None = Field(default=None, alias="IsRemoved")
    perform_deletion: bool | None = Field(default=None, alias="PerformDeletion")

    def to_api_dict(self, include_none: bool = False) -> dict[str, Any]:
        """
        Convert the model to a dictionary suitable for API requests.

        Uses PascalCase field names as expected by the Corrigo API.

        Args:
            include_none: If True, include fields with None values.

        Returns:
            Dictionary with PascalCase keys.
        """
        data = self.model_dump(by_alias=True, exclude_none=not include_none)
        return data

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> CorrigoEntity:
        """
        Create a model instance from an API response.

        Args:
            data: The API response data (with PascalCase keys).

        Returns:
            A model instance.
        """
        return cls.model_validate(data)


class EntitySpecifier(BaseModel):
    """
    Represents an entity reference returned by create/update operations.

    Contains the entity type, ID, and concurrency version.
    """

    model_config = ConfigDict(populate_by_name=True)

    entity_type: str = Field(alias="EntityType")
    id: int = Field(alias="Id")
    concurrency_id: int = Field(alias="ConcurrencyId")


class PropertySet(BaseModel):
    """
    Specifies which properties to retrieve or update.

    Use "*" to retrieve all scalar properties, or specify individual
    property names. Use dot notation for nested properties.
    """

    model_config = ConfigDict(populate_by_name=True)

    properties: list[str] = Field(default_factory=list, alias="Properties")

    @classmethod
    def all(cls) -> PropertySet:
        """Get all scalar properties."""
        return cls(properties=["*"])

    @classmethod
    def select(cls, *props: str) -> PropertySet:
        """Select specific properties."""
        return cls(properties=list(props))


class MoneyValue(BaseModel):
    """Represents a monetary value with currency."""

    model_config = ConfigDict(populate_by_name=True)

    amount: float = Field(default=0.0, alias="Amount")
    currency_type: str | None = Field(default=None, alias="CurrencyType")


class Address(BaseModel):
    """Physical address structure."""

    model_config = ConfigDict(populate_by_name=True)

    street: str | None = Field(default=None, alias="Street", max_length=256)
    city: str | None = Field(default=None, alias="City", max_length=64)
    state: str | None = Field(default=None, alias="State", max_length=64)
    zip: str | None = Field(default=None, alias="Zip", max_length=16)
    country: str | None = Field(default=None, alias="Country", max_length=64)
    latitude: float | None = Field(default=None, alias="Latitude")
    longitude: float | None = Field(default=None, alias="Longitude")


class ContactInfo(BaseModel):
    """Contact information (email, phone, etc.)."""

    model_config = ConfigDict(populate_by_name=True)

    address: str | None = Field(default=None, alias="Address")
    addr_type_id: str | None = Field(default=None, alias="AddrTypeId")


class EntityReference(BaseModel):
    """A reference to another entity (by ID only)."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(alias="Id")


class PaginatedResponse(BaseModel, Generic[T]):
    """Response containing a paginated list of entities."""

    model_config = ConfigDict(populate_by_name=True)

    entities: list[T] = Field(default_factory=list, alias="Entities")
    total_count: int | None = Field(default=None, alias="TotalCount")


class QueryExpression(BaseModel):
    """
    Query expression for the Query API.

    Used to filter, sort, and paginate entity queries.
    """

    model_config = ConfigDict(populate_by_name=True)

    entity_type: str | None = Field(default=None, alias="EntityType")
    property_set: PropertySet | None = Field(default=None, alias="PropertySet")
    criteria: FilterExpression | None = Field(default=None, alias="Criteria")
    order: OrderExpression | None = Field(default=None, alias="Order")
    distinct: bool = Field(default=False, alias="Distinct")
    count: int | None = Field(default=None, alias="Count")
    first_result_index: int = Field(default=0, alias="FirstResultIndex")


class FilterExpression(BaseModel):
    """Filter criteria for queries."""

    model_config = ConfigDict(populate_by_name=True)

    conditions: list[ConditionExpression] = Field(default_factory=list, alias="Conditions")
    filter_operator: str = Field(default="And", alias="FilterOperator")
    filters: list[FilterExpression] | None = Field(default=None, alias="Filters")


class ConditionExpression(BaseModel):
    """A single filter condition."""

    model_config = ConfigDict(populate_by_name=True)

    property_name: str = Field(alias="PropertyName")
    operator: str = Field(alias="Operator")
    values: list[Any] = Field(default_factory=list, alias="Values")


class OrderExpression(BaseModel):
    """Sort order for query results."""

    model_config = ConfigDict(populate_by_name=True)

    property_name: str = Field(alias="PropertyName")
    direction: str = Field(default="Ascending", alias="Direction")  # Ascending or Descending
