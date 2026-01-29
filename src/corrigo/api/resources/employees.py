"""Employee resource manager."""

from __future__ import annotations

from typing import Any

from corrigo.api.base import BaseResource


class EmployeeResource(BaseResource[Any]):
    """
    Resource manager for Employee entities.

    Employees represent internal users and service professionals who can
    be assigned to work orders. This includes technicians, managers, and
    other staff members.
    """

    entity_type = "Employee"

    def create(
        self,
        first_name: str,
        last_name: str,
        username: str,
        role_id: int,
        number: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        access_to_all_work_zones: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a new employee.

        Args:
            first_name: Employee's first name (required).
            last_name: Employee's last name (required).
            username: Login username (max 256 chars, required).
            role_id: The role ID for permissions (required).
            number: Employee identifier/number.
            email: Employee email address.
            phone: Employee phone number.
            access_to_all_work_zones: If True, employee can access all work zones.
            **kwargs: Additional employee fields.

        Returns:
            EntitySpecifier with the created employee ID.
        """
        data: dict[str, Any] = {
            "Entity": {
                "FirstName": first_name,
                "LastName": last_name,
                "Username": username,
                "Role": {"Id": role_id},
                "AccessToAllWorkZones": access_to_all_work_zones,
            },
            "PropertySet": {"Properties": ["*"]},
        }

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
        Find an employee by username.

        Args:
            username: The employee's username.

        Returns:
            Employee data or None if not found.
        """
        return self.find_one(username=username)

    def get_by_number(self, number: str) -> dict[str, Any] | None:
        """
        Find an employee by employee number.

        Args:
            number: The employee's number/identifier.

        Returns:
            Employee data or None if not found.
        """
        return self.find_one(number=number)

    def list_by_role(self, role_id: int, limit: int = 100) -> list[dict[str, Any]]:
        """
        List employees with a specific role.

        Args:
            role_id: The role ID.
            limit: Maximum number of results.

        Returns:
            List of employee data.
        """
        builder = self.query().limit(limit).where_equal("Role.Id", role_id)
        from corrigo.api.query import QueryExecutor

        return QueryExecutor(self._http, builder).execute()

    def list_available_for_assignment(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        List employees who can be assigned to work orders.

        Returns employees with ActorTypeId = Employee.

        Args:
            limit: Maximum number of results.

        Returns:
            List of employee data.
        """
        builder = self.query().limit(limit).where_equal("ActorTypeId", 1)  # Employee
        from corrigo.api.query import QueryExecutor

        return QueryExecutor(self._http, builder).execute()
