"""Corrigo MCP Server — exposes the Corrigo SDK via Model Context Protocol."""

try:
    from corrigo.mcp.server import mcp
except ImportError:
    raise ImportError(
        "The MCP server requires FastMCP. Install with: pip install corrigo[mcp]"
    ) from None

__all__ = ["main", "mcp"]


def main() -> None:
    """Entry point for the corrigo-mcp CLI command."""
    mcp.run()
