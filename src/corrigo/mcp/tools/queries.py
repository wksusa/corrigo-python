"""Generic query and search tools for the Corrigo MCP server."""

from __future__ import annotations

import json
from typing import Any

from fastmcp import Context
from fastmcp.exceptions import ToolError

from corrigo.exceptions import CorrigoError
from corrigo.mcp.server import handle_sdk_error, mcp

# Entity types that customer-facing agents can query
CUSTOMER_FACING_ENTITIES = {"WorkOrder", "Customer", "Location"}

# All known Corrigo entity types
VALID_ENTITY_TYPES = {
    "WorkOrder",
    "Customer",
    "Location",
    "Employee",
    "Contact",
    "WorkZone",
    "Invoice",
    "AssetAttribute",
    "AttributeDescriptor",
    "Task",
    "WorkOrderType",
    "WoPriority",
}

# Supported filter operators (suffix → QueryBuilder method)
FILTER_OPERATORS = {
    "__eq": "where_equal",
    "__ne": "where_not_equal",
    "__gt": "where_greater_than",
    "__gte": "where_greater_or_equal",
    "__lt": "where_less_than",
    "__lte": "where_less_or_equal",
    "__like": "where_like",
    "__contains": "where_contains",
    "__isnull": "where_is_null",
    "__isnotnull": "where_is_not_null",
}


def _parse_filter(key: str, value: Any, builder: Any) -> None:
    """Apply a single filter to the QueryBuilder.

    Supports Django-like suffixes:
        {"StatusId": "Open"}          → where_equal("StatusId", "Open")
        {"Name__like": "%cooler%"}    → where_like("Name", "%cooler%")
        {"DtCreated__gt": "2024-01"}  → where_greater_than("DtCreated", "2024-01")
    """
    for suffix, method_name in FILTER_OPERATORS.items():
        if key.endswith(suffix):
            field = key[: -len(suffix)]
            method = getattr(builder, method_name)
            if suffix in ("__isnull", "__isnotnull"):
                method(field)
            else:
                method(field, value)
            return

    # No operator suffix → default to equality
    builder.where_equal(key, value)


@mcp.tool(tags={"queries", "read", "internal", "customer-facing"})
def query_entities(
    entity_type: str,
    filters: dict[str, Any] | None = None,
    select: list[str] | None = None,
    limit: int = 100,
    offset: int = 0,
    order_by: str | None = None,
    descending: bool = False,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Query any Corrigo entity type with filters.

    Entity types: WorkOrder, Customer, Location, Employee, Contact,
    WorkZone, Invoice, AssetAttribute, AttributeDescriptor, Task,
    WorkOrderType, WoPriority.

    Note: Customer-facing agents are restricted to WorkOrder, Customer, Location.

    Filter syntax uses Django-like operators:
        {"StatusId": "Open"}           — equals (default)
        {"Name__like": "%cooler%"}     — LIKE pattern match
        {"DtCreated__gt": "2024-01"}   — greater than
        {"DtCreated__gte": "2024-01"}  — greater than or equal
        {"Priority.Id__lt": 5}         — less than
        {"Name__contains": "walk"}     — contains substring

    Args:
        entity_type: The Corrigo entity type to query.
        filters: Dict of field→value filters with optional operator suffixes.
        select: List of properties to return (default: all scalar properties).
        limit: Max results (capped at 4000).
        offset: Pagination offset.
        order_by: Property name to sort by.
        descending: Sort descending if True.
    """
    if entity_type not in VALID_ENTITY_TYPES:
        raise ToolError(
            f"Unknown entity type '{entity_type}'. "
            f"Valid types: {', '.join(sorted(VALID_ENTITY_TYPES))}"
        )

    # Enforce customer-facing allowlist
    # TODO: Check server tags when FastMCP provides runtime tag inspection
    # For now, the allowlist is advisory — tag filtering at server level
    # hides this tool from customer-facing clients for non-allowed types

    client = ctx.lifespan_context["client"]
    try:
        from corrigo.api.query import QueryBuilder, QueryExecutor

        builder = QueryBuilder(entity_type).limit(min(limit, 4000)).offset(offset)

        if select:
            builder.select(*select)

        if filters:
            for key, value in filters.items():
                _parse_filter(key, value, builder)

        if order_by:
            builder.order_by(order_by, descending=descending)

        results = QueryExecutor(client._http, builder).execute()
        return json.dumps(
            {
                "entity_type": entity_type,
                "results": results,
                "count": len(results),
                "has_more": len(results) == min(limit, 4000),
            },
            default=str,
        )
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"locations", "read", "internal", "customer-facing"})
def search_locations(
    name: str,
    limit: int = 100,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Search locations by name (partial match).

    Returns locations whose name contains the search term.
    Useful for finding equipment, buildings, or units by name.

    If no results are found, try searching by store number or address instead.
    """
    client = ctx.lifespan_context["client"]
    try:
        results = client.locations.search_by_name(name, limit=limit)
        if not results:
            return json.dumps(
                {
                    "results": [],
                    "count": 0,
                    "has_more": False,
                    "suggestion": (
                        f"No locations found matching '{name}'. "
                        "Try searching by store number or address instead."
                    ),
                }
            )
        return json.dumps(
            {
                "results": results,
                "count": len(results),
                "has_more": len(results) == limit,
            },
            default=str,
        )
    except CorrigoError as e:
        raise handle_sdk_error(e) from e
