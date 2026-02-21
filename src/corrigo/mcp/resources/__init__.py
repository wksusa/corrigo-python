"""Resource template registrations for the Corrigo MCP server.

Importing this module registers all resource templates on the server via side effects.
"""

from corrigo.mcp.resources import customers as _customers  # noqa: F401
from corrigo.mcp.resources import employees as _employees  # noqa: F401
from corrigo.mcp.resources import locations as _locations  # noqa: F401
from corrigo.mcp.resources import work_orders as _work_orders  # noqa: F401
