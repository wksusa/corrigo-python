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
