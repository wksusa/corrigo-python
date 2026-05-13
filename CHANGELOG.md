# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.5.0] - 2026-05-13

### Added

- `WorkOrderResource.list_on_hold(reason_id=None, limit=4000)` — lists OnHold
  work orders with `LastAction.Reason.*` populated, so callers can read the
  current hold reason without walking `ActionLogRecords`. Optionally filters
  by `LastAction.Reason.Id` client-side (Corrigo's Query API does not accept
  it as a server-side filter target). Reason IDs are tenant-configured —
  inspect a known example's `LastAction.Reason` to discover them.

## [0.4.0] - 2026-05-08

### Changed (breaking)

- `WorkOrderResource.cancel` and `CommandExecutor.cancel_work_order` now take a
  required `action_reason_id: int` parameter instead of `reason: str | None`.
  The previous free-text `Reason` body was rejected by Corrigo
  (`BUSINESS_LOGIC_ERROR: "status Cancelled requires reason"`) on tenants
  configured to require a reason — including WKS production and staging — so
  the prior signature did not work in practice. The CLI flag is now
  `--action-reason-id / -r`. Reason IDs are tenant-configured and not exposed
  via the Query API; obtain them from the Corrigo admin UI or by inspecting
  `WoActionLog` rows with `TypeId = "Cancel"`.

## [0.3.0] - 2026-02-25

### Fixed

- `WorkOrderResource.get_by_number` now zero-pads short numeric inputs to 9
  digits before querying. Callers (e.g. voice agents) often drop the leading
  zero when reading a work order number aloud — `"72460001"` now resolves to
  `"072460001"` correctly.

## [0.1.0] - 2026-02-20

### Added

- OAuth 2.0 authentication with automatic token management and refresh
- Regional support for Americas, APAC, and EMEA endpoints
- Dynamic endpoint discovery per tenant
- Fluent `QueryBuilder` for building complex Corrigo queries
- Work order lifecycle commands (create, assign, start, complete, cancel, hold, reopen)
- Resource classes for work orders, customers, locations, contacts, employees, work zones, and invoices
- Equipment attribute lookups (make, model, serial number)
- `list_by_customer` for retrieving all assets for a store
- Full-featured CLI with `corrigo` command
  - Work order, customer, and location management
  - Multiple output formats (table, JSON, text)
  - Profile-based configuration with `~/.corrigo/config.yaml`
  - Connection debugging via `corrigo debug`
- CLI dependencies made optional via `pip install corrigo[cli]`
- Comprehensive exception hierarchy (`CorrigoError`, `AuthenticationError`, `NotFoundError`, etc.)
- Full type annotations with strict mypy checking
- Test suite with pytest, pytest-asyncio, and respx for HTTP mocking
- MkDocs documentation site with Material theme

[0.1.0]: https://github.com/wksusa/corrigo-python/releases/tag/v0.1.0
