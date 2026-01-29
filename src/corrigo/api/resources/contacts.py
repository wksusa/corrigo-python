"""Contact resource manager."""

from __future__ import annotations

from typing import Any

from corrigo.api.base import BaseResource


class ContactResource(BaseResource[Any]):
    """
    Resource manager for Contact entities.

    Contacts represent people who can request work or interact with the
    Corrigo Customer Portal. Each contact belongs to a Customer.
    """

    entity_type = "Contact"

    def create(
        self,
        customer_id: int,
        last_name: str,
        username: str,
        first_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        number: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a new contact.

        Args:
            customer_id: The customer ID this contact belongs to.
            last_name: Contact's last name (required).
            username: Login username (max 256 chars, required).
            first_name: Contact's first name.
            email: Contact email address.
            phone: Contact phone number.
            number: Contact identifier/employee number.
            **kwargs: Additional contact fields.

        Returns:
            EntitySpecifier with the created contact ID.
        """
        data: dict[str, Any] = {
            "Entity": {
                "CustomerId": customer_id,
                "LastName": last_name,
                "Username": username,
            },
            "PropertySet": {"Properties": ["*"]},
        }

        if first_name:
            data["Entity"]["FirstName"] = first_name
        if number:
            data["Entity"]["Number"] = number

        # Add contact addresses
        addresses = []
        if email:
            addresses.append({"Address": email, "AddrTypeId": "Email"})
        if phone:
            addresses.append({"Address": phone, "AddrTypeId": "Phone"})
        if addresses:
            data["Entity"]["ContactAddresses"] = addresses

        data["Entity"].update(kwargs)

        return self._http.post(f"/base/{self.entity_type}", json=data)

    def get_by_username(self, username: str) -> dict[str, Any] | None:
        """
        Find a contact by username.

        Args:
            username: The contact's username.

        Returns:
            Contact data or None if not found.
        """
        return self.find_one(username=username)

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        """
        Find a contact by email address.

        Args:
            email: The contact's email.

        Returns:
            Contact data or None if not found.
        """
        builder = self.query().where_equal("ContactAddresses.Address", email)
        from corrigo.api.query import QueryExecutor

        results = QueryExecutor(self._http, builder).execute()
        return results[0] if results else None

    def list_by_customer(
        self, customer_id: int, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        List contacts for a specific customer.

        Args:
            customer_id: The customer ID.
            limit: Maximum number of results.

        Returns:
            List of contact data.
        """
        return self.list(limit=limit, customer_id=customer_id)
