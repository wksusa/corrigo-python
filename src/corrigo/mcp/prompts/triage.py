"""Triage work order prompt for internal ops/dispatch."""

from __future__ import annotations

import asyncio
import json

from fastmcp import Context

from corrigo.mcp.server import mcp


@mcp.prompt(tags={"internal", "work-orders"})
async def triage_work_order(work_order_id: int, ctx: Context) -> str:
    """Triage a work order for dispatch. Fetches full context for prioritization.

    Internal prompt for ops/dispatch teams. Provides the work order details,
    customer info, and asset data to help decide priority and assignment.
    """
    client = ctx.lifespan_context["client"]

    await ctx.info(f"Fetching work order {work_order_id} for triage...")
    wo = await asyncio.to_thread(client.work_orders.get, work_order_id)

    # Fetch related data with graceful degradation
    customer_info = "[Could not load customer data]"
    try:
        customer_id = wo.get("Customer", {}).get("Id")
        if customer_id:
            customer = await asyncio.to_thread(client.customers.get, customer_id)
            customer_info = json.dumps(customer, indent=2, default=str)
    except Exception as e:
        customer_info = f"[Could not load customer: {e}]"

    return f"""Triage the following work order for dispatch:

Work Order: {json.dumps(wo, indent=2, default=str)}

Customer: {customer_info}

Assess priority, recommend assignment, and identify any urgency factors.
Consider: equipment type, customer SLA tier, time since creation, and
whether this is a repeat issue."""
