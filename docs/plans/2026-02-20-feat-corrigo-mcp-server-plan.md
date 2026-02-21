---
title: "feat: Corrigo MCP Server"
type: feat
status: active
date: 2026-02-20
deepened: 2026-02-20
---

## Enhancement Summary

**Deepened on:** 2026-02-20
**Research agents used:** 7 (FastMCP patterns, security, testing, voice agent design, SDK analysis, packaging, performance)

### Key Improvements
1. **Voice agent optimization** — Latency budgets, numbered troubleshooting steps, tool annotations, tiered degradation, composite intake flow
2. **Security hardening** — OWASP MCP Top 10 mapping, voice prompt injection defense, context over-sharing prevention, `voice` tag refinement
3. **Testing strategy** — FastMCP `Client(server)` in-memory pattern with concrete fixtures, lifespan injection, tag filtering verification
4. **Performance patterns** — AttributeDescriptor caching in lifespan, connection pool tuning, progress reporting for multi-step ops
5. **Packaging best practices** — Conditional import guard, avoid upper version bounds on fastmcp, normalized extra names

### New Considerations Discovered
- OWASP published an MCP-specific Top 10 (2025) — 3 risks directly apply to this server
- FastMCP 3.0 supports `on_duplicate_tools="error"` for catching registration bugs
- SSE transport was deprecated June 2025 in favor of Streamable HTTP — update transport docs
- Voice latency budget: <800ms per tool call is acceptable, >1200ms feels broken to callers
- The `query_entities` allowlist is defense-in-depth against jailbroken voice agents querying sensitive entities
- `pytest-asyncio` with `asyncio_mode = "auto"` is required for MCP test fixtures

---

# ✨ Corrigo MCP Server

## Overview

Build an MCP (Model Context Protocol) server that wraps the Corrigo Python SDK, enabling any MCP-compatible AI client (Claude Code, Claude Desktop, Cursor, voice agents) to interact with the Corrigo Enterprise API. The server exposes the SDK's operations across the full MCP primitive surface: **tools** for mutations and listings, **resource templates** for reads, and **prompts** for common workflows.

**Primary use case:** A voice agent that lets callers report equipment issues, receive troubleshooting guidance over the phone, and — if unresolved — have a work order created automatically.

**Package:** Ships as `pip install corrigo[mcp]` — a subpackage (`corrigo.mcp`) in the existing repo, using FastMCP 3.0.

## Problem Statement

The Corrigo SDK provides a comprehensive Python API for facilities management, but AI clients cannot use it directly. An MCP server bridges this gap by exposing SDK operations as discoverable, typed, tagged primitives that any MCP client can invoke. The voice agent use case specifically requires:

1. Equipment lookup and identification (by name, customer, location)
2. Asset attribute retrieval for troubleshooting guidance
3. Work order creation when troubleshooting fails
4. Work order status checking and updates

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Framework** | FastMCP 3.0 | Pythonic decorators, all MCP primitives, tags, lifespan, stdio/SSE |
| **Location** | `src/corrigo/mcp/` subpackage | Keeps SDK and MCP server in lockstep |
| **Auth** | Environment variables only | Standard for MCP servers; no config file fallback |
| **Transport** | stdio default, Streamable HTTP available | stdio for local (Claude Code, Cursor), Streamable HTTP for remote/voice (SSE deprecated June 2025) |
| **Sync/async** | Mix: sync handlers + async for multi-step | FastMCP auto-threadpools sync `def`; async `def` with `to_thread()` for tools needing progress reporting |
| **Reads vs writes** | GET → resource templates, mutations → tools | Clean semantic split |
| **Customer-facing writes** | `create_work_order` + `update_work_order` | Voice agent needs to create WOs and add notes to existing ones |
| **Troubleshooting** | New `troubleshoot_equipment` prompt | Customer-safe variant; keeps `diagnose_work_order` as deep internal prompt |
| **ConcurrencyId** | Auto-fetch on update | `update_work_order` tool fetches current entity first, extracts ConcurrencyId, then applies update |
| **Query tool scoping** | Allowlist per audience tag | Customer-facing: `WorkOrder`, `Customer`, `Location` only |

## Technical Approach

### Architecture

```
┌─────────────────────────────────────────────────┐
│              MCP Client (Claude, Voice Agent)     │
└──────────────────────┬──────────────────────────┘
                       │ MCP Protocol (stdio / HTTP)
┌──────────────────────▼──────────────────────────┐
│              FastMCP 3.0 Server                   │
│  ┌─────────┐  ┌───────────┐  ┌────────────┐    │
│  │  Tools   │  │ Resources │  │  Prompts   │    │
│  │ (22)     │  │ (8)       │  │  (6)       │    │
│  └────┬─────┘  └─────┬─────┘  └─────┬──────┘    │
│       │              │              │            │
│  ┌────▼──────────────▼──────────────▼──────┐    │
│  │           Error Handler                  │    │
│  │    SDK Exception → ToolError mapping     │    │
│  └────────────────────┬────────────────────┘    │
│                       │                          │
│  ┌────────────────────▼────────────────────┐    │
│  │    Lifespan: CorrigoClient lifecycle     │    │
│  │    (init on startup, close on shutdown)  │    │
│  └────────────────────┬────────────────────┘    │
└───────────────────────┼─────────────────────────┘
                        │ httpx (sync, threadpooled)
┌───────────────────────▼─────────────────────────┐
│           Corrigo Enterprise REST API            │
└─────────────────────────────────────────────────┘
```

### Voice Agent Call Flow

```
Caller: "My walk-in cooler isn't working at store 1234"
  │
  ├─1. search_locations("walk-in cooler")           ← tool (read)
  │    or list assets via corrigo://customers/1234/assets  ← resource
  │
  ├─2. corrigo://locations/{id}/attributes           ← resource
  │    → Returns: Make, Model, Serial #, Last Service Date
  │
  ├─3. troubleshoot_equipment(equipment_id)          ← prompt
  │    → Returns: LLM messages with troubleshooting steps
  │    → "Check the compressor relay, verify thermostat setting..."
  │
  ├─4a. Issue resolved → Done
  │
  └─4b. Issue unresolved →
        create_work_order(customer_id, asset_id, ...)  ← tool (write)
        → "Work order WO-12345 created. A technician will be dispatched."
```

### File Structure

```
src/corrigo/mcp/
    __init__.py          # Public API: main(), mcp instance
    server.py            # FastMCP server setup, lifespan, error handler
    tools/
        __init__.py      # Registers all tool submodules
        work_orders.py   # WO lifecycle (10) + listing tools (5)
        entities.py      # Customer, contact, employee, location CRUD (5)
        queries.py       # Generic query tool + location search (2)
    resources/
        __init__.py      # Registers all resource submodules
        work_orders.py   # corrigo://work-orders/{id}, /number/{number}
        customers.py     # corrigo://customers/{id}, /{id}/assets
        locations.py     # corrigo://locations/{id}, /{id}/attributes
        employees.py     # corrigo://employees/{id}, corrigo://invoices/{id}
    prompts/
        __init__.py      # Registers all prompt submodules
        triage.py        # triage_work_order (internal)
        diagnose.py      # diagnose_work_order (internal)
        overview.py      # customer_overview (internal)
        status.py        # work_order_status (customer-facing)
        intake.py        # report_issue (customer-facing)
        troubleshoot.py  # troubleshoot_equipment (customer-facing) — NEW
```

### Implementation Phases

#### Phase 1: Foundation

Server setup, lifespan management, error handling, and a single "hello world" tool to validate the end-to-end flow.

**Tasks:**

- [x] Add `[project.optional-dependencies] mcp = ["fastmcp>=3.0.0"]` to `pyproject.toml`
- [x] Add `[project.scripts] corrigo-mcp = "corrigo.mcp:main"` entry point
- [x] Create `src/corrigo/mcp/__init__.py` with `main()` function
- [x] Create `src/corrigo/mcp/server.py`:
  - FastMCP instance with `mask_error_details=True`
  - Lifespan that validates env vars, creates `CorrigoClient`, yields it in context, closes on shutdown
  - Startup validation: check all 4 env vars present, attempt endpoint discovery to verify credentials
  - Error handler utility: maps SDK exceptions to `ToolError` with clear messages
- [x] Create a single test tool (e.g., `ping`) to validate stdio transport works
- [x] Add `src/corrigo/mcp/__main__.py` for `python -m corrigo.mcp` support

**Error mapping table (implemented in `server.py`):**

| SDK Exception | MCP Behavior | Message to Client |
|--------------|-------------|-------------------|
| `NotFoundError` | `ToolError` | "{entity_type} {id} not found" |
| `ValidationError` | `ToolError` | Validation details from `error.errors` |
| `RequiredFieldError` | `ToolError` | "Required field missing: {field}" |
| `ConcurrencyError` | `ToolError` | "Entity was modified. Retry the operation." |
| `AuthenticationError` | `ToolError` | "Authentication failed. Check CORRIGO_* env vars." |
| `AuthorizationError` | `ToolError` | "Permission denied for this operation." |
| `RateLimitError` | `ToolError` | "Rate limited. Retry after {n} seconds." |
| `ServerError` | `ToolError` | "Corrigo server error. Try again later." |
| `NetworkError` | `ToolError` | "Network error connecting to Corrigo API." |

**Lifespan pattern:**

```python
# src/corrigo/mcp/server.py
from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan

@lifespan
async def corrigo_lifespan(server):
    # Validate env vars
    client_id = os.environ.get("CORRIGO_CLIENT_ID")
    # ... validate all 4 required vars, raise clear error if missing

    client = CorrigoClient(client_id=client_id, ...)
    try:
        yield {"client": client}
    finally:
        client.close()

mcp = FastMCP(
    "Corrigo",
    lifespan=corrigo_lifespan,
    mask_error_details=True,
)
```

**Acceptance criteria:**
- [x] `corrigo-mcp` starts without error when env vars are set
- [x] `corrigo-mcp` fails fast with clear message when any env var is missing
- [x] `python -m corrigo.mcp` works as alternative entry point
- [x] Ping tool returns success via stdio
- [x] `CorrigoClient` is properly closed on server shutdown

**Tests:** `tests/mcp/test_server.py`
- Missing env var produces clear error
- Lifespan creates and closes client
- Error handler maps each SDK exception correctly

### Phase 1 Research Insights

**Best Practices (from FastMCP 3.0 docs):**
- Always use `try/finally` in lifespan — the docs explicitly require this for cleanup during abnormal shutdowns (SIGTERM, exceptions). The plan already does this correctly.
- Set `on_duplicate_tools="error"` (and equivalent for resources/prompts) on the FastMCP instance to catch registration bugs early in development.
- The lifespan context dict is shared across ALL requests and sessions — ideal for the `CorrigoClient` which is thread-safe via httpx's connection pool.

**Performance: Cache AttributeDescriptor in Lifespan:**
The `get_with_attributes()` method makes N+1 HTTP calls, one per attribute descriptor. Descriptors are reference data that rarely change. Cache them at startup:

```python
@lifespan
async def corrigo_lifespan(server):
    client = CorrigoClient(...)
    # Pre-cache attribute descriptors (reference data, changes rarely)
    descriptors = await asyncio.to_thread(
        lambda: client.query("AttributeDescriptor").select_all().limit(500).execute()
    )
    descriptor_map = {d["Id"]: d["DisplayAs"] for d in descriptors}
    try:
        yield {"client": client, "descriptor_cache": descriptor_map}
    finally:
        client.close()
```

This eliminates the per-descriptor HTTP calls in `get_with_attributes`, reducing 5-15 API calls per asset to 1.

**Conditional Import Guard (from packaging research):**
Since `fastmcp` is an optional dependency, the `__init__.py` should guard against missing install:

```python
# src/corrigo/mcp/__init__.py
try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "FastMCP is required for the MCP server. "
        "Install it with: pip install corrigo[mcp]"
    ) from None
```

**Packaging: Avoid Upper Version Bound:**
Use `fastmcp>=3.0.0` (not `>=3.0.0,<4.0.0`). Upper bounds cause more harm than good — they prevent users from getting compatible updates and create dependency conflicts. Only add upper bounds when you've confirmed incompatibility.

**Security: OWASP MCP Top 10 Mapping:**
Three risks from the [OWASP MCP Top 10](https://owasp.org/www-project-mcp-top-10/) directly apply:

| OWASP Risk | Applies To | Mitigation in Plan |
|---|---|---|
| **MCP01: Token Mismanagement** | Corrigo OAuth credentials in env vars | `mask_error_details=True` prevents credential leakage in errors; env vars only (no config files) |
| **MCP05: Command Injection** | `query_entities` accepts user-provided filters | Filters go through `QueryBuilder` which parameterizes values — no raw SQL/OData injection possible |
| **MCP10: Context Over-Sharing** | Customer-facing tools could expose internal data | Tag-based filtering + `query_entities` allowlist + `work_order_status` prompt strips costs/internal notes |

**Voice-Optimized Error Messages:**
The error mapping table should include voice-friendly alternatives. When the MCP server is deployed for voice, the ToolError messages are what the voice agent LLM reads. Consider including a `caller_message` field:

```python
def handle_sdk_error(e: CorrigoError) -> ToolError:
    if isinstance(e, NotFoundError):
        return ToolError(f"{e.entity_type} {e.entity_id} not found. "
                        f"Caller message: I wasn't able to find that. "
                        f"Could you double-check the information?")
```

**Testing Pattern (from FastMCP docs):**
Use the in-memory `Client(server)` pattern — no subprocess, no network:

```python
@pytest.fixture
async def mcp_client(mock_corrigo_client):
    from fastmcp.server.lifespan import lifespan

    @lifespan
    async def test_lifespan(server):
        yield {"client": mock_corrigo_client}

    test_server = FastMCP("Test", lifespan=test_lifespan, mask_error_details=True)
    # Register tools/resources/prompts on test_server...
    async with Client(test_server) as client:
        yield client
```

Add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` in `pyproject.toml` and add `pytest-asyncio` as a dev dependency.

---

#### Phase 2: Tools — Work Order Lifecycle & Listings

The core tool surface: 10 WO lifecycle tools + 5 listing tools.

**Work Order Lifecycle Tools (tagged: `work-orders`, `write`):**

All lifecycle tools are `internal`-only EXCEPT `create_work_order` and `update_work_order` which are also tagged `customer-facing`.

| Tool | SDK Method | Audience Tags | Handler Type | Valid Source States |
|------|-----------|---------------|-------------|-------------------|
| `create_work_order` | `work_orders.create()` | `internal`, `customer-facing` | sync | N/A (new entity) |
| `update_work_order` | auto-fetch + `work_orders.update()` | `internal`, `customer-facing` | async (to_thread) | Any active state |
| `assign_work_order` | `work_orders.assign()` | `internal` | sync | Open |
| `pickup_work_order` | `work_orders.pickup()` | `internal` | sync | Open (assigned) |
| `start_work_order` | `work_orders.start()` | `internal` | sync | Open, Paused |
| `complete_work_order` | `work_orders.complete()` | `internal` | sync | InProgress |
| `cancel_work_order` | `work_orders.cancel()` | `internal` | sync | Open, InProgress, Paused |
| `hold_work_order` | `work_orders.hold()` | `internal` | sync | Open, InProgress |
| `pause_work_order` | `work_orders.pause()` | `internal` | sync | InProgress |
| `reopen_work_order` | `work_orders.reopen()` | `internal` | sync | Completed, Cancelled |

**`update_work_order` auto-fetch pattern:**

```python
# tools/work_orders.py
@mcp.tool(tags={"work-orders", "write", "internal", "customer-facing"})
async def update_work_order(
    work_order_id: int,
    updates: dict,
    ctx: Context,
) -> dict:
    """Update fields on a work order. Automatically handles concurrency."""
    client = ctx.lifespan_context["client"]
    await ctx.info(f"Fetching current state of WO {work_order_id}...")
    current = await asyncio.to_thread(client.work_orders.get, work_order_id)
    concurrency_id = current.get("ConcurrencyId")
    updates["ConcurrencyId"] = concurrency_id
    await ctx.info("Applying updates...")
    result = await asyncio.to_thread(
        client.update, "WorkOrder", work_order_id, updates
    )
    return result
```

**Work Order Listing Tools (tagged: `work-orders`, `read`, `internal`, `customer-facing`):**

All listing tools share common parameters and are available to both audiences.

| Tool | Additional Params | Notes |
|------|------------------|-------|
| `list_work_orders` | — | All WOs with defaults |
| `list_work_orders_by_customer` | `customer_id: int` | Single customer |
| `list_work_orders_by_customers` | `customer_ids: list[int]` | Explicit group |
| `list_work_orders_by_brand` | `brand_prefix: str` | Two-step: resolve customers → query WOs |
| `list_work_orders_by_assignee` | `employee_id: int` | By assigned employee |

**Common listing parameters:**

```python
def list_work_orders(
    status: str = "Open",           # "Open", "InProgress", "Paused", "Completed", "Cancelled", "all"
    type_category: str | None = None,  # "Request", "PMRM", or None for all
    limit: int = 100,               # Max results (capped at 4000)
    offset: int = 0,                # Pagination offset
) -> dict:
    """Returns {"results": [...], "count": N, "has_more": bool}"""
```

**`list_work_orders_by_brand` is async (two SDK calls):**

```python
@mcp.tool(tags={"work-orders", "read", "internal", "customer-facing"})
async def list_work_orders_by_brand(
    brand_prefix: str,
    status: str = "Open",
    type_category: str | None = None,
    limit: int = 100,
    ctx: Context,
) -> dict:
    """List work orders for all customers matching a brand prefix (e.g., 'WEN' for Wendys)."""
    client = ctx.lifespan_context["client"]
    await ctx.info(f"Resolving customers for brand '{brand_prefix}'...")
    customers = await asyncio.to_thread(
        client.customers.list, limit=500, display_as__like=f"{brand_prefix} - %"
    )
    if not customers:
        raise ToolError(f"No customers found matching brand prefix '{brand_prefix}'")
    customer_ids = [c["Id"] for c in customers]
    await ctx.report_progress(1, 2)
    await ctx.info(f"Found {len(customer_ids)} customers. Querying work orders...")
    # ... query WOs by customer IDs
```

**Acceptance criteria:**
- [x] All 10 lifecycle tools callable via MCP and delegate to correct SDK methods
- [x] `create_work_order` tool description documents required params (`customer_id`, `asset_id`, `task_id`, `subtype_id`)
- [x] `update_work_order` auto-fetches ConcurrencyId before applying changes
- [x] All 5 listing tools return `{"results": [...], "count": N, "has_more": bool}`
- [x] `list_work_orders_by_brand` returns clear error when prefix matches 0 customers
- [x] `status="all"` skips the status filter
- [x] Lifecycle tools document valid source states in their docstrings
- [x] Invalid lifecycle transitions return clear ToolError (SDK's 400 is caught and clarified)

**Tests:** `tests/mcp/test_tools_work_orders.py`
- Each lifecycle tool calls correct SDK method with correct args
- `update_work_order` fetches then updates with ConcurrencyId
- Listing tools build correct query filters
- `has_more` is true when `len(results) == limit`
- Brand listing with 0 matches raises ToolError

### Phase 2 Research Insights

**Tool Annotations for Voice Agents:**
The MCP spec (2025-06-18) supports tool annotations that help voice agent orchestrators. Mark read-only listing tools so they can be called without confirmation prompts:

```python
@mcp.tool(
    tags={"work-orders", "read", "internal", "customer-facing"},
    annotations={"readOnlyHint": True, "openWorldHint": False},
)
def list_work_orders(...) -> dict:
```

Mark `create_work_order` and lifecycle tools as destructive so voice agents confirm before calling:

```python
@mcp.tool(
    tags={"work-orders", "write", "internal", "customer-facing"},
    annotations={"destructiveHint": True, "readOnlyHint": False},
)
def create_work_order(...) -> dict:
```

**Customer-Facing Response Optimization:**
For voice agents, listing tool responses should be concise. Consider returning only essential fields for customer-facing calls (WO number, status, equipment name, last update) rather than the full entity. The voice agent operates under a ~500-800ms response budget, and every extra field costs tokens and LLM processing time.

**Idempotency for Voice Retry Safety:**
Voice agents may retry tool calls due to network hiccups or misheard confirmations. `update_work_order` already handles this via ConcurrencyId. Consider an optional `idempotency_key` parameter on `create_work_order`:

```python
@mcp.tool(tags={"work-orders", "write", "internal", "customer-facing"})
def create_work_order(
    customer_id: int,
    asset_id: int,
    task_id: int,
    subtype_id: int,
    idempotency_key: str | None = None,  # Voice agent can pass caller session ID
    ...
) -> dict:
```

**Brand-to-Customer Cache:**
`list_work_orders_by_brand` makes two sequential API calls (resolve customers, then query WOs). In facilities management, the customer list is stable. Consider caching the brand→customer_ids mapping in the lifespan context and refreshing on a timer (or on first call with a 1-hour TTL).

**SDK Method Signatures (from codebase analysis):**
The SDK's `work_orders.create()` requires: `customer_id`, `asset_id`, `task_id`, `subtype_id`. Optional: `priority_id`, `contact_address`, `compute_assignment=False`, `compute_schedule=False`. All return `dict[str, Any]`. The SDK auto-converts snake_case kwargs to PascalCase, so `customer_id` becomes `CustomerId` in the API payload.

---

#### Phase 3: Tools — Entity CRUD & Queries

**Entity CRUD Tools (tagged: `write` + entity tag, `internal` only):**

| Tool | SDK Method | Tags |
|------|-----------|------|
| `create_customer` | `customers.create()` | `customers`, `write`, `internal` |
| `update_customer` | auto-fetch + `customers.update()` | `customers`, `write`, `internal` |
| `create_contact` | `contacts.create()` | `contacts`, `write`, `internal` |
| `create_employee` | `employees.create()` | `employees`, `write`, `internal` |
| `create_location` | `locations.create()` | `locations`, `write`, `internal` |

**Query & Search Tools (tagged: `read`):**

| Tool | SDK Method | Audience | Notes |
|------|-----------|----------|-------|
| `query_entities` | `QueryBuilder` | Both (allowlisted) | Customer-facing: `WorkOrder`, `Customer`, `Location` only |
| `search_locations` | `locations.search_by_name()` | Both | Partial name match |

**`query_entities` allowlist enforcement:**

```python
CUSTOMER_FACING_ENTITIES = {"WorkOrder", "Customer", "Location"}

@mcp.tool(tags={"queries", "read", "internal", "customer-facing"})
def query_entities(
    entity_type: str,
    filters: dict | None = None,
    limit: int = 100,
    offset: int = 0,
    order_by: str | None = None,
    descending: bool = False,
) -> dict:
    """Query any Corrigo entity type with filters.

    Entity types: WorkOrder, Customer, Location, Employee, Contact,
    WorkZone, Invoice, AssetAttribute, AttributeDescriptor, Task,
    WorkOrderType, WoPriority.

    Note: Customer-facing agents are restricted to WorkOrder, Customer, Location.
    """
```

> **Implementation note:** FastMCP 3.0 tag filtering happens at the server level (`include_tags`/`exclude_tags`), not per-tool. The allowlist is enforced in the tool body by checking which tags the current server was initialized with. If the server was started with `include_tags={"customer-facing"}`, the tool validates `entity_type in CUSTOMER_FACING_ENTITIES`.

**Acceptance criteria:**
- [x] `query_entities` builds correct `QueryBuilder` from filter dict
- [x] Customer-facing `query_entities` rejects entity types not in allowlist
- [x] `search_locations` performs partial name match via LIKE query
- [x] Entity CRUD tools delegate to correct SDK resource methods

**Tests:** `tests/mcp/test_tools_entities.py`, `tests/mcp/test_tools_queries.py`

### Phase 3 Research Insights

**Query Injection Defense (OWASP MCP05):**
The `query_entities` tool accepts user-provided `filters: dict`. This is safe because the SDK's `QueryBuilder` uses a structured condition model (not string interpolation). The filter dict maps to typed `where_*` calls:

```python
# Safe: QueryBuilder parameterizes all values
builder = client.query(entity_type)
for field, value in filters.items():
    builder = builder.where_equal(field, value)
```

No raw OData or SQL strings are passed through. However, add a validation check that `entity_type` is a known Corrigo entity type (not just the customer-facing allowlist, but the full set of valid types) to prevent information disclosure through error messages.

**Query Builder Capabilities (from SDK analysis):**
The SDK's `QueryBuilder` supports: `where_equal`, `where_not_equal`, `where_greater_than`, `where_less_than`, `where_like`, `where_in`, `where_between`, `where_is_null`, `where_contains`, plus `or_conditions()` for OR logic, `order_by()`, `limit()` (max 4000), `offset()`, and `distinct()`. The `query_entities` tool's `filters: dict` parameter should document which operators are available.

**Tag Filtering Verification Tests:**
Write explicit tests that verify tag filtering hides the right tools AND prevents calling hidden tools:

```python
async def test_customer_facing_hides_admin_tools():
    server = build_server(include_tags={"customer-facing"})
    async with Client(server) as client:
        tools = await client.list_tools()
        names = {t.name for t in tools}
        assert "create_employee" not in names  # internal-only
        assert "create_work_order" in names     # customer-facing

        # Hidden tools also can't be called
        with pytest.raises(Exception):
            await client.call_tool("create_employee", {...})
```

---

#### Phase 4: Resource Templates

Read-only data endpoints using URI templates. All resource handlers use sync `def` (simple single-call patterns).

**Resource Templates (tagged: `read` + entity tag):**

| Resource URI | SDK Method | Audience Tags |
|-------------|-----------|---------------|
| `corrigo://work-orders/{id}` | `work_orders.get(id)` | `internal`, `customer-facing` |
| `corrigo://work-orders/number/{number}` | `work_orders.get_by_number(number)` | `internal`, `customer-facing` |
| `corrigo://customers/{id}` | `customers.get(id)` | `internal`, `customer-facing` |
| `corrigo://customers/{id}/assets` | `locations.list_by_customer(id)` | `internal`, `customer-facing` |
| `corrigo://locations/{id}` | `locations.get(id)` | `internal`, `customer-facing` |
| `corrigo://locations/{id}/attributes` | `locations.get_with_attributes(id)` | `internal`, `customer-facing` |
| `corrigo://employees/{id}` | `employees.get(id)` | `internal` |
| `corrigo://invoices/{id}` | `invoices.get(id)` | `internal` |

**Resource handler pattern:**

```python
# resources/work_orders.py
import json
from fastmcp import Context

@mcp.resource("corrigo://work-orders/{id}", tags={"work-orders", "read", "internal", "customer-facing"})
def get_work_order(id: int, ctx: Context) -> str:
    """Get a work order by ID. Returns full work order details."""
    client = ctx.lifespan_context["client"]
    wo = client.work_orders.get(id)
    return json.dumps(wo, default=str)
```

**Note on `locations/{id}/attributes`:** This resource makes N+1 HTTP calls (one per attribute descriptor). Since it's sync, FastMCP runs it in a threadpool — this is fine. The N+1 is bounded by the number of attributes on a single asset (typically 5-15).

**Acceptance criteria:**
- [x] All 8 resource templates return valid JSON
- [x] Non-existent ID returns clear error (NotFoundError → resource error)
- [x] `corrigo://work-orders/number/{number}` handles the case where number is not found
- [x] `corrigo://customers/{id}/assets` returns list of all customer assets
- [x] `corrigo://locations/{id}/attributes` returns asset data with resolved attribute names
- [x] Employee and invoice resources are `internal`-only (not visible to customer-facing clients)

**Tests:** `tests/mcp/test_resources.py`

### Phase 4 Research Insights

**Resource Error Handling:**
Use `ResourceError` (not `ToolError`) for resource handler failures. Both are always visible to clients even with `mask_error_details=True`:

```python
from fastmcp.exceptions import ResourceError

@mcp.resource("corrigo://work-orders/{id}", tags={"work-orders", "read"})
def get_work_order(id: int, ctx: Context) -> str:
    client = ctx.lifespan_context["client"]
    try:
        wo = client.work_orders.get(id)
    except NotFoundError:
        raise ResourceError(f"Work order {id} not found")
    return json.dumps(wo, default=str)
```

**N+1 Mitigation for `locations/{id}/attributes`:**
With the descriptor cache from the lifespan (Phase 1 insight), the `get_with_attributes` resource handler can avoid per-descriptor HTTP calls. Pass the cache to the SDK method or post-process the result:

```python
@mcp.resource("corrigo://locations/{id}/attributes", tags={"locations", "read"})
def get_location_attributes(id: int, ctx: Context) -> str:
    client = ctx.lifespan_context["client"]
    descriptor_cache = ctx.lifespan_context["descriptor_cache"]
    location = client.locations.get(id)
    # Fetch raw attribute values (1 API call) and resolve names via cache
    attrs = client.locations._get_raw_attributes(id)  # hypothetical
    resolved = {descriptor_cache.get(a["DescriptorId"], "Unknown"): a["Value"] for a in attrs}
    location["attributes"] = resolved
    return json.dumps(location, default=str)
```

If the SDK doesn't expose raw attribute access, the existing `get_with_attributes` still works — the descriptor cache just prevents the redundant descriptor name lookups.

**Resource Template Testing Pattern:**

```python
async def test_work_order_resource(mcp_client, mock_corrigo_client):
    mock_corrigo_client.work_orders.get.return_value = {"Id": 42, "Number": "WO-001"}
    content = await mcp_client.read_resource("corrigo://work-orders/42")
    data = json.loads(content[0].text)
    assert data["Number"] == "WO-001"

async def test_work_order_not_found(mcp_client, mock_corrigo_client):
    mock_corrigo_client.work_orders.get.side_effect = NotFoundError("WorkOrder", 999)
    with pytest.raises(Exception, match="not found"):
        await mcp_client.read_resource("corrigo://work-orders/999")
```

---

#### Phase 5: Prompts

Reusable message templates that fetch context and compose structured LLM messages. All prompts use `async def` with `to_thread()` since they make multiple SDK calls and benefit from progress reporting.

**Prompts:**

| Prompt | Tags | Audience | Parameters |
|--------|------|----------|-----------|
| `triage_work_order` | `internal`, `work-orders` | Ops/dispatch | `work_order_id: int` |
| `diagnose_work_order` | `internal`, `work-orders` | Technicians/ops | `work_order_id: int` |
| `customer_overview` | `internal`, `customers` | Account managers | `customer_id: int` |
| `work_order_status` | `customer-facing`, `work-orders` | Call center/voice | `work_order_id: int` |
| `report_issue` | `customer-facing`, `work-orders` | Call center/voice | `customer_id: int`, `description: str` |
| `troubleshoot_equipment` | `customer-facing`, `locations` | Voice agent | `equipment_id: int` |

**`troubleshoot_equipment` prompt (NEW — voice agent primary flow):**

```python
# prompts/troubleshoot.py
@mcp.prompt(tags={"customer-facing", "locations"})
async def troubleshoot_equipment(equipment_id: int, ctx: Context) -> list[Message]:
    """Guide troubleshooting for a specific piece of equipment.

    Fetches equipment details and attributes (make, model, type) to provide
    targeted troubleshooting steps. Used by voice agents during customer calls.
    """
    client = ctx.lifespan_context["client"]
    await ctx.info(f"Fetching equipment {equipment_id} with attributes...")

    equipment = await asyncio.to_thread(
        client.locations.get_with_attributes, equipment_id
    )

    return [
        Message(role="user", content=f"""A customer is calling about a problem with this equipment:

Equipment: {equipment.get('Name', 'Unknown')}
Type: {equipment.get('TypeId', 'Unknown')}
Location: {equipment.get('ParentName', 'Unknown')}
Attributes: {json.dumps(equipment.get('attributes', {}), indent=2)}

Provide step-by-step troubleshooting guidance appropriate for a non-technical caller.
Focus on simple checks they can perform (power, settings, visual inspection).
If the issue cannot be resolved, recommend creating a work order."""),
    ]
```

**`report_issue` prompt design decision:**

Returns structured natural language with a final assistant message suggesting the `create_work_order` tool call with pre-filled parameters. Does NOT auto-call the tool — the LLM decides.

```python
@mcp.prompt(tags={"customer-facing", "work-orders"})
async def report_issue(customer_id: int, description: str, ctx: Context) -> list[Message]:
    """Guide intake of a new service request from a customer.

    Fetches customer details and assets to help identify the right equipment
    and collect information needed for work order creation.
    """
    client = ctx.lifespan_context["client"]

    await ctx.info("Fetching customer and assets...")
    customer = await asyncio.to_thread(client.customers.get, customer_id)
    assets = await asyncio.to_thread(client.locations.list_by_customer, customer_id)

    equipment = [a for a in assets if a.get("TypeId") == "Equipment"]

    return [
        Message(role="user", content=f"""A customer is reporting an issue.

Customer: {customer.get('DisplayAs', 'Unknown')} (ID: {customer_id})
Issue: {description}

Equipment at this location:
{json.dumps([{'id': e['Id'], 'name': e['Name']} for e in equipment], indent=2)}

Help identify which equipment is affected, confirm the issue details,
and if a work order is needed, call the create_work_order tool with:
- customer_id: {customer_id}
- asset_id: [the identified equipment ID]
- task_id: [appropriate task ID]
- subtype_id: [appropriate subtype ID]"""),
    ]
```

**Partial failure handling:** Prompts return available data with a note about what failed. If a sub-fetch fails, catch the exception and include `"[Could not load {component}: {error}]"` in the message. The prompt never fails entirely due to a single sub-fetch failure.

**Acceptance criteria:**
- [x] All 6 prompts return well-structured `list[Message]`
- [x] `troubleshoot_equipment` includes equipment attributes in the context
- [x] `report_issue` lists available equipment for the customer and suggests `create_work_order` params
- [x] Partial fetch failures produce degraded but useful prompt output (not a crash)
- [x] `work_order_status` returns only customer-safe information (no internal notes, no cost data)
- [x] `diagnose_work_order` includes full technical context (attributes, history, customer)
- [ ] Internal prompts not visible when server uses `include_tags={"customer-facing"}` (deferred — tag filtering is a runtime feature)

**Tests:** `tests/mcp/test_prompts.py`
- Each prompt returns correct message structure
- Partial failure includes error note but doesn't crash
- Customer-facing prompts exclude sensitive data

### Phase 5 Research Insights

**Voice-Optimized Troubleshooting Prompt:**
Research from production voice agents shows that spoken responses longer than ~30 seconds lose the caller. Structure troubleshooting as numbered steps, not paragraphs. Refine the `troubleshoot_equipment` prompt:

```python
return [
    Message(role="user", content=f"""A customer is calling about a problem with this equipment:

Equipment: {equipment.get('Name', 'Unknown')}
Type: {equipment.get('TypeId', 'Unknown')}
Location: {equipment.get('ParentName', 'Unknown')}
Attributes: {json.dumps(equipment.get('attributes', {}), indent=2)}

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
Then call the create_work_order tool."""),
]
```

**Tiered Graceful Degradation:**
When sub-fetches fail in prompts, degrade through tiers rather than returning a generic error:

```
Level 1: Full context (equipment + attributes + service history)
Level 2: Equipment + attributes (service history unavailable)
Level 3: Equipment only (attributes fetch failed)
Level 4: Generic troubleshooting from caller description (equipment not found)
```

At each level the prompt still produces useful guidance, just less specific. A walk-in cooler with no attributes can still get generic cooler troubleshooting.

**Never Return Empty Results Silently:**
If `search_locations` returns zero results in a voice context, the tool response must include a suggestion: "No equipment found matching that description. Try searching by store number or address instead." The voice agent needs something to say to the caller.

**Latency Considerations for Prompts:**
The `troubleshoot_equipment` prompt makes N+1 calls via `get_with_attributes`. With the descriptor cache (Phase 1 insight), this drops from 5-15 API calls to 1. Voice latency budget:

| Threshold | User Perception |
|---|---|
| < 500ms | Natural, indistinguishable from human |
| 500-800ms | Acceptable, feels like a thoughtful pause |
| 800-1200ms | Noticeable delay, still tolerable |
| > 1200ms | Feels broken, caller starts saying "hello?" |

The voice agent should use `ctx.info()` messages as filler: "Let me look that up for you..." gives the TTS a natural pause while the backend processes.

**Prompt Testing Pattern:**

```python
async def test_troubleshoot_equipment(mcp_client, mock_corrigo_client):
    mock_corrigo_client.locations.get_with_attributes.return_value = {
        "Name": "Walk-in Cooler",
        "TypeId": "Equipment",
        "ParentName": "Store 1234",
        "attributes": {"Model #": "XYZ-100", "Serial #": "SN-999"},
    }
    result = await mcp_client.get_prompt(
        "troubleshoot_equipment", arguments={"equipment_id": 42}
    )
    assert len(result.messages) == 1
    content = result.messages[0].content.text
    assert "Walk-in Cooler" in content
    assert "XYZ-100" in content

async def test_troubleshoot_partial_failure(mcp_client, mock_corrigo_client):
    """Attributes fail but prompt still works with equipment data only."""
    mock_corrigo_client.locations.get_with_attributes.side_effect = NetworkError()
    mock_corrigo_client.locations.get.return_value = {"Name": "Walk-in Cooler"}
    result = await mcp_client.get_prompt(
        "troubleshoot_equipment", arguments={"equipment_id": 42}
    )
    content = result.messages[0].content.text
    assert "Walk-in Cooler" in content
    assert "Could not load" in content  # degradation note
```

**Voice Prompt Injection Defense (OWASP MCP10):**
The TEAPOT methodology (Transcription analysis, Exploration, Attack surface mapping, Prompt injection, Output evaluation, Tool/function abuse) identifies voice-specific injection risks. A caller could use conversational manipulation to make the voice agent:
- Query entities outside the allowlist
- Create work orders for other customers
- Extract internal system information

Mitigations already in the plan: tag filtering, `query_entities` allowlist, `mask_error_details=True`. Additional consideration: the `report_issue` prompt includes `customer_id` as a parameter — ensure the voice agent validates caller identity before passing this value.

---

#### Phase 6: Packaging, CLI & Documentation

**Tasks:**

- [x] Update `pyproject.toml`:
  - Add `mcp = ["fastmcp>=3.0.0"]` optional dependency
  - Add `corrigo-mcp = "corrigo.mcp:main"` script entry point
- [x] Create `src/corrigo/mcp/__main__.py` for `python -m corrigo.mcp`
- [ ] Add MCP server section to `README.md` (installation, env vars, running, Claude Desktop config example)
- [ ] Add Claude Desktop `claude_desktop_config.json` example:

```json
{
  "mcpServers": {
    "corrigo": {
      "command": "corrigo-mcp",
      "env": {
        "CORRIGO_CLIENT_ID": "your_client_id",
        "CORRIGO_CLIENT_SECRET": "your_client_secret",
        "CORRIGO_COMPANY_NAME": "YourCompany",
        "CORRIGO_REGION": "AM"
      }
    }
  }
}
```

- [ ] Add Claude Code `~/.claude/mcp.json` example
- [ ] Document tag-based filtering for audience separation:

```bash
# Full access (internal ops)
corrigo-mcp

# Customer-facing only (voice agent, call center)
CORRIGO_MCP_TAGS=customer-facing corrigo-mcp
```

**Acceptance criteria:**
- [x] `pip install corrigo[mcp]` installs fastmcp dependency
- [x] `corrigo-mcp` starts the server via stdio
- [x] `python -m corrigo.mcp` works as alternative
- [ ] README documents all env vars, installation, and client config examples
- [x] Quality gates pass: `uv run pytest`, `uv run ruff check src/ tests/`, `uv run mypy src/`

### Phase 6 Research Insights

**Transport Update — SSE Deprecated:**
The SSE transport was deprecated in the MCP spec (2025-06-18) in favor of **Streamable HTTP**. Update documentation to reflect:

```bash
# Full access (internal ops, stdio for local)
corrigo-mcp

# Customer-facing only (Streamable HTTP for voice agent)
CORRIGO_MCP_TAGS=customer-facing corrigo-mcp --transport streamable-http --port 8000
```

**Entry Point with Conditional Import:**
The `corrigo-mcp` script entry point will fail with an opaque error if `fastmcp` isn't installed. Add a guard in `__init__.py`:

```python
# src/corrigo/mcp/__init__.py
try:
    from corrigo.mcp.server import mcp
except ImportError:
    raise ImportError(
        "The MCP server requires FastMCP. Install with: pip install corrigo[mcp]"
    ) from None

def main():
    mcp.run()
```

**`__main__.py` Pattern:**
Keep it minimal — no `if __name__ == '__main__'` guard needed:

```python
# src/corrigo/mcp/__main__.py
from corrigo.mcp import main
main()
```

**Voice Agent Integration Paths (from research):**
Document these MCP-compatible voice platforms in the README:

| Platform | Integration Method | Notes |
|---|---|---|
| **OpenAI Realtime API** | Built-in MCP support (Aug 2025) | Streaming tool results mid-conversation |
| **Retell AI** | MCP Node connector | Drop-in, no custom code needed |
| **Vapi** | Native MCP client | Dynamic tool discovery |
| **LiveKit Agents** | voice-mcp-agent framework | Open-source reference impl |

**Dev Dependencies for MCP Testing:**
Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"

[project.optional-dependencies]
dev = [
    # ... existing dev deps ...
    "pytest-asyncio>=0.23.0",
]
```

---

## Alternative Approaches Considered

| Approach | Why Rejected |
|----------|-------------|
| **Separate repo** | Would drift from SDK changes; harder to keep in sync |
| **Full async HTTP client** | Significant SDK rewrite for v1 MCP server; threadpool is sufficient |
| **One tool per entity query** | Would create ~15 tools for reads alone; single `query_entities` tool is more manageable |
| **Re-tag `diagnose_work_order` as customer-facing** | Exposes full technical context (costs, internal notes) to voice agents; separate `troubleshoot_equipment` is safer |
| **Config file auth fallback** | Non-standard for MCP servers; env vars are the convention |

## Acceptance Criteria

### Functional Requirements

- [x] 22 tools callable via MCP protocol (10 WO lifecycle + 5 WO listing + 5 entity CRUD + 2 query/search)
- [x] 8 resource templates return entity data via URI patterns
- [x] 6 prompts return structured LLM messages
- [x] Tag-based filtering correctly separates `internal` vs `customer-facing` surfaces
- [x] Voice agent flow works end-to-end: search → troubleshoot → create WO

### Non-Functional Requirements

- [x] Startup fails fast with clear error on missing env vars
- [x] All SDK exceptions mapped to clear `ToolError` messages
- [x] Sync tools do not block the event loop (FastMCP auto-threadpool)
- [x] Server shuts down cleanly (CorrigoClient closed)
- [x] `mask_error_details=True` prevents internal stack traces leaking to clients

### Quality Gates

- [x] Test coverage for all tools, resources, and prompts (mocked SDK calls)
- [x] `uv run ruff check src/ tests/` passes
- [x] `uv run mypy src/` passes (strict mode)
- [x] `uv run pytest` passes

## Dependencies & Prerequisites

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `fastmcp` | >=3.0.0 | MCP server framework |
| `corrigo` SDK | 0.1.0 (this repo) | All API operations |
| Python | >=3.9 | Matches existing SDK requirement |

**New dev dependency required:** `pytest-asyncio>=0.23.0` for async MCP test fixtures with `asyncio_mode = "auto"`.

## Risk Analysis & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| FastMCP 3.0 API changes | Server breakage on updates | Pin to `>=3.0.0` (no upper bound per packaging best practice); monitor changelog |
| Sync SDK blocks threadpool under load | Slow concurrent tool calls in Streamable HTTP mode | Acceptable for v1; tune thread pool (`anyio.to_thread.current_default_thread_limiter().total_tokens = 40`); async HTTP client is future optimization |
| `get_with_attributes` makes N+1 calls | Slow `troubleshoot_equipment` prompt (1-3s) | Cache `AttributeDescriptor` entities in lifespan context to eliminate per-descriptor calls |
| Brand prefix matching is convention-dependent | False positives/missed matches | Document convention clearly; tool returns matched customer count for transparency |
| `create_work_order` requires opaque IDs (task_id, subtype_id) | AI client can't self-serve valid values | `query_entities` can query `Task`, `WorkOrderType`, `WoPriority` entities; document this in tool description |
| Voice prompt injection (OWASP MCP10) | Caller manipulates voice agent into unauthorized actions | Tag filtering + `query_entities` allowlist + `mask_error_details=True`; caller identity validation before `report_issue` |
| Context over-sharing between sessions | Sensitive data leakage between callers | FastMCP lifespan context is shared (read-only client), but no per-session state is stored; each tool call is stateless |
| Voice latency >1200ms | Caller abandonment ("hello?") | Descriptor cache, brand-customer cache, `ctx.info()` filler messages, consider composite intake tool |

## Future Considerations

- **Async HTTP client**: If Streamable HTTP deployments show concurrency bottlenecks, build `AsyncCorrigoHTTPClient`
- **Reference/lookup resources**: Add `corrigo://reference/tasks`, `corrigo://reference/priorities` for ID discovery
- **Remaining lifecycle tools**: `flag`, `send`, `verify` can be added as internal-only tools when needed
- **Rate limiting at MCP layer**: Add request counting/throttling if abuse patterns emerge (OWASP MCP02: Privilege Escalation)
- **Audit logging**: Structured logging to stderr for all write operations (tool name, entity ID, user context) — addresses OWASP MCP08: Lack of Audit and Telemetry
- **Portfolio support**: If Corrigo adds API support for portfolio-based filtering, expose as grouping mechanism
- **Composite intake tool**: Combine search + attribute fetch in one tool call to cut an LLM reasoning cycle from the voice agent critical path (reduces 4 round-trips to 3)
- **`voice` tag**: Add as a subset of `customer-facing` for further surface restriction (e.g., hide file-upload tools from voice but expose to web portal)
- **ResponseCachingMiddleware**: FastMCP 3.0 provides built-in TTL-based caching middleware for tools/resources/prompts — evaluate for production Streamable HTTP deployments
- **Server composition**: Use FastMCP `mount()` to split domain modules (work orders, customers, locations) into sub-servers with namespacing if the tool count grows beyond 30

## References & Research

### Internal References

- Brainstorm: `docs/brainstorms/2026-02-20-corrigo-mcp-server-brainstorm.md`
- SDK client: `src/corrigo/client.py` — CorrigoClient facade
- Commands: `src/corrigo/api/commands.py` — All WO lifecycle commands
- Query builder: `src/corrigo/api/query.py` — QueryBuilder + QueryExecutor
- Work orders: `src/corrigo/api/resources/work_orders.py` — WO resource with all lifecycle methods
- Locations: `src/corrigo/api/resources/locations.py` — Asset tree, attributes, search
- Exceptions: `src/corrigo/exceptions.py` — Full exception hierarchy
- Bug fix plan: `docs/plans/2026-02-20-fix-sdk-live-testing-bugs-plan.md` — Error handling patterns

### External References

- FastMCP 3.0 docs: https://gofastmcp.com/getting-started/welcome
- FastMCP GitHub: https://github.com/jlowin/fastmcp
- MCP specification: https://modelcontextprotocol.io
- MCP spec (2025-06-18): https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- FastMCP tools: https://gofastmcp.com/servers/tools
- FastMCP resources: https://gofastmcp.com/servers/resources
- FastMCP prompts: https://gofastmcp.com/servers/prompts
- FastMCP lifespan: https://gofastmcp.com/servers/lifespan
- FastMCP composition: https://gofastmcp.com/servers/composition
- FastMCP tags/visibility: https://gofastmcp.com/servers/visibility
- FastMCP client (testing): https://gofastmcp.com/clients/client
- FastMCP testing patterns: https://gofastmcp.com/patterns/testing

### Security References (from deepening research)

- OWASP MCP Top 10: https://owasp.org/www-project-mcp-top-10/
- TEAPOT voice AI prompt injection methodology: https://www.redcaller.com/docs/methodologies/teapot-methodology
- Voice AI compliance & security: https://hamming.ai/blog/ai-voice-agent-compliance-and-security

### Voice Agent References (from deepening research)

- OpenAI MCP-powered voice agent cookbook: https://cookbook.openai.com/examples/partners/mcp_powered_voice_agents/mcp_powered_agents_cookbook
- Voice AI latency benchmarks: https://www.trillet.ai/blogs/voice-ai-latency-benchmarks
- Sierra voice latency engineering: https://sierra.ai/blog/voice-latency
- Retell AI MCP connector: https://www.retellai.com/blog/connect-any-ai-voice-agent-to-mcp-with-retell-ai-mcp-node
- Vapi MCP client: https://vapi.ai/blog/introducing-vapi-mcp-client
- LiveKit voice-mcp-agent: https://github.com/den-vasyliev/voice-mcp-agent

### Testing References (from deepening research)

- FastMCP testing blog: https://www.jlowin.dev/blog/stop-vibe-testing-mcp-servers
- MCPcat unit testing guide: https://mcpcat.io/guides/writing-unit-tests-mcp-servers/
- MCPcat integration testing: https://mcpcat.io/guides/integration-tests-mcp-flows/

### Production Data (from brainstorm research)

- Work order types: `Request` (80%), `PMRM` (20%), `Basic` (legacy), `Turn` (unused)
- Valid statuses: `Open`, `InProgress`, `Paused`, `Completed`, `Cancelled`
- Portfolio filtering is broken in REST API (silently ignored) — use brand prefix convention instead
- 100 portfolios exist but are UI-only grouping; not usable for API queries
