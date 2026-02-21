"""Work order status prompt for customer-facing use."""

from __future__ import annotations

import asyncio
import json

from fastmcp import Context
from fastmcp.prompts.prompt import Message

from corrigo.mcp.server import mcp


@mcp.prompt(tags={"customer-facing", "work-orders"})
async def work_order_status(work_order_id: int, ctx: Context) -> list[Message]:
    """Provide customer-safe work order status information.

    Returns only information appropriate for sharing with customers:
    status, last update, and next steps. Excludes internal notes,
    cost data, and technician details.
    """
    client = ctx.lifespan_context["client"]

    await ctx.info(f"Fetching work order {work_order_id} status...")
    wo = await asyncio.to_thread(client.work_orders.get, work_order_id)

    # Extract only customer-safe fields
    safe_fields = {
        "Number": wo.get("Number"),
        "Status": wo.get("StatusId"),
        "Created": wo.get("DtCreated"),
        "LastUpdated": wo.get("DtModified"),
        "TypeCategory": wo.get("TypeCategory"),
    }

    return [
        Message(
            role="user",
            content=f"""Provide a customer-friendly status update for this work order:

{json.dumps(safe_fields, indent=2, default=str)}

Provide a brief, friendly status update suitable for sharing with the customer.
Do NOT mention internal details, costs, or technician assignments.
Focus on: current status, what has been done, and expected next steps.""",
        )
    ]
