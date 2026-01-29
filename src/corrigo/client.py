"""Main Corrigo client for high-level API access."""

from __future__ import annotations

from typing import Any

from corrigo.auth import CorrigoAuth
from corrigo.http import CorrigoHTTPClient, Region


class CorrigoClient:
    """
    High-level client for the Corrigo Enterprise REST API.

    Provides convenient access to all Corrigo API operations including
    work orders, customers, locations, employees, and more.

    Example:
        >>> client = CorrigoClient(
        ...     client_id="your_client_id",
        ...     client_secret="your_client_secret",
        ...     company_name="YourCompany",
        ... )
        >>> # Get a work order
        >>> wo = client.work_orders.get(12345)
        >>> # Query work orders
        >>> orders = client.work_orders.query().where("StatusId", "Open").execute()
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        company_name: str,
        region: Region | str = Region.AMERICAS,
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        """
        Initialize the Corrigo client.

        Args:
            client_id: OAuth client ID from Corrigo Enterprise settings.
            client_secret: OAuth client secret from Corrigo Enterprise settings.
            company_name: The Corrigo company/tenant name.
            region: API region - "AM", "APAC", "EMEA", or Region enum value.
            base_url: Override the base URL (skips automatic discovery).
            timeout: Request timeout in seconds.
        """
        # Convert string region to enum
        if isinstance(region, str):
            region_map = {
                "AM": Region.AMERICAS,
                "AMERICAS": Region.AMERICAS,
                "APAC": Region.APAC,
                "EMEA": Region.EMEA,
            }
            region = region_map.get(region.upper(), Region.AMERICAS)

        self._auth = CorrigoAuth(client_id=client_id, client_secret=client_secret)
        self._http = CorrigoHTTPClient(
            auth=self._auth,
            company_name=company_name,
            region=region,
            base_url=base_url,
            timeout=timeout,
        )
        self._company_name = company_name
        self._region = region

        # Initialize resource managers (lazy loaded)
        self._work_orders: WorkOrderResource | None = None
        self._customers: CustomerResource | None = None
        self._contacts: ContactResource | None = None
        self._employees: EmployeeResource | None = None
        self._locations: LocationResource | None = None
        self._work_zones: WorkZoneResource | None = None
        self._invoices: InvoiceResource | None = None

    @property
    def work_orders(self) -> WorkOrderResource:
        """Access work order operations."""
        if self._work_orders is None:
            from corrigo.api.resources.work_orders import WorkOrderResource

            self._work_orders = WorkOrderResource(self._http)
        return self._work_orders

    @property
    def customers(self) -> CustomerResource:
        """Access customer operations."""
        if self._customers is None:
            from corrigo.api.resources.customers import CustomerResource

            self._customers = CustomerResource(self._http)
        return self._customers

    @property
    def contacts(self) -> ContactResource:
        """Access contact operations."""
        if self._contacts is None:
            from corrigo.api.resources.contacts import ContactResource

            self._contacts = ContactResource(self._http)
        return self._contacts

    @property
    def employees(self) -> EmployeeResource:
        """Access employee operations."""
        if self._employees is None:
            from corrigo.api.resources.employees import EmployeeResource

            self._employees = EmployeeResource(self._http)
        return self._employees

    @property
    def locations(self) -> LocationResource:
        """Access location operations."""
        if self._locations is None:
            from corrigo.api.resources.locations import LocationResource

            self._locations = LocationResource(self._http)
        return self._locations

    @property
    def work_zones(self) -> WorkZoneResource:
        """Access work zone operations."""
        if self._work_zones is None:
            from corrigo.api.resources.work_zones import WorkZoneResource

            self._work_zones = WorkZoneResource(self._http)
        return self._work_zones

    @property
    def invoices(self) -> InvoiceResource:
        """Access invoice operations."""
        if self._invoices is None:
            from corrigo.api.resources.invoices import InvoiceResource

            self._invoices = InvoiceResource(self._http)
        return self._invoices

    # Low-level API access

    def get(self, entity_type: str, entity_id: int, properties: list[str] | None = None) -> dict[str, Any]:
        """
        Get an entity by ID using the Base API.

        Args:
            entity_type: The entity type (e.g., "WorkOrder", "Customer").
            entity_id: The entity ID.
            properties: List of properties to retrieve (optional).

        Returns:
            The entity data.
        """
        params = {}
        if properties:
            params["properties"] = ",".join(properties)
        return self._http.get(f"/base/{entity_type}/{entity_id}", params=params)

    def create(self, entity_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create an entity using the Base API.

        Note: WorkOrder, Space, and WorkZone require special commands.

        Args:
            entity_type: The entity type.
            data: The entity data.

        Returns:
            EntitySpecifier with the created entity ID.
        """
        return self._http.post(f"/base/{entity_type}", json=data)

    def update(
        self,
        entity_type: str,
        entity_id: int,
        data: dict[str, Any],
        properties: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Update an entity using the Base API.

        Args:
            entity_type: The entity type.
            entity_id: The entity ID.
            data: The updated entity data (must include ConcurrencyId).
            properties: List of properties being updated.

        Returns:
            Updated EntitySpecifier.
        """
        params = {}
        if properties:
            params["properties"] = ",".join(properties)
        return self._http.put(f"/base/{entity_type}/{entity_id}", json=data, params=params)

    def delete(self, entity_type: str, entity_id: int, ignore_missing: bool = False) -> dict[str, Any]:
        """
        Delete an entity using the Base API.

        Note: Some entities don't support deletion (WorkOrder, WorkZone, etc.).

        Args:
            entity_type: The entity type.
            entity_id: The entity ID.
            ignore_missing: If True, don't error if entity doesn't exist.

        Returns:
            Empty response on success.
        """
        headers = {}
        if ignore_missing:
            headers["IgnoreMissingEntityOnDelete"] = "true"
        return self._http.delete(f"/base/{entity_type}/{entity_id}", headers=headers)

    def query(self, entity_type: str, query_expression: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a query using the Query API.

        Args:
            entity_type: The entity type to query.
            query_expression: The QueryExpression object.

        Returns:
            Query results with Entities array.
        """
        return self._http.post(f"/query/{entity_type}", json=query_expression)

    def execute_command(self, command_name: str, command_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a command using the Command API.

        Args:
            command_name: The command class name (e.g., "WoCreateCommand").
            command_data: The command parameters.

        Returns:
            Command response.
        """
        return self._http.post(f"/cmd/{command_name}", json=command_data)

    def close(self) -> None:
        """Close the client and release resources."""
        self._http.close()
        self._auth.close()

    def __enter__(self) -> CorrigoClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


# Type hints for lazy-loaded resources (avoid circular imports)
class WorkOrderResource:
    """Placeholder for type hints."""

    pass


class CustomerResource:
    """Placeholder for type hints."""

    pass


class ContactResource:
    """Placeholder for type hints."""

    pass


class EmployeeResource:
    """Placeholder for type hints."""

    pass


class LocationResource:
    """Placeholder for type hints."""

    pass


class WorkZoneResource:
    """Placeholder for type hints."""

    pass


class InvoiceResource:
    """Placeholder for type hints."""

    pass
