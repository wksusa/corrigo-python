# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
