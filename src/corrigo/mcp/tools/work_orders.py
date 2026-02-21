"""Work order lifecycle and listing tools for the Corrigo MCP server."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastmcp import Context
from fastmcp.exceptions import ToolError

from corrigo.exceptions import CorrigoError
from corrigo.mcp.server import handle_sdk_error, mcp

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STATUS_VALUES = {"Open", "InProgress", "Paused", "Completed", "Cancelled", "all"}


def _build_listing_result(results: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    """Wrap query results in the standard listing envelope."""
    return {
        "results": results,
        "count": len(results),
        "has_more": len(results) == limit,
    }


def _build_wo_query(
    _client: Any,
    status: str,
    type_category: str | None,
    limit: int,
    offset: int,
) -> Any:
    """Build a WorkOrder QueryBuilder with common filters."""
    from corrigo.api.query import QueryBuilder

    builder = QueryBuilder("WorkOrder").limit(min(limit, 4000)).offset(offset)

    if status != "all":
        if status not in STATUS_VALUES:
            raise ToolError(
                f"Invalid status '{status}'. Valid values: {', '.join(sorted(STATUS_VALUES))}"
            )
        builder.where_equal("StatusId", status)

    if type_category:
        builder.where_equal("TypeCategory", type_category)

    return builder


def _execute_query(client: Any, builder: Any) -> list[dict[str, Any]]:
    """Execute a QueryBuilder and return results."""
    from corrigo.api.query import QueryExecutor

    return QueryExecutor(client._http, builder).execute()


# ---------------------------------------------------------------------------
# Lifecycle Tools
# ---------------------------------------------------------------------------


@mcp.tool(tags={"work-orders", "write", "internal", "customer-facing"})
def create_work_order(
    customer_id: int,
    asset_id: int,
    task_id: int,
    subtype_id: int,
    priority_id: int | None = None,
    contact_address: str | None = None,
    compute_assignment: bool = False,
    compute_schedule: bool = False,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Create a new work order.

    Required parameters:
    - customer_id: The customer requesting service
    - asset_id: The equipment/location needing service
    - task_id: The type of work to perform (query Task entities to find valid IDs)
    - subtype_id: The work order subtype (query WorkOrderType entities to find valid IDs)

    Optional:
    - priority_id: Priority level (query WoPriority entities for valid IDs)
    - contact_address: Contact email or phone for notifications
    - compute_assignment: Auto-assign to a technician
    - compute_schedule: Auto-schedule the work
    """
    client = ctx.lifespan_context["client"]
    try:
        result = client.work_orders.create(
            customer_id=customer_id,
            asset_id=asset_id,
            task_id=task_id,
            subtype_id=subtype_id,
            priority_id=priority_id,
            contact_address=contact_address,
            compute_assignment=compute_assignment,
            compute_schedule=compute_schedule,
        )
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"work-orders", "write", "internal", "customer-facing"})
async def update_work_order(
    work_order_id: int,
    updates: dict[str, Any],
    ctx: Context,
) -> str:
    """Update fields on a work order. Automatically handles concurrency.

    Fetches the current work order to get the ConcurrencyId, then applies
    the updates. The updates dict uses PascalCase field names matching the
    Corrigo API (e.g., {"Priority": {"Id": 5}, "ContactAddress": {...}}).
    """
    client = ctx.lifespan_context["client"]
    try:
        await ctx.info(f"Fetching current state of work order {work_order_id}...")
        current = await asyncio.to_thread(client.work_orders.get, work_order_id)
        concurrency_id = current.get("ConcurrencyId")
        updates["ConcurrencyId"] = concurrency_id

        await ctx.info("Applying updates...")
        result = await asyncio.to_thread(client.update, "WorkOrder", work_order_id, updates)
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"work-orders", "write", "internal"})
def assign_work_order(
    work_order_id: int,
    employee_id: int | None = None,
    comment: str | None = None,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Assign a work order to an employee. Valid when status is Open."""
    client = ctx.lifespan_context["client"]
    try:
        result = client.work_orders.assign(work_order_id, employee_id, comment)
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"work-orders", "write", "internal"})
def pickup_work_order(
    work_order_id: int,
    comment: str | None = None,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Acknowledge assignment of a work order. Valid when status is Open (assigned)."""
    client = ctx.lifespan_context["client"]
    try:
        result = client.work_orders.pickup(work_order_id, comment)
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"work-orders", "write", "internal"})
def start_work_order(
    work_order_id: int,
    comment: str | None = None,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Start work on a work order. Valid when status is Open or Paused."""
    client = ctx.lifespan_context["client"]
    try:
        result = client.work_orders.start(work_order_id, comment)
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"work-orders", "write", "internal"})
def complete_work_order(
    work_order_id: int,
    comment: str | None = None,
    completion_note_option: int = 2,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Complete a work order. Valid when status is InProgress."""
    client = ctx.lifespan_context["client"]
    try:
        result = client.work_orders.complete(work_order_id, comment, completion_note_option)
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"work-orders", "write", "internal"})
def cancel_work_order(
    work_order_id: int,
    reason: str | None = None,
    comment: str | None = None,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Cancel a work order. Valid when status is Open, InProgress, or Paused."""
    client = ctx.lifespan_context["client"]
    try:
        result = client.work_orders.cancel(work_order_id, reason, comment)
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"work-orders", "write", "internal"})
def hold_work_order(
    work_order_id: int,
    reason: str | None = None,
    comment: str | None = None,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Put a work order on hold. Valid when status is Open or InProgress."""
    client = ctx.lifespan_context["client"]
    try:
        result = client.work_orders.hold(work_order_id, reason, comment)
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"work-orders", "write", "internal"})
def pause_work_order(
    work_order_id: int,
    comment: str | None = None,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Pause a work order. Valid when status is InProgress."""
    client = ctx.lifespan_context["client"]
    try:
        result = client.work_orders.pause(work_order_id, comment)
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"work-orders", "write", "internal"})
def reopen_work_order(
    work_order_id: int,
    comment: str | None = None,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Reopen a completed or cancelled work order."""
    client = ctx.lifespan_context["client"]
    try:
        result = client.work_orders.reopen(work_order_id, comment)
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


# ---------------------------------------------------------------------------
# Listing Tools
# ---------------------------------------------------------------------------


@mcp.tool(tags={"work-orders", "read", "internal", "customer-facing"})
def list_work_orders(
    status: str = "Open",
    type_category: str | None = None,
    limit: int = 100,
    offset: int = 0,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """List work orders with optional filtering.

    Args:
        status: Filter by status — Open, InProgress, Paused, Completed, Cancelled, or "all".
        type_category: Filter by type — "Request", "PMRM", or None for all.
        limit: Max results (capped at 4000).
        offset: Pagination offset.
    """
    client = ctx.lifespan_context["client"]
    try:
        builder = _build_wo_query(client, status, type_category, limit, offset)
        results = _execute_query(client, builder)
        return json.dumps(_build_listing_result(results, limit), default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"work-orders", "read", "internal", "customer-facing"})
def list_work_orders_by_customer(
    customer_id: int,
    status: str = "Open",
    type_category: str | None = None,
    limit: int = 100,
    offset: int = 0,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """List work orders for a specific customer."""
    client = ctx.lifespan_context["client"]
    try:
        builder = _build_wo_query(client, status, type_category, limit, offset)
        builder.where_equal("Customer.Id", customer_id)
        results = _execute_query(client, builder)
        return json.dumps(_build_listing_result(results, limit), default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"work-orders", "read", "internal", "customer-facing"})
def list_work_orders_by_customers(
    customer_ids: list[int],
    status: str = "Open",
    type_category: str | None = None,
    limit: int = 100,
    offset: int = 0,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """List work orders for multiple customers (by explicit ID list)."""
    client = ctx.lifespan_context["client"]
    try:
        builder = _build_wo_query(client, status, type_category, limit, offset)
        builder.where_in("Customer.Id", *customer_ids)
        results = _execute_query(client, builder)
        return json.dumps(_build_listing_result(results, limit), default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"work-orders", "read", "internal", "customer-facing"})
async def list_work_orders_by_brand(
    brand_prefix: str,
    status: str = "Open",
    type_category: str | None = None,
    limit: int = 100,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """List work orders for all customers matching a brand prefix.

    Example: brand_prefix="WEN" matches "WEN - Store 1234", "WEN - Store 5678", etc.
    This is a two-step operation: resolve customers by brand, then query their work orders.
    """
    client = ctx.lifespan_context["client"]
    try:
        await ctx.info(f"Resolving customers for brand '{brand_prefix}'...")
        customers = await asyncio.to_thread(
            client.customers.list, limit=500, display_as__like=f"{brand_prefix} - %"
        )
        if not customers:
            raise ToolError(
                f"No customers found matching brand prefix '{brand_prefix}'. "
                "Try a different prefix or check the spelling."
            )
        customer_ids = [c["Id"] for c in customers]
        await ctx.report_progress(1, 2)
        await ctx.info(f"Found {len(customer_ids)} customers. Querying work orders...")

        builder = _build_wo_query(client, status, type_category, limit, 0)
        builder.where_in("Customer.Id", *customer_ids)
        results = await asyncio.to_thread(_execute_query, client, builder)

        return json.dumps(_build_listing_result(results, limit), default=str)
    except ToolError:
        raise
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"work-orders", "read", "internal", "customer-facing"})
def list_work_orders_by_assignee(
    employee_id: int,
    status: str = "Open",
    type_category: str | None = None,
    limit: int = 100,
    offset: int = 0,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """List work orders assigned to a specific employee."""
    client = ctx.lifespan_context["client"]
    try:
        builder = _build_wo_query(client, status, type_category, limit, offset)
        builder.where_equal("AssignedEmployee.Id", employee_id)
        results = _execute_query(client, builder)
        return json.dumps(_build_listing_result(results, limit), default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e
