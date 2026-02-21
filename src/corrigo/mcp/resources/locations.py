"""Location resource templates for the Corrigo MCP server."""

from __future__ import annotations

import json

from fastmcp import Context
from fastmcp.exceptions import ResourceError

from corrigo.exceptions import CorrigoError, NotFoundError
from corrigo.mcp.server import mcp


@mcp.resource(
    "corrigo://locations/{id}",
    tags={"locations", "read", "internal", "customer-facing"},
)
def get_location(id: int, ctx: Context) -> str:
    """Get a location by ID."""
    client = ctx.lifespan_context["client"]
    try:
        location = client.locations.get(id)
        return json.dumps(location, default=str)
    except NotFoundError:
        raise ResourceError(f"Location {id} not found") from None
    except CorrigoError as e:
        raise ResourceError(f"Error fetching location {id}: {e.message}") from e


@mcp.resource(
    "corrigo://locations/{id}/attributes",
    tags={"locations", "read", "internal", "customer-facing"},
)
def get_location_attributes(id: int, ctx: Context) -> str:
    """Get a location/asset with all attributes (make, model, serial, etc.).

    Returns the base location data plus an 'attributes' dict with resolved
    attribute names and values.
    """
    client = ctx.lifespan_context["client"]
    try:
        location = client.locations.get_with_attributes(id)
        return json.dumps(location, default=str)
    except NotFoundError:
        raise ResourceError(f"Location {id} not found") from None
    except CorrigoError as e:
        raise ResourceError(f"Error fetching location {id} attributes: {e.message}") from e
