"""Customer overview prompt for account managers."""

from __future__ import annotations

import asyncio
import json

from fastmcp import Context
from fastmcp.prompts.prompt import Message

from corrigo.mcp.server import mcp


@mcp.prompt(tags={"internal", "customers"})
async def customer_overview(customer_id: int, ctx: Context) -> list[Message]:
    """Generate an overview of a customer for account management.

    Fetches customer details, assets, and recent work orders to provide
    a comprehensive view of the customer's facilities and service history.
    """
    client = ctx.lifespan_context["client"]

    await ctx.info(f"Fetching customer {customer_id} overview...")
    customer = await asyncio.to_thread(client.customers.get, customer_id)

    # Fetch assets
    assets_info = "[Could not load assets]"
    try:
        assets = await asyncio.to_thread(client.locations.list_by_customer, customer_id)
        assets_info = json.dumps(assets, indent=2, default=str)
    except Exception as e:
        assets_info = f"[Could not load assets: {e}]"

    # Fetch recent work orders
    wo_info = "[Could not load work orders]"
    try:
        work_orders = await asyncio.to_thread(
            client.work_orders.list_by_customer, customer_id, limit=20
        )
        wo_info = json.dumps(work_orders, indent=2, default=str)
    except Exception as e:
        wo_info = f"[Could not load work orders: {e}]"

    return [
        Message(
            role="user",
            content=f"""Provide an overview of this customer:

Customer: {json.dumps(customer, indent=2, default=str)}

Assets/Locations: {assets_info}

Recent Work Orders: {wo_info}

Summarize:
1. Customer profile and key details
2. Number and types of assets
3. Work order trends (frequency, types, common issues)
4. Any concerns or opportunities for the account""",
        )
    ]
