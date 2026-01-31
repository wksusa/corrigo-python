"""Output formatting for Corrigo CLI."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


class OutputFormat(str, Enum):
    """Supported output formats."""

    JSON = "json"
    TABLE = "table"
    TEXT = "text"


def format_output(
    data: dict[str, Any] | list[dict[str, Any]],
    format: OutputFormat = OutputFormat.TABLE,
    columns: list[str] | None = None,
    title: str | None = None,
) -> None:
    """
    Format and print output in the specified format.

    Args:
        data: Single dict or list of dicts to output.
        format: Output format (json, table, text).
        columns: Columns to display (for table/text). If None, auto-detect from data.
        title: Table title (for table format).
    """
    if format == OutputFormat.JSON:
        _output_json(data)
    elif format == OutputFormat.TABLE:
        _output_table(data, columns, title)
    else:
        _output_text(data, columns)


def _output_json(data: dict[str, Any] | list[dict[str, Any]]) -> None:
    """Output data as formatted JSON."""
    console.print_json(json.dumps(data, indent=2, default=str))


def _output_table(
    data: dict[str, Any] | list[dict[str, Any]],
    columns: list[str] | None = None,
    title: str | None = None,
) -> None:
    """Output data as a Rich table."""
    # Handle single record as vertical key-value display
    if isinstance(data, dict):
        _output_single_record(data, title)
        return

    if not data:
        console.print("[yellow]No results[/yellow]")
        return

    # For single item in list, also use vertical display
    if len(data) == 1:
        _output_single_record(data[0], title)
        return

    if columns is None:
        columns = _detect_columns(data)

    table = Table(title=title)
    for col in columns:
        table.add_column(_format_column_header(col), style="cyan" if col == "Id" else None)

    for row in data:
        values = [_format_value(row.get(col)) for col in columns]
        table.add_row(*values)

    console.print(table)


def _output_single_record(data: dict[str, Any], title: str | None = None) -> None:
    """Output a single record as a vertical key-value table."""
    table = Table(title=title, show_header=False, box=None)
    table.add_column("Field", style="cyan", width=25)
    table.add_column("Value", style="white")

    # Prioritize important fields first
    priority_keys = ["Id", "Number", "Name", "DisplayName", "StatusId", "TypeCategory", "Type"]
    seen = set()

    for key in priority_keys:
        if key in data:
            table.add_row(_format_column_header(key), _format_value(data[key]))
            seen.add(key)

    # Add remaining fields
    for key, value in sorted(data.items()):
        if key not in seen:
            table.add_row(_format_column_header(key), _format_value(value))

    console.print(table)


def _output_text(
    data: dict[str, Any] | list[dict[str, Any]],
    columns: list[str] | None = None,
) -> None:
    """Output data as simple text."""
    if isinstance(data, dict):
        data = [data]

    if not data:
        console.print("No results")
        return

    if columns is None:
        columns = _detect_columns(data)

    for row in data:
        values = [f"{col}={_format_value(row.get(col))}" for col in columns]
        console.print("  ".join(values))


def _detect_columns(data: list[dict[str, Any]]) -> list[str]:
    """Auto-detect columns from data, prioritizing common fields."""
    if not data:
        return []

    all_keys = set()
    for row in data:
        all_keys.update(row.keys())

    priority_keys = ["Id", "Number", "Name", "DisplayName", "Status", "StatusId", "Type", "TypeId"]
    columns = [k for k in priority_keys if k in all_keys]
    remaining = sorted(k for k in all_keys if k not in columns)
    return columns + remaining


def _format_column_header(key: str) -> str:
    """Format a column header from a key name."""
    import re

    words = re.sub(r"([a-z])([A-Z])", r"\1 \2", key)
    return words.replace("_", " ").title()


def _format_value(value: Any) -> str:
    """Format a value for display."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, dict):
        if "Id" in value and len(value) <= 3:
            if "Name" in value:
                return f"{value['Name']} ({value['Id']})"
            elif "DisplayName" in value:
                return f"{value['DisplayName']} ({value['Id']})"
            return str(value["Id"])
        return json.dumps(value)
    if isinstance(value, list):
        if len(value) == 0:
            return ""
        if len(value) <= 3 and all(isinstance(v, (str, int, float)) for v in value):
            return ", ".join(str(v) for v in value)
        return f"[{len(value)} items]"
    return str(value)


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]Error: {message}[/red]")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]{message}[/green]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]{message}[/yellow]")


def print_detail(label: str, value: Any) -> None:
    """Print a labeled detail."""
    console.print(f"[cyan]{label}:[/cyan] {_format_value(value)}")
