"""Employee and invoice resource templates for the Corrigo MCP server."""

from __future__ import annotations

import json

from fastmcp import Context
from fastmcp.exceptions import ResourceError

from corrigo.exceptions import CorrigoError, NotFoundError
from corrigo.mcp.server import mcp


@mcp.resource(
    "corrigo://employees/{id}",
    tags={"employees", "read", "internal"},
)
def get_employee(id: int, ctx: Context) -> str:
    """Get an employee by ID. Internal use only."""
    client = ctx.lifespan_context["client"]
    try:
        employee = client.employees.get(id)
        return json.dumps(employee, default=str)
    except NotFoundError:
        raise ResourceError(f"Employee {id} not found") from None
    except CorrigoError as e:
        raise ResourceError(f"Error fetching employee {id}: {e.message}") from e


@mcp.resource(
    "corrigo://invoices/{id}",
    tags={"invoices", "read", "internal"},
)
def get_invoice(id: int, ctx: Context) -> str:
    """Get an invoice by ID. Internal use only."""
    client = ctx.lifespan_context["client"]
    try:
        invoice = client.invoices.get(id)
        return json.dumps(invoice, default=str)
    except NotFoundError:
        raise ResourceError(f"Invoice {id} not found") from None
    except CorrigoError as e:
        raise ResourceError(f"Error fetching invoice {id}: {e.message}") from e
