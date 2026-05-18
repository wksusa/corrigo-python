"""Customer resource manager."""

from __future__ import annotations

from typing import Any

from corrigo.api.base import BaseResource


class CustomerResource(BaseResource[Any]):
    """
    Resource manager for Customer entities.

    Customers represent client organizations that request services.
    Each customer belongs to a WorkZone and can have multiple Contacts and Spaces.
    """

    entity_type = "Customer"

    def create(
        self,
        name: str,
        work_zone_id: int,
        display_as: str | None = None,
        tenant_code: str | None = None,
        tax_exempt: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a new customer.

        Args:
            name: Customer name (max 64 chars, required).
            work_zone_id: The work zone ID (required).
            display_as: Display name (max 64 chars, defaults to name).
            tenant_code: Unique tenant code.
            tax_exempt: Whether customer is tax exempt.
            **kwargs: Additional customer fields.

        Returns:
            EntitySpecifier with the created customer ID.
        """
        data: dict[str, Any] = {
            "Entity": {
                "Name": name,
                "DisplayAs": display_as or name,
                "WorkZone": {"Id": work_zone_id},
                "TaxExempt": tax_exempt,
            },
            "PropertySet": {"Properties": ["*"]},
        }

        if tenant_code:
            data["Entity"]["TenantCode"] = tenant_code

        data["Entity"].update(kwargs)

        return self._http.post(f"/base/{self.entity_type}", json=data)

    def get_by_tenant_code(self, tenant_code: str) -> dict[str, Any] | None:
        """
        Find a customer by tenant code.

        Args:
            tenant_code: The unique tenant code.

        Returns:
            Customer data or None if not found.
        """
        return self.find_one(tenant_code=tenant_code)

    def list_by_work_zone(
        self, work_zone_id: int, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        List customers in a specific work zone.

        Args:
            work_zone_id: The work zone ID.
            limit: Maximum number of results.

        Returns:
            List of customer data.
        """
        builder = self.query().limit(limit).where_equal("WorkZone.Id", work_zone_id)
        from corrigo.api.query import QueryExecutor

        return QueryExecutor(self._http, builder).execute()

    def get_custom_fields(self, customer_id: int) -> dict[str, str]:
        """Return a customer's custom fields keyed by their human-readable name.

        Custom fields (District Manager, DM Email, Brand VP, Facilities
        Manager, Supervisor, etc.) live on the Customer entity but are NOT
        exposed via the Query API or via ``/base/Customer/{id}`` with the
        default property set. The only working access path is to request
        ``CustomFields.Descriptor.Name`` and ``CustomFields.Value``
        explicitly.

        Values are plain strings as stored in Corrigo's tenant config — the
        District Manager field, for example, holds a human name, not a
        foreign key to an Employee record. Field names are tenant-specific;
        for the WKS tenant see the project documentation.

        Args:
            customer_id: The Corrigo Customer (store) ID.

        Returns:
            A mapping of ``Descriptor.Name`` → ``Value``. Empty dict when the
            customer has no custom fields. Entries lacking a name are
            skipped; if two custom fields share a name, the last one wins.
        """
        response = self._http.get(
            f"/base/{self.entity_type}/{customer_id}",
            params={"properties": "CustomFields.Descriptor.Name,CustomFields.Value"},
        )
        data = response.get("Data", response) if isinstance(response, dict) else {}
        fields = data.get("CustomFields") or []
        result: dict[str, str] = {}
        for entry in fields:
            descriptor = entry.get("Descriptor") or {}
            name = descriptor.get("Name")
            if name is None:
                continue
            result[name] = entry.get("Value")
        return result

    def get_district_manager(self, customer_id: int) -> str | None:
        """Return the District Manager name for a customer, or ``None``.

        Shortcut for ``get_custom_fields(customer_id).get("District Manager")``.
        The value is the human's full name as free text (the custom field is
        Descriptor.Id 1069 on the WKS tenant), not a foreign key — see the
        Customer custom fields guide for related fields (DM phone, DM email).

        Args:
            customer_id: The Corrigo Customer (store) ID.

        Returns:
            The District Manager name, or ``None`` if the field is not set
            on this customer.
        """
        return self.get_custom_fields(customer_id).get("District Manager")
