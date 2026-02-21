"""Tool registrations for the Corrigo MCP server.

Importing this module registers all tools on the server via side effects.
"""

from corrigo.mcp.tools import entities as _entities  # noqa: F401
from corrigo.mcp.tools import queries as _queries  # noqa: F401
from corrigo.mcp.tools import work_orders as _work_orders  # noqa: F401
