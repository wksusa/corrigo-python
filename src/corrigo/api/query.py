"""Fluent query builder for the Corrigo Query API."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from corrigo.models.base import (
    ConditionExpression,
    FilterExpression,
    OrderExpression,
    PropertySet,
    QueryExpression,
)
from corrigo.models.enums import ConditionOperator, FilterOperator

if TYPE_CHECKING:
    from corrigo.http import CorrigoHTTPClient


class QueryBuilder:
    """
    Fluent builder for constructing Corrigo QueryExpression objects.

    Provides a chainable API for building complex queries with filtering,
    sorting, and pagination.

    Example:
        >>> query = (QueryBuilder("WorkOrder")
        ...     .select("Number", "StatusId", "Priority.*")
        ...     .where("StatusId", ConditionOperator.EQUAL, "Open")
        ...     .where("DtCreated", ConditionOperator.GREATER_OR_EQUAL, "2024-01-01")
        ...     .order_by("DtCreated", descending=True)
        ...     .limit(100)
        ...     .build())
    """

    def __init__(self, entity_type: str) -> None:
        """
        Initialize a query builder for the specified entity type.

        Args:
            entity_type: The entity type to query (e.g., "WorkOrder", "Customer").
        """
        self._entity_type = entity_type
        self._properties: list[str] = []
        self._conditions: list[ConditionExpression] = []
        self._filter_operator = FilterOperator.AND
        self._order_by: OrderExpression | None = None
        self._count: int | None = None
        self._offset: int = 0
        self._distinct: bool = False

    def select(self, *properties: str) -> QueryBuilder:
        """
        Specify which properties to retrieve.

        Use "*" for all scalar properties, or specify individual property names.
        Use dot notation for nested properties (e.g., "Priority.*", "Customer.Name").

        Args:
            properties: Property names to retrieve.

        Returns:
            Self for chaining.
        """
        self._properties.extend(properties)
        return self

    def select_all(self) -> QueryBuilder:
        """
        Select all scalar properties.

        Returns:
            Self for chaining.
        """
        self._properties = ["*"]
        return self

    def where(
        self,
        property_name: str,
        operator: ConditionOperator | str,
        *values: Any,
    ) -> QueryBuilder:
        """
        Add a filter condition.

        Args:
            property_name: The property to filter on.
            operator: The comparison operator.
            values: The value(s) to compare against.

        Returns:
            Self for chaining.
        """
        if isinstance(operator, ConditionOperator):
            operator = operator.value

        condition = ConditionExpression(
            property_name=property_name,
            operator=operator,
            values=list(values),
        )
        self._conditions.append(condition)
        return self

    def where_equal(self, property_name: str, value: Any) -> QueryBuilder:
        """Shorthand for where(property, Equal, value)."""
        return self.where(property_name, ConditionOperator.EQUAL, value)

    def where_not_equal(self, property_name: str, value: Any) -> QueryBuilder:
        """Shorthand for where(property, NotEqual, value)."""
        return self.where(property_name, ConditionOperator.NOT_EQUAL, value)

    def where_greater_than(self, property_name: str, value: Any) -> QueryBuilder:
        """Shorthand for where(property, GreaterThan, value)."""
        return self.where(property_name, ConditionOperator.GREATER_THAN, value)

    def where_greater_or_equal(self, property_name: str, value: Any) -> QueryBuilder:
        """Shorthand for where(property, GreaterOrEqual, value)."""
        return self.where(property_name, ConditionOperator.GREATER_OR_EQUAL, value)

    def where_less_than(self, property_name: str, value: Any) -> QueryBuilder:
        """Shorthand for where(property, LessThan, value)."""
        return self.where(property_name, ConditionOperator.LESS_THAN, value)

    def where_less_or_equal(self, property_name: str, value: Any) -> QueryBuilder:
        """Shorthand for where(property, LessOrEqual, value)."""
        return self.where(property_name, ConditionOperator.LESS_OR_EQUAL, value)

    def where_like(self, property_name: str, pattern: str) -> QueryBuilder:
        """Shorthand for where(property, Like, pattern)."""
        return self.where(property_name, ConditionOperator.LIKE, pattern)

    def where_in(self, property_name: str, *values: Any) -> QueryBuilder:
        """Shorthand for where(property, In, values)."""
        return self.where(property_name, ConditionOperator.IN, *values)

    def where_not_in(self, property_name: str, *values: Any) -> QueryBuilder:
        """Shorthand for where(property, NotIn, values)."""
        return self.where(property_name, ConditionOperator.NOT_IN, *values)

    def where_is_null(self, property_name: str) -> QueryBuilder:
        """Shorthand for where(property, IsNull)."""
        return self.where(property_name, ConditionOperator.IS_NULL)

    def where_is_not_null(self, property_name: str) -> QueryBuilder:
        """Shorthand for where(property, IsNotNull)."""
        return self.where(property_name, ConditionOperator.IS_NOT_NULL)

    def where_between(self, property_name: str, min_value: Any, max_value: Any) -> QueryBuilder:
        """Shorthand for where(property, Between, min, max)."""
        return self.where(property_name, ConditionOperator.BETWEEN, min_value, max_value)

    def where_contains(self, property_name: str, value: str) -> QueryBuilder:
        """Shorthand for where(property, Contains, value)."""
        return self.where(property_name, ConditionOperator.CONTAINS, value)

    def and_conditions(self) -> QueryBuilder:
        """Combine conditions with AND (default)."""
        self._filter_operator = FilterOperator.AND
        return self

    def or_conditions(self) -> QueryBuilder:
        """Combine conditions with OR."""
        self._filter_operator = FilterOperator.OR
        return self

    def order_by(self, property_name: str, descending: bool = False) -> QueryBuilder:
        """
        Set the sort order.

        Args:
            property_name: The property to sort by.
            descending: If True, sort in descending order.

        Returns:
            Self for chaining.
        """
        self._order_by = OrderExpression(
            property_name=property_name,
            direction="Descending" if descending else "Ascending",
        )
        return self

    def limit(self, count: int) -> QueryBuilder:
        """
        Limit the number of results.

        Note: Maximum is 4000 per the Corrigo API.

        Args:
            count: Maximum number of results.

        Returns:
            Self for chaining.
        """
        self._count = min(count, 4000)  # API maximum
        return self

    def offset(self, index: int) -> QueryBuilder:
        """
        Set the starting index for pagination.

        Args:
            index: The zero-based starting index.

        Returns:
            Self for chaining.
        """
        self._offset = index
        return self

    def distinct(self, value: bool = True) -> QueryBuilder:
        """
        Enable/disable distinct results.

        Args:
            value: If True, return only distinct results.

        Returns:
            Self for chaining.
        """
        self._distinct = value
        return self

    def build(self) -> dict[str, Any]:
        """
        Build the QueryExpression as a dictionary for the API.

        Returns:
            Dictionary representation suitable for the Query API.
        """
        query: dict[str, Any] = {}

        # Property set
        if self._properties:
            query["PropertySet"] = {"Properties": self._properties}
        else:
            query["PropertySet"] = {"Properties": ["*"]}

        # Filter criteria
        if self._conditions:
            query["Criteria"] = {
                "Conditions": [
                    {
                        "PropertyName": c.property_name,
                        "Operator": c.operator,
                        "Values": c.values,
                    }
                    for c in self._conditions
                ],
                "FilterOperator": self._filter_operator.value
                if isinstance(self._filter_operator, FilterOperator)
                else self._filter_operator,
            }

        # Order
        if self._order_by:
            query["Order"] = {
                "PropertyName": self._order_by.property_name,
                "Direction": self._order_by.direction,
            }

        # Pagination
        if self._count is not None:
            query["Count"] = self._count
        if self._offset > 0:
            query["FirstResultIndex"] = self._offset

        # Distinct
        if self._distinct:
            query["Distinct"] = True

        return query

    def to_expression(self) -> QueryExpression:
        """
        Build the QueryExpression as a Pydantic model.

        Returns:
            QueryExpression model instance.
        """
        props = PropertySet(properties=self._properties if self._properties else ["*"])

        criteria = None
        if self._conditions:
            criteria = FilterExpression(
                conditions=self._conditions,
                filter_operator=self._filter_operator.value
                if isinstance(self._filter_operator, FilterOperator)
                else self._filter_operator,
            )

        return QueryExpression(
            entity_type=self._entity_type,
            property_set=props,
            criteria=criteria,
            order=self._order_by,
            count=self._count,
            first_result_index=self._offset,
            distinct=self._distinct,
        )


class QueryExecutor:
    """
    Executes queries and handles pagination.

    Wraps a QueryBuilder to execute queries against the Corrigo API
    and automatically handle pagination for large result sets.
    """

    def __init__(self, http_client: CorrigoHTTPClient, query_builder: QueryBuilder) -> None:
        """
        Initialize the executor.

        Args:
            http_client: The HTTP client for API requests.
            query_builder: The query builder with the query configuration.
        """
        self._http = http_client
        self._builder = query_builder

    def execute(self) -> list[dict[str, Any]]:
        """
        Execute the query and return all results.

        Automatically paginates if the result count exceeds the limit.

        Returns:
            List of entity data dictionaries.
        """
        query = self._builder.build()
        entity_type = self._builder._entity_type
        # Wrap query in QueryExpression as required by the API
        response = self._http.post(f"/query/{entity_type}", json={"QueryExpression": query})

        entities = response.get("Entities", [])
        results = [e.get("Data", e) for e in entities]

        return results

    def execute_first(self) -> dict[str, Any] | None:
        """
        Execute the query and return the first result.

        Returns:
            The first entity data dictionary, or None if no results.
        """
        self._builder.limit(1)
        results = self.execute()
        return results[0] if results else None

    def execute_count(self) -> int:
        """
        Execute the query and return the count of matching entities.

        Returns:
            The number of matching entities.
        """
        # Set count to 0 to get just the count without results
        query = self._builder.build()
        query["Count"] = 0
        entity_type = self._builder._entity_type
        # Wrap query in QueryExpression as required by the API
        response = self._http.post(f"/query/{entity_type}", json={"QueryExpression": query})
        return response.get("TotalCount", 0)

    def execute_paginated(self, page_size: int = 1000) -> list[dict[str, Any]]:
        """
        Execute the query with automatic pagination.

        Fetches all results by making multiple requests if necessary.

        Args:
            page_size: Number of results per page (max 4000).

        Returns:
            List of all matching entity data dictionaries.
        """
        page_size = min(page_size, 4000)
        all_results: list[dict[str, Any]] = []
        offset = 0

        while True:
            self._builder.limit(page_size).offset(offset)
            results = self.execute()

            if not results:
                break

            all_results.extend(results)

            if len(results) < page_size:
                break

            offset += page_size

        return all_results
