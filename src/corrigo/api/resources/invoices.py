"""Invoice resource manager."""

from __future__ import annotations

from typing import Any

from corrigo.api.base import BaseResource


class InvoiceResource(BaseResource[Any]):
    """
    Resource manager for Invoice entities.

    Invoices represent billing documents for customers. They have states
    (Draft, Posted, Paid, Credit) and contain line items.
    """

    entity_type = "Invoice"

    def list_by_state(
        self, state: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        List invoices by state.

        Args:
            state: Invoice state (Draft, Posted, Paid, Credit).
            limit: Maximum number of results.

        Returns:
            List of invoice data.
        """
        return self.list(limit=limit, state=state)

    def list_draft(self, limit: int = 100) -> list[dict[str, Any]]:
        """List draft invoices."""
        return self.list_by_state("Draft", limit)

    def list_posted(self, limit: int = 100) -> list[dict[str, Any]]:
        """List posted invoices."""
        return self.list_by_state("Posted", limit)

    def list_paid(self, limit: int = 100) -> list[dict[str, Any]]:
        """List paid invoices."""
        return self.list_by_state("Paid", limit)

    def list_by_customer(
        self, customer_id: int, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        List invoices for a specific customer.

        Args:
            customer_id: The customer ID.
            limit: Maximum number of results.

        Returns:
            List of invoice data.
        """
        builder = self.query().limit(limit).where_equal("Customer.Id", customer_id)
        from corrigo.api.query import QueryExecutor

        return QueryExecutor(self._http, builder).execute()
