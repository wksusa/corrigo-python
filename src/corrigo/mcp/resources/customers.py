"""Customer resource templates for the Corrigo MCP server."""

from __future__ import annotations

import json

from fastmcp import Context
from fastmcp.exceptions import ResourceError

from corrigo.exceptions import CorrigoError, NotFoundError
from corrigo.mcp.server import mcp


@mcp.resource(
    "corrigo://customers/{id}",
    tags={"customers", "read", "internal", "customer-facing"},
)
def get_customer(id: int, ctx: Context) -> str:
    """Get a customer by ID."""
    client = ctx.lifespan_context["client"]
    try:
        customer = client.customers.get(id)
        return json.dumps(customer, default=str)
    except NotFoundError:
        raise ResourceError(f"Customer {id} not found") from None
    except CorrigoError as e:
        raise ResourceError(f"Error fetching customer {id}: {e.message}") from e


@mcp.resource(
    "corrigo://customers/{id}/assets",
    tags={"customers", "read", "internal", "customer-facing"},
)
def get_customer_assets(id: int, ctx: Context) -> str:
    """List all assets/locations for a customer."""
    client = ctx.lifespan_context["client"]
    try:
        assets = client.locations.list_by_customer(id)
        return json.dumps(assets, default=str)
    except CorrigoError as e:
        raise ResourceError(f"Error fetching assets for customer {id}: {e.message}") from e
