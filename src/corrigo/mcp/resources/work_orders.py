"""Work order resource templates for the Corrigo MCP server."""

from __future__ import annotations

import json

from fastmcp import Context
from fastmcp.exceptions import ResourceError

from corrigo.exceptions import CorrigoError, NotFoundError
from corrigo.mcp.server import mcp


@mcp.resource(
    "corrigo://work-orders/{id}",
    tags={"work-orders", "read", "internal", "customer-facing"},
)
def get_work_order(id: int, ctx: Context) -> str:
    """Get a work order by ID. Returns full work order details."""
    client = ctx.lifespan_context["client"]
    try:
        wo = client.work_orders.get(id)
        return json.dumps(wo, default=str)
    except NotFoundError:
        raise ResourceError(f"Work order {id} not found") from None
    except CorrigoError as e:
        raise ResourceError(f"Error fetching work order {id}: {e.message}") from e


@mcp.resource(
    "corrigo://work-orders/number/{number}",
    tags={"work-orders", "read", "internal", "customer-facing"},
)
def get_work_order_by_number(number: str, ctx: Context) -> str:
    """Get a work order by its display number (e.g., 'WO-12345')."""
    client = ctx.lifespan_context["client"]
    try:
        wo = client.work_orders.get_by_number(number)
        if wo is None:
            raise ResourceError(f"Work order with number '{number}' not found")
        return json.dumps(wo, default=str)
    except CorrigoError as e:
        raise ResourceError(f"Error fetching work order '{number}': {e.message}") from e
