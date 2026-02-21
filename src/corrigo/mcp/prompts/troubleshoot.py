"""Troubleshoot equipment prompt for voice agents (customer-facing)."""

from __future__ import annotations

import asyncio
import json

from fastmcp import Context
from fastmcp.prompts.prompt import Message

from corrigo.mcp.server import mcp


@mcp.prompt(tags={"customer-facing", "locations"})
async def troubleshoot_equipment(equipment_id: int, ctx: Context) -> list[Message]:
    """Guide troubleshooting for a specific piece of equipment.

    Fetches equipment details and attributes (make, model, type) to provide
    targeted troubleshooting steps. Used by voice agents during customer calls.

    Implements tiered graceful degradation:
    - Level 1: Full context (equipment + attributes)
    - Level 2: Equipment only (attributes unavailable)
    - Level 3: Generic troubleshooting (equipment not found)
    """
    client = ctx.lifespan_context["client"]
    await ctx.info(f"Fetching equipment {equipment_id} with attributes...")

    # Try full context first, degrade gracefully
    equipment_name = "Unknown equipment"
    equipment_type = "Unknown"
    parent_name = "Unknown location"
    attributes_json = "{}"
    degradation_note = ""

    try:
        equipment = await asyncio.to_thread(client.locations.get_with_attributes, equipment_id)
        equipment_name = equipment.get("Name", "Unknown equipment")
        equipment_type = equipment.get("TypeId", "Unknown")
        parent_name = equipment.get("ParentName", "Unknown location")
        attributes_json = json.dumps(equipment.get("attributes", {}), indent=2)
    except Exception:
        # Level 2: Try basic equipment data without attributes
        try:
            equipment = await asyncio.to_thread(client.locations.get, equipment_id)
            equipment_name = equipment.get("Name", "Unknown equipment")
            equipment_type = equipment.get("TypeId", "Unknown")
            parent_name = equipment.get("ParentName", "Unknown location")
            degradation_note = (
                "\n[Could not load equipment attributes. "
                "Provide general troubleshooting for this equipment type.]"
            )
        except Exception:
            # Level 3: Generic troubleshooting
            degradation_note = (
                "\n[Could not load equipment details. "
                "Provide generic troubleshooting guidance based on the caller's description.]"
            )

    return [
        Message(
            role="user",
            content=f"""A customer is calling about a problem with this equipment:

Equipment: {equipment_name}
Type: {equipment_type}
Location: {parent_name}
Attributes: {attributes_json}
{degradation_note}
Provide exactly 3-5 troubleshooting steps as a numbered list.
Each step must be:
- One sentence, under 20 words
- An action the caller can perform without tools
- Phrased as a direct instruction ("Check the...", "Look at the...")

After each step, pause and ask if the issue is resolved.
Do NOT use technical jargon. Say "power switch" not "circuit breaker panel".
Say "the temperature dial" not "the thermostat setpoint".

If no steps resolve the issue, say:
"It sounds like this needs a technician visit. Let me create a service request for you."
Then call the create_work_order tool.""",
        )
    ]
