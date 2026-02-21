"""FastMCP server setup, lifespan, and error handling for Corrigo MCP."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.lifespan import lifespan

from corrigo.client import CorrigoClient
from corrigo.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConcurrencyError,
    CorrigoError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    RequiredFieldError,
    ServerError,
    ValidationError,
)

logger = logging.getLogger("corrigo.mcp")

# Required environment variables for Corrigo API access
REQUIRED_ENV_VARS = [
    "CORRIGO_CLIENT_ID",
    "CORRIGO_CLIENT_SECRET",
    "CORRIGO_COMPANY_NAME",
    "CORRIGO_REGION",
]


def handle_sdk_error(e: CorrigoError) -> ToolError:
    """Map a Corrigo SDK exception to a ToolError with a clear client message."""
    if isinstance(e, NotFoundError):
        entity_desc = ""
        if e.entity_type and e.entity_id:
            entity_desc = f"{e.entity_type} {e.entity_id}"
        elif e.entity_type:
            entity_desc = e.entity_type
        else:
            entity_desc = "Entity"
        return ToolError(
            f"{entity_desc} not found. "
            "Caller message: I wasn't able to find that. "
            "Could you double-check the information?"
        )
    if isinstance(e, RequiredFieldError):
        return ToolError(f"Required field missing: {e.field_name}")
    if isinstance(e, ValidationError):
        details = "; ".join(str(err) for err in e.errors) if e.errors else e.message
        return ToolError(f"Validation error: {details}")
    if isinstance(e, ConcurrencyError):
        return ToolError("Entity was modified by another process. Retry the operation.")
    if isinstance(e, AuthenticationError):
        return ToolError("Authentication failed. Check CORRIGO_* environment variables.")
    if isinstance(e, AuthorizationError):
        return ToolError("Permission denied for this operation.")
    if isinstance(e, RateLimitError):
        msg = "Rate limited."
        if e.retry_after:
            msg += f" Retry after {e.retry_after} seconds."
        return ToolError(msg)
    if isinstance(e, ServerError):
        return ToolError("Corrigo server error. Try again later.")
    if isinstance(e, NetworkError):
        return ToolError("Network error connecting to Corrigo API.")
    # Catch-all for any other CorrigoError subclass
    return ToolError(f"Corrigo API error: {e.message}")


@lifespan
async def corrigo_lifespan(_server: Any) -> Any:
    """Manage the CorrigoClient lifecycle.

    Validates environment variables, creates the client on startup,
    and closes it on shutdown.
    """
    # Validate all required environment variables are present
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Set these before starting the MCP server."
        )

    client = CorrigoClient(
        client_id=os.environ["CORRIGO_CLIENT_ID"],
        client_secret=os.environ["CORRIGO_CLIENT_SECRET"],
        company_name=os.environ["CORRIGO_COMPANY_NAME"],
        region=os.environ["CORRIGO_REGION"],
    )

    # Pre-cache attribute descriptors (reference data, rarely changes).
    # This eliminates N+1 HTTP calls in get_with_attributes.
    descriptor_cache: dict[int, str] = {}
    try:
        from corrigo.api.query import QueryBuilder, QueryExecutor

        descriptors = await asyncio.to_thread(
            lambda: QueryExecutor(
                client._http,
                QueryBuilder("AttributeDescriptor").select("Id", "Name").limit(500),
            ).execute()
        )
        descriptor_cache = {
            d["Id"]: d.get("Name", f"Attribute {d['Id']}") for d in descriptors if "Id" in d
        }
        logger.info("Cached %d attribute descriptors", len(descriptor_cache))
    except Exception:
        logger.warning("Could not cache attribute descriptors; will use per-request lookups")

    try:
        yield {"client": client, "descriptor_cache": descriptor_cache}
    finally:
        client.close()


mcp = FastMCP(
    "Corrigo",
    lifespan=corrigo_lifespan,
    mask_error_details=True,
    on_duplicate="error",
)


# --- Ping tool for validation ---


@mcp.tool(tags={"internal", "customer-facing"})
def ping(ctx: Context) -> str:
    """Verify the MCP server is running and connected to Corrigo."""
    client: CorrigoClient = ctx.lifespan_context["client"]
    return json.dumps(
        {
            "status": "ok",
            "company": client._company_name,
        }
    )
