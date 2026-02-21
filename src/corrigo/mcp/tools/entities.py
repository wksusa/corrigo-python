"""Entity CRUD tools for the Corrigo MCP server."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastmcp import Context

from corrigo.exceptions import CorrigoError
from corrigo.mcp.server import handle_sdk_error, mcp


@mcp.tool(tags={"customers", "write", "internal"})
def create_customer(
    name: str,
    work_zone_id: int,
    display_as: str | None = None,
    tenant_code: str | None = None,
    tax_exempt: bool = False,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Create a new customer.

    Args:
        name: Customer name (max 64 chars).
        work_zone_id: The work zone ID (required).
        display_as: Display name (defaults to name).
        tenant_code: Unique tenant code.
        tax_exempt: Whether customer is tax exempt.
    """
    client = ctx.lifespan_context["client"]
    try:
        result = client.customers.create(
            name=name,
            work_zone_id=work_zone_id,
            display_as=display_as,
            tenant_code=tenant_code,
            tax_exempt=tax_exempt,
        )
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"customers", "write", "internal"})
async def update_customer(
    customer_id: int,
    updates: dict[str, Any],
    ctx: Context,
) -> str:
    """Update fields on a customer. Automatically handles concurrency.

    The updates dict uses PascalCase field names matching the Corrigo API.
    """
    client = ctx.lifespan_context["client"]
    try:
        await ctx.info(f"Fetching current state of customer {customer_id}...")
        current = await asyncio.to_thread(client.customers.get, customer_id)
        concurrency_id = current.get("ConcurrencyId")
        updates["ConcurrencyId"] = concurrency_id

        await ctx.info("Applying updates...")
        result = await asyncio.to_thread(client.update, "Customer", customer_id, updates)
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"contacts", "write", "internal"})
def create_contact(
    customer_id: int,
    last_name: str,
    username: str,
    first_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Create a new contact for a customer.

    Args:
        customer_id: The customer this contact belongs to.
        last_name: Contact's last name (required).
        username: Login username (max 256 chars, required).
        first_name: Contact's first name.
        email: Contact email address.
        phone: Contact phone number.
    """
    client = ctx.lifespan_context["client"]
    try:
        result = client.contacts.create(
            customer_id=customer_id,
            last_name=last_name,
            username=username,
            first_name=first_name,
            email=email,
            phone=phone,
        )
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"employees", "write", "internal"})
def create_employee(
    first_name: str,
    last_name: str,
    username: str,
    role_id: int,
    number: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Create a new employee.

    Args:
        first_name: Employee's first name (required).
        last_name: Employee's last name (required).
        username: Login username (max 256 chars, required).
        role_id: The role ID for permissions (required).
        number: Employee identifier/number.
        email: Employee email address.
        phone: Employee phone number.
    """
    client = ctx.lifespan_context["client"]
    try:
        result = client.employees.create(
            first_name=first_name,
            last_name=last_name,
            username=username,
            role_id=role_id,
            number=number,
            email=email,
            phone=phone,
        )
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e


@mcp.tool(tags={"locations", "write", "internal"})
def create_location(
    name: str,
    model_id: int,
    type_id: str = "Building",
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Create a new location (building, unit, or equipment).

    Args:
        name: Location name (max 64 chars).
        model_id: The model/template ID (required).
        type_id: Asset type — Building, Unit, Community, Equipment, etc.
    """
    client = ctx.lifespan_context["client"]
    try:
        result = client.locations.create(
            name=name,
            model_id=model_id,
            type_id=type_id,
        )
        return json.dumps(result, default=str)
    except CorrigoError as e:
        raise handle_sdk_error(e) from e
