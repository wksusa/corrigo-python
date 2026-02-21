"""Issue intake prompt for customer-facing use (call center/voice agent)."""

from __future__ import annotations

import asyncio
import json

from fastmcp import Context
from fastmcp.prompts.prompt import Message

from corrigo.mcp.server import mcp


@mcp.prompt(tags={"customer-facing", "work-orders"})
async def report_issue(customer_id: int, description: str, ctx: Context) -> list[Message]:
    """Guide intake of a new service request from a customer.

    Fetches customer details and assets to help identify the right equipment
    and collect information needed for work order creation.
    """
    client = ctx.lifespan_context["client"]

    await ctx.info("Fetching customer and assets...")
    customer = await asyncio.to_thread(client.customers.get, customer_id)

    # Fetch customer assets with graceful degradation
    equipment_info = "[Could not load equipment list]"
    try:
        assets = await asyncio.to_thread(client.locations.list_by_customer, customer_id)
        equipment = [
            {"id": a["Id"], "name": a.get("Name", "Unknown")}
            for a in assets
            if a.get("TypeId") == "Equipment"
        ]
        if equipment:
            equipment_info = json.dumps(equipment, indent=2)
        else:
            equipment_info = "No equipment found for this customer."
    except Exception as e:
        equipment_info = f"[Could not load equipment: {e}]"

    return [
        Message(
            role="user",
            content=f"""A customer is reporting an issue.

Customer: {customer.get("DisplayAs", "Unknown")} (ID: {customer_id})
Issue: {description}

Equipment at this location:
{equipment_info}

Help identify which equipment is affected, confirm the issue details,
and if a work order is needed, call the create_work_order tool with:
- customer_id: {customer_id}
- asset_id: [the identified equipment ID]
- task_id: [appropriate task ID]
- subtype_id: [appropriate subtype ID]""",
        )
    ]
