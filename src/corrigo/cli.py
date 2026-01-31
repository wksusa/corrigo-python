"""Corrigo CLI - Command-line interface for Corrigo Enterprise API."""

from __future__ import annotations

import sys
from typing import Any, Optional

try:
    import typer
    from rich.console import Console
    from rich.table import Table
except ImportError:
    def main() -> None:
        """Entry point that handles missing CLI dependencies."""
        print("Error: CLI dependencies not installed.", file=sys.stderr)
        print("Install with: pip install corrigo-sdk[cli]", file=sys.stderr)
        sys.exit(1)
    # Allow module to be imported without CLI deps for type checking
    raise SystemExit(
        "CLI dependencies not installed. Install with: pip install corrigo-sdk[cli]"
    )

from corrigo.client import CorrigoClient
from corrigo.config import Config, get_credentials, validate_credentials
from corrigo.output import OutputFormat, format_output, print_error, print_success, print_detail

app = typer.Typer(
    name="corrigo",
    help="Command-line interface for Corrigo Enterprise API",
    no_args_is_help=True,
)
console = Console()


def main() -> int:
    """CLI entry point."""
    try:
        app()
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0


def get_client(profile: str | None = None) -> CorrigoClient:
    """Create a CorrigoClient from config credentials."""
    creds = get_credentials(profile)
    missing = validate_credentials(creds)
    if missing:
        print_error(f"Missing required configuration: {', '.join(missing)}")
        print_error("Run 'corrigo config show' to see current status.")
        raise typer.Exit(1)

    return CorrigoClient(
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        company_name=creds["company_name"],
        region=creds.get("region", "AM"),
    )

# Subcommand groups
config_app = typer.Typer(help="Configuration management")
work_orders_app = typer.Typer(help="Work order operations")
customers_app = typer.Typer(help="Customer operations")
locations_app = typer.Typer(help="Location operations")
contacts_app = typer.Typer(help="Contact operations")
employees_app = typer.Typer(help="Employee operations")
work_zones_app = typer.Typer(help="Work zone operations")
invoices_app = typer.Typer(help="Invoice operations")

# Register subcommands
app.add_typer(config_app, name="config")
app.add_typer(work_orders_app, name="work-orders")
app.add_typer(customers_app, name="customers")
app.add_typer(locations_app, name="locations")
app.add_typer(contacts_app, name="contacts")
app.add_typer(employees_app, name="employees")
app.add_typer(work_zones_app, name="work-zones")
app.add_typer(invoices_app, name="invoices")


@app.callback()
def app_callback() -> None:
    """
    Corrigo CLI - Interact with Corrigo Enterprise API from the command line.

    Configure credentials using environment variables or a config file.
    """
    pass


@app.command("debug")
def debug_connection(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Debug connection and endpoint discovery."""
    import httpx

    creds = get_credentials(profile)
    missing = validate_credentials(creds)

    console.print("[bold]1. Checking credentials...[/bold]")
    console.print(f"   client_id: {'[green]set[/green]' if creds.get('client_id') else '[red]missing[/red]'}")
    console.print(f"   client_secret: {'[green]set[/green]' if creds.get('client_secret') else '[red]missing[/red]'}")
    console.print(f"   company_name: {creds.get('company_name') or '[red]missing[/red]'}")
    console.print(f"   region: {creds.get('region', 'AM')}")

    if missing:
        print_error(f"Missing: {', '.join(missing)}")
        raise typer.Exit(1)

    console.print("\n[bold]2. Testing OAuth token...[/bold]")
    from corrigo.auth import CorrigoAuth, OAUTH_TOKEN_URL

    try:
        auth = CorrigoAuth(
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
        )
        token = auth.get_token()
        console.print(f"   [green]Token obtained successfully[/green]")
        console.print(f"   Token type: {token.token_type}")
        console.print(f"   Token prefix: {token.access_token[:20]}...")
    except Exception as e:
        print_error(f"OAuth failed: {e}")
        raise typer.Exit(1)

    console.print("\n[bold]3. Testing endpoint discovery...[/bold]")
    from corrigo.http import API_LOCATOR_URLS, DEFAULT_ENDPOINTS, Region

    region_map = {"AM": Region.AMERICAS, "APAC": Region.APAC, "EMEA": Region.EMEA}
    region = region_map.get(creds.get("region", "AM").upper(), Region.AMERICAS)
    locator_url = API_LOCATOR_URLS[region]

    console.print(f"   Locator URL: {locator_url}")
    console.print(f"   CompanyName: {creds['company_name']}")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                locator_url,
                json={"Command": {"CompanyName": creds["company_name"]}},
                headers={
                    "Authorization": token.authorization_header,
                    "Content-Type": "application/json",
                    "CompanyName": creds["company_name"],
                },
            )
            console.print(f"   Status: {response.status_code}")
            console.print(f"   [dim]Full response: {response.text[:1000]}[/dim]")
            if response.status_code == 200:
                data = response.json()
                # Check for nested CommandResult structure
                result = data.get("CommandResult", data)
                raw_url = result.get("Url", "")
                company_id = result.get("CompanyId")
                # Extract base URL from WSDL URL
                if raw_url:
                    from urllib.parse import urlparse
                    parsed = urlparse(raw_url)
                    base_url = f"https://{parsed.netloc}"
                else:
                    base_url = DEFAULT_ENDPOINTS[region]
                console.print(f"   [yellow]Raw URL: {raw_url}[/yellow]")
                console.print(f"   [green]REST API URL: {base_url}[/green]")
                console.print(f"   Company ID: {company_id}")
            else:
                console.print(f"   [yellow]Falling back to: {DEFAULT_ENDPOINTS[region]}[/yellow]")
    except Exception as e:
        print_error(f"Discovery request failed: {e}")

    console.print("\n[bold]4. Testing API endpoint...[/bold]")
    try:
        with get_client(profile) as client:
            # Try a simple query
            result = client._http.get("/base/WorkOrder/1", params={"properties": "Id"})
            console.print(f"   [green]API connection successful[/green]")
    except Exception as e:
        print_error(f"API request failed: {e}")


# Config commands


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key (client_id, client_secret, company_name, region)"),
    value: str = typer.Argument(..., help="Configuration value"),
    profile: str = typer.Option("default", "--profile", "-p", help="Profile name"),
) -> None:
    """Set a configuration value."""
    valid_keys = {"client_id", "client_secret", "company_name", "region"}
    if key not in valid_keys:
        console.print(f"[red]Invalid key: {key}[/red]")
        console.print(f"Valid keys: {', '.join(sorted(valid_keys))}")
        raise typer.Exit(1)

    config = Config()
    config.set_value(profile, key, value)
    console.print(f"[green]Set {key} for profile '{profile}'[/green]")


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Configuration key to retrieve"),
    profile: str = typer.Option("default", "--profile", "-p", help="Profile name"),
) -> None:
    """Get a configuration value."""
    config = Config()
    value = config.get_value(profile, key)
    if value:
        if key == "client_secret":
            console.print(f"{key}: {'*' * 8}")
        else:
            console.print(f"{key}: {value}")
    else:
        console.print(f"[yellow]{key} is not set for profile '{profile}'[/yellow]")


@config_app.command("list")
def config_list(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name (lists all profiles if not specified)"),
) -> None:
    """List configuration values."""
    config = Config()

    if profile:
        profile_config = config.get_profile(profile)
        if not profile_config:
            console.print(f"[yellow]No configuration found for profile '{profile}'[/yellow]")
            return

        table = Table(title=f"Profile: {profile}")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")

        for key, value in sorted(profile_config.items()):
            display_value = "*" * 8 if key == "client_secret" else str(value)
            table.add_row(key, display_value)

        console.print(table)
    else:
        profiles = config.list_profiles()
        if not profiles:
            console.print("[yellow]No profiles configured[/yellow]")
            console.print("Run 'corrigo config set client_id <value>' to get started.")
            return

        default_profile = config.get_default_profile()
        table = Table(title="Configured Profiles")
        table.add_column("Profile", style="cyan")
        table.add_column("Default", style="green")
        table.add_column("Company", style="white")

        for prof in sorted(profiles):
            is_default = "Yes" if prof == default_profile else ""
            company = config.get_value(prof, "company_name") or ""
            table.add_row(prof, is_default, company)

        console.print(table)


@config_app.command("delete")
def config_delete(
    key: Optional[str] = typer.Argument(None, help="Configuration key to delete (deletes entire profile if not specified)"),
    profile: str = typer.Option("default", "--profile", "-p", help="Profile name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a configuration value or entire profile."""
    config = Config()

    if key:
        if config.delete_value(profile, key):
            console.print(f"[green]Deleted {key} from profile '{profile}'[/green]")
        else:
            console.print(f"[yellow]{key} not found in profile '{profile}'[/yellow]")
    else:
        if not force:
            confirm = typer.confirm(f"Delete entire profile '{profile}'?")
            if not confirm:
                raise typer.Abort()

        if config.delete_profile(profile):
            console.print(f"[green]Deleted profile '{profile}'[/green]")
        else:
            console.print(f"[yellow]Profile '{profile}' not found[/yellow]")


@config_app.command("use")
def config_use(
    profile: str = typer.Argument(..., help="Profile to set as default"),
) -> None:
    """Set the default profile."""
    config = Config()
    if profile not in config.list_profiles():
        console.print(f"[red]Profile '{profile}' does not exist[/red]")
        raise typer.Exit(1)

    config.set_default_profile(profile)
    console.print(f"[green]Default profile set to '{profile}'[/green]")


@config_app.command("show")
def config_show(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile name"),
) -> None:
    """Show current configuration status."""
    config = Config()
    profile = profile or config.get_default_profile()
    creds = get_credentials(profile)
    missing = validate_credentials(creds)

    table = Table(title=f"Configuration Status (Profile: {profile})")
    table.add_column("Key", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Source", style="dim")

    import os
    for key in ["client_id", "client_secret", "company_name", "region"]:
        env_var = f"CORRIGO_{key.upper()}"
        from_env = bool(os.environ.get(env_var))
        value = creds.get(key)

        if key in missing:
            status = "[red]Not set[/red]"
            source = ""
        else:
            display = "*" * 8 if key == "client_secret" else str(value)
            status = f"[green]{display}[/green]"
            source = "env" if from_env else "config"

        table.add_row(key, status, source)

    console.print(table)

    if missing:
        console.print(f"\n[yellow]Missing required configuration: {', '.join(missing)}[/yellow]")
        console.print("Set via environment variables (CORRIGO_CLIENT_ID, etc.) or config file.")


# Work Order Commands


@work_orders_app.command("list")
def work_orders_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (Open, InProgress, Completed, etc.)"),
    customer_id: Optional[int] = typer.Option(None, "--customer", "-c", help="Filter by customer ID"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of results"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """List work orders with optional filters."""
    try:
        with get_client(profile) as client:
            filters: dict[str, Any] = {}
            if status:
                filters["status_id"] = status
            if customer_id:
                results = client.work_orders.list_by_customer(customer_id, limit=limit, **filters)
            else:
                results = client.work_orders.list(limit=limit, **filters)

            columns = ["Id", "Number", "StatusId", "TypeCategory", "Customer"]
            format_output(results, output, columns=columns, title="Work Orders")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@work_orders_app.command("get")
def work_orders_get(
    work_order_id: int = typer.Argument(..., help="Work order ID"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Get a work order by ID."""
    try:
        with get_client(profile) as client:
            result = client.work_orders.get(work_order_id)
            format_output(result, output, title=f"Work Order {work_order_id}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@work_orders_app.command("find")
def work_orders_find(
    number: str = typer.Argument(..., help="Work order number to find"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Find a work order by its number."""
    try:
        with get_client(profile) as client:
            result = client.work_orders.get_by_number(number)
            if result:
                format_output(result, output, title=f"Work Order {number}")
            else:
                print_error(f"Work order '{number}' not found")
                raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@work_orders_app.command("create")
def work_orders_create(
    customer_id: int = typer.Option(..., "--customer", "-c", help="Customer ID (required)"),
    asset_id: int = typer.Option(..., "--asset", "-a", help="Asset/location ID (required)"),
    task_id: int = typer.Option(..., "--task", "-t", help="Task ID (required)"),
    subtype_id: int = typer.Option(..., "--subtype", help="Work order subtype ID (required)"),
    priority_id: Optional[int] = typer.Option(None, "--priority", help="Priority ID"),
    contact: Optional[str] = typer.Option(None, "--contact", help="Contact email or phone"),
    auto_assign: bool = typer.Option(False, "--auto-assign", help="Auto-assign the work order"),
    auto_schedule: bool = typer.Option(False, "--auto-schedule", help="Auto-schedule the work order"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Create a new work order."""
    try:
        with get_client(profile) as client:
            result = client.work_orders.create(
                customer_id=customer_id,
                asset_id=asset_id,
                task_id=task_id,
                subtype_id=subtype_id,
                priority_id=priority_id,
                contact_address=contact,
                compute_assignment=auto_assign,
                compute_schedule=auto_schedule,
            )
            print_success(f"Created work order with ID: {result.get('Id', result)}")
            format_output(result, output)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@work_orders_app.command("assign")
def work_orders_assign(
    work_order_id: int = typer.Argument(..., help="Work order ID"),
    employee_id: Optional[int] = typer.Option(None, "--employee", "-e", help="Employee ID to assign to"),
    comment: Optional[str] = typer.Option(None, "--comment", "-m", help="Comment"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Assign a work order to an employee."""
    try:
        with get_client(profile) as client:
            result = client.work_orders.assign(work_order_id, employee_id, comment)
            print_success(f"Assigned work order {work_order_id}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@work_orders_app.command("start")
def work_orders_start(
    work_order_id: int = typer.Argument(..., help="Work order ID"),
    comment: Optional[str] = typer.Option(None, "--comment", "-m", help="Comment"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Start work on a work order."""
    try:
        with get_client(profile) as client:
            result = client.work_orders.start(work_order_id, comment)
            print_success(f"Started work order {work_order_id}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@work_orders_app.command("complete")
def work_orders_complete(
    work_order_id: int = typer.Argument(..., help="Work order ID"),
    comment: Optional[str] = typer.Option(None, "--comment", "-m", help="Completion comment"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Complete a work order."""
    try:
        with get_client(profile) as client:
            result = client.work_orders.complete(work_order_id, comment)
            print_success(f"Completed work order {work_order_id}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@work_orders_app.command("cancel")
def work_orders_cancel(
    work_order_id: int = typer.Argument(..., help="Work order ID"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Cancellation reason"),
    comment: Optional[str] = typer.Option(None, "--comment", "-m", help="Comment"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Cancel a work order."""
    try:
        with get_client(profile) as client:
            result = client.work_orders.cancel(work_order_id, reason, comment)
            print_success(f"Cancelled work order {work_order_id}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@work_orders_app.command("hold")
def work_orders_hold(
    work_order_id: int = typer.Argument(..., help="Work order ID"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Hold reason"),
    comment: Optional[str] = typer.Option(None, "--comment", "-m", help="Comment"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Put a work order on hold."""
    try:
        with get_client(profile) as client:
            result = client.work_orders.hold(work_order_id, reason, comment)
            print_success(f"Put work order {work_order_id} on hold")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@work_orders_app.command("reopen")
def work_orders_reopen(
    work_order_id: int = typer.Argument(..., help="Work order ID"),
    comment: Optional[str] = typer.Option(None, "--comment", "-m", help="Comment"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Reopen a cancelled or completed work order."""
    try:
        with get_client(profile) as client:
            result = client.work_orders.reopen(work_order_id, comment)
            print_success(f"Reopened work order {work_order_id}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


# Customer Commands


@customers_app.command("list")
def customers_list(
    work_zone_id: Optional[int] = typer.Option(None, "--work-zone", "-w", help="Filter by work zone ID"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of results"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """List customers with optional filters."""
    try:
        with get_client(profile) as client:
            if work_zone_id:
                results = client.customers.list_by_work_zone(work_zone_id, limit=limit)
            else:
                results = client.customers.list(limit=limit)

            columns = ["Id", "Name", "DisplayAs", "TenantCode", "WorkZone"]
            format_output(results, output, columns=columns, title="Customers")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@customers_app.command("get")
def customers_get(
    customer_id: int = typer.Argument(..., help="Customer ID"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Get a customer by ID."""
    try:
        with get_client(profile) as client:
            result = client.customers.get(customer_id)
            format_output(result, output, title=f"Customer {customer_id}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@customers_app.command("find")
def customers_find(
    tenant_code: str = typer.Argument(..., help="Tenant code to find"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Find a customer by tenant code."""
    try:
        with get_client(profile) as client:
            result = client.customers.get_by_tenant_code(tenant_code)
            if result:
                format_output(result, output, title=f"Customer {tenant_code}")
            else:
                print_error(f"Customer with tenant code '{tenant_code}' not found")
                raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@customers_app.command("create")
def customers_create(
    name: str = typer.Option(..., "--name", "-n", help="Customer name (required)"),
    work_zone_id: int = typer.Option(..., "--work-zone", "-w", help="Work zone ID (required)"),
    display_as: Optional[str] = typer.Option(None, "--display-as", "-d", help="Display name"),
    tenant_code: Optional[str] = typer.Option(None, "--tenant-code", "-t", help="Unique tenant code"),
    tax_exempt: bool = typer.Option(False, "--tax-exempt", help="Customer is tax exempt"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Create a new customer."""
    try:
        with get_client(profile) as client:
            result = client.customers.create(
                name=name,
                work_zone_id=work_zone_id,
                display_as=display_as,
                tenant_code=tenant_code,
                tax_exempt=tax_exempt,
            )
            print_success(f"Created customer with ID: {result.get('Id', result)}")
            format_output(result, output)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@customers_app.command("update")
def customers_update(
    customer_id: int = typer.Argument(..., help="Customer ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New name"),
    display_as: Optional[str] = typer.Option(None, "--display-as", "-d", help="New display name"),
    tax_exempt: Optional[bool] = typer.Option(None, "--tax-exempt", help="Tax exempt status"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Update an existing customer."""
    try:
        with get_client(profile) as client:
            # First get the current data to obtain ConcurrencyId
            current = client.customers.get(customer_id)

            data: dict[str, Any] = {
                "Entity": {"ConcurrencyId": current.get("ConcurrencyId")},
                "PropertySet": {"Properties": []},
            }

            if name is not None:
                data["Entity"]["Name"] = name
                data["PropertySet"]["Properties"].append("Name")
            if display_as is not None:
                data["Entity"]["DisplayAs"] = display_as
                data["PropertySet"]["Properties"].append("DisplayAs")
            if tax_exempt is not None:
                data["Entity"]["TaxExempt"] = tax_exempt
                data["PropertySet"]["Properties"].append("TaxExempt")

            if not data["PropertySet"]["Properties"]:
                print_error("No updates specified")
                raise typer.Exit(1)

            result = client.customers.update(customer_id, data)
            print_success(f"Updated customer {customer_id}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@customers_app.command("delete")
def customers_delete(
    customer_id: int = typer.Argument(..., help="Customer ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Delete a customer."""
    if not force:
        confirm = typer.confirm(f"Delete customer {customer_id}?")
        if not confirm:
            raise typer.Abort()

    try:
        with get_client(profile) as client:
            client.customers.delete(customer_id)
            print_success(f"Deleted customer {customer_id}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@customers_app.command("assets")
def customers_assets(
    customer_id: int = typer.Argument(..., help="Customer ID"),
    limit: int = typer.Option(500, "--limit", "-l", help="Maximum number of results"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """List all assets/locations for a customer (store)."""
    try:
        with get_client(profile) as client:
            results = client.locations.list_by_customer(customer_id, limit=limit)
            columns = ["Id", "Name", "TypeId", "ModelId", "ParentId"]
            format_output(results, output, columns=columns, title=f"Assets for Customer {customer_id}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


# Location Commands


@locations_app.command("list")
def locations_list(
    type_id: Optional[int] = typer.Option(None, "--type", "-t", help="Filter by type (1=Building, 2=Unit, 3=Community, 4=Equipment)"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of results"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """List locations with optional filters."""
    try:
        with get_client(profile) as client:
            if type_id:
                results = client.locations.list_by_type(type_id, limit=limit)
            else:
                results = client.locations.list(limit=limit)

            columns = ["Id", "Name", "TypeId", "ModelId", "Address"]
            format_output(results, output, columns=columns, title="Locations")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@locations_app.command("get")
def locations_get(
    location_id: int = typer.Argument(..., help="Location ID"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Get a location by ID."""
    try:
        with get_client(profile) as client:
            result = client.locations.get(location_id)
            format_output(result, output, title=f"Location {location_id}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@locations_app.command("search")
def locations_search(
    name: str = typer.Argument(..., help="Name pattern to search"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of results"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Search locations by name."""
    try:
        with get_client(profile) as client:
            results = client.locations.search_by_name(name, limit=limit)
            columns = ["Id", "Name", "TypeId", "Address"]
            format_output(results, output, columns=columns, title=f"Locations matching '{name}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@locations_app.command("buildings")
def locations_buildings(
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of results"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """List building locations."""
    try:
        with get_client(profile) as client:
            results = client.locations.list_buildings(limit=limit)
            columns = ["Id", "Name", "Address"]
            format_output(results, output, columns=columns, title="Buildings")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@locations_app.command("units")
def locations_units(
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of results"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """List unit locations."""
    try:
        with get_client(profile) as client:
            results = client.locations.list_units(limit=limit)
            columns = ["Id", "Name", "Address"]
            format_output(results, output, columns=columns, title="Units")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@locations_app.command("equipment")
def locations_equipment(
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of results"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """List equipment locations."""
    try:
        with get_client(profile) as client:
            results = client.locations.list_equipment(limit=limit)
            columns = ["Id", "Name", "ModelId"]
            format_output(results, output, columns=columns, title="Equipment")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@locations_app.command("details")
def locations_details(
    location_id: int = typer.Argument(..., help="Location/asset ID"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Get asset details including attributes (make, model, serial, etc.)."""
    try:
        with get_client(profile) as client:
            result = client.locations.get_with_attributes(location_id)

            if output == OutputFormat.JSON:
                format_output(result, output)
            else:
                # Display base info
                console.print(f"[bold]Asset {location_id}[/bold]")
                console.print(f"  Name: {result.get('Name')}")
                console.print(f"  Type: {result.get('TypeId')}")
                console.print(f"  Model ID: {result.get('ModelId')}")

                # Display attributes
                attrs = result.get('attributes', {})
                if attrs:
                    console.print("\n[bold]Attributes:[/bold]")
                    for name, value in sorted(attrs.items()):
                        console.print(f"  {name}: {value}")
                else:
                    console.print("\n[yellow]No attributes defined for this asset[/yellow]")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@locations_app.command("equipment-details")
def locations_equipment_details(
    customer_id: int = typer.Argument(..., help="Customer ID"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of results"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """List equipment for a customer with make/model/serial attributes."""
    try:
        with get_client(profile) as client:
            results = client.locations.list_equipment_with_attributes(customer_id, limit=limit)

            if output == OutputFormat.JSON:
                format_output(results, output)
            else:
                console.print(f"[bold]Equipment for Customer {customer_id}[/bold]\n")
                for equip in results:
                    attrs = equip.get('attributes', {})
                    model = attrs.get('Model #', '')
                    serial = attrs.get('Serial #', '')
                    mfr = attrs.get('Manufacturer Name', '')

                    info_parts = []
                    if mfr:
                        info_parts.append(mfr)
                    if model:
                        info_parts.append(f"Model: {model}")
                    if serial:
                        info_parts.append(f"S/N: {serial}")

                    info_str = " | ".join(info_parts) if info_parts else "[dim]No attributes[/dim]"
                    console.print(f"  [{equip.get('Id')}] {equip.get('Name')}")
                    console.print(f"        {info_str}")

                console.print(f"\n[dim]Total: {len(results)} equipment items[/dim]")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@locations_app.command("create")
def locations_create(
    name: str = typer.Option(..., "--name", "-n", help="Location name (required)"),
    model_id: int = typer.Option(..., "--model", "-m", help="Model/template ID (required)"),
    type_id: int = typer.Option(1, "--type", "-t", help="Type ID (1=Building, 2=Unit, 3=Community, 4=Equipment)"),
    street: Optional[str] = typer.Option(None, "--street", help="Street address"),
    city: Optional[str] = typer.Option(None, "--city", help="City"),
    state: Optional[str] = typer.Option(None, "--state", help="State/province"),
    zip_code: Optional[str] = typer.Option(None, "--zip", help="ZIP/postal code"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Create a new location."""
    try:
        with get_client(profile) as client:
            address = None
            if any([street, city, state, zip_code]):
                address = {}
                if street:
                    address["Street"] = street
                if city:
                    address["City"] = city
                if state:
                    address["State"] = state
                if zip_code:
                    address["Zip"] = zip_code

            result = client.locations.create(
                name=name,
                model_id=model_id,
                type_id=type_id,
                address=address,
            )
            print_success(f"Created location with ID: {result.get('Id', result)}")
            format_output(result, output)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@locations_app.command("update")
def locations_update(
    location_id: int = typer.Argument(..., help="Location ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New name"),
    street: Optional[str] = typer.Option(None, "--street", help="New street address"),
    city: Optional[str] = typer.Option(None, "--city", help="New city"),
    state: Optional[str] = typer.Option(None, "--state", help="New state"),
    zip_code: Optional[str] = typer.Option(None, "--zip", help="New ZIP code"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Update an existing location."""
    try:
        with get_client(profile) as client:
            # First get the current data to obtain ConcurrencyId
            current = client.locations.get(location_id)

            data: dict[str, Any] = {
                "Entity": {"ConcurrencyId": current.get("ConcurrencyId")},
                "PropertySet": {"Properties": []},
            }

            if name is not None:
                data["Entity"]["Name"] = name
                data["PropertySet"]["Properties"].append("Name")

            # Handle address updates
            address_updates = {}
            if street is not None:
                address_updates["Street"] = street
            if city is not None:
                address_updates["City"] = city
            if state is not None:
                address_updates["State"] = state
            if zip_code is not None:
                address_updates["Zip"] = zip_code

            if address_updates:
                data["Entity"]["Address"] = address_updates
                data["PropertySet"]["Properties"].append("Address")

            if not data["PropertySet"]["Properties"]:
                print_error("No updates specified")
                raise typer.Exit(1)

            result = client.locations.update(location_id, data)
            print_success(f"Updated location {location_id}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@locations_app.command("delete")
def locations_delete(
    location_id: int = typer.Argument(..., help="Location ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Config profile to use"),
) -> None:
    """Delete a location."""
    if not force:
        confirm = typer.confirm(f"Delete location {location_id}?")
        if not confirm:
            raise typer.Abort()

    try:
        with get_client(profile) as client:
            client.locations.delete(location_id)
            print_success(f"Deleted location {location_id}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@contacts_app.command("list")
def contacts_list() -> None:
    """List contacts."""
    typer.echo("Contacts list - not yet implemented")


@contacts_app.command("get")
def contacts_get(contact_id: int) -> None:
    """Get a contact by ID."""
    typer.echo(f"Get contact {contact_id} - not yet implemented")


@employees_app.command("list")
def employees_list() -> None:
    """List employees."""
    typer.echo("Employees list - not yet implemented")


@employees_app.command("get")
def employees_get(employee_id: int) -> None:
    """Get an employee by ID."""
    typer.echo(f"Get employee {employee_id} - not yet implemented")


@work_zones_app.command("list")
def work_zones_list() -> None:
    """List work zones."""
    typer.echo("Work zones list - not yet implemented")


@work_zones_app.command("get")
def work_zones_get(work_zone_id: int) -> None:
    """Get a work zone by ID."""
    typer.echo(f"Get work zone {work_zone_id} - not yet implemented")


@invoices_app.command("list")
def invoices_list() -> None:
    """List invoices."""
    typer.echo("Invoices list - not yet implemented")


@invoices_app.command("get")
def invoices_get(invoice_id: int) -> None:
    """Get an invoice by ID."""
    typer.echo(f"Get invoice {invoice_id} - not yet implemented")


if __name__ == "__main__":
    main()
