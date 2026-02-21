"""Diagnose work order prompt for technicians/ops."""

from __future__ import annotations

import asyncio
import json

from fastmcp import Context
from fastmcp.prompts.prompt import Message

from corrigo.mcp.server import mcp


@mcp.prompt(tags={"internal", "work-orders"})
async def diagnose_work_order(work_order_id: int, ctx: Context) -> list[Message]:
    """Deep diagnostic context for a work order. Internal use only.

    Fetches full technical context including equipment attributes, service
    history, and customer details. Used by technicians and operations teams.
    """
    client = ctx.lifespan_context["client"]

    await ctx.info(f"Fetching work order {work_order_id} for diagnosis...")
    wo = await asyncio.to_thread(client.work_orders.get, work_order_id)

    # Fetch asset with attributes
    asset_info = "[Could not load asset data]"
    try:
        asset_id = None
        items = wo.get("Items", [])
        if items:
            asset_id = items[0].get("Asset", {}).get("Id")
        if asset_id:
            asset = await asyncio.to_thread(client.locations.get_with_attributes, asset_id)
            asset_info = json.dumps(asset, indent=2, default=str)
    except Exception as e:
        asset_info = f"[Could not load asset: {e}]"

    # Fetch customer
    customer_info = "[Could not load customer data]"
    try:
        customer_id = wo.get("Customer", {}).get("Id")
        if customer_id:
            customer = await asyncio.to_thread(client.customers.get, customer_id)
            customer_info = json.dumps(customer, indent=2, default=str)
    except Exception as e:
        customer_info = f"[Could not load customer: {e}]"

    return [
        Message(
            content=f"""Diagnose the following work order:

Work Order: {json.dumps(wo, indent=2, default=str)}

Equipment: {asset_info}

Customer: {customer_info}

Provide a technical diagnosis considering:
1. Equipment make, model, and age (from attributes)
2. Common failure modes for this equipment type
3. Parts that may be needed
4. Estimated repair complexity and time
5. Safety considerations""",
        )
    ]
