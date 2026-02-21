"""Prompt registrations for the Corrigo MCP server.

Importing this module registers all prompts on the server via side effects.
"""

from corrigo.mcp.prompts import diagnose as _diagnose  # noqa: F401
from corrigo.mcp.prompts import intake as _intake  # noqa: F401
from corrigo.mcp.prompts import overview as _overview  # noqa: F401
from corrigo.mcp.prompts import status as _status  # noqa: F401
from corrigo.mcp.prompts import triage as _triage  # noqa: F401
from corrigo.mcp.prompts import troubleshoot as _troubleshoot  # noqa: F401
