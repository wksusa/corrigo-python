"""Work order resource manager."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from corrigo.api.base import BaseResource
from corrigo.api.commands import CommandExecutor

if TYPE_CHECKING:
    from corrigo.http import CorrigoHTTPClient


class WorkOrderResource(BaseResource[Any]):
    """
    Resource manager for WorkOrder entities.

    WorkOrders are the core entity in Corrigo, representing service requests
    and maintenance work items.

    Note: WorkOrders cannot be created via POST - use the create() method
    which internally uses WoCreateCommand.
    """

    entity_type = "WorkOrder"

    def __init__(self, http_client: CorrigoHTTPClient) -> None:
        super().__init__(http_client)
        self._commands = CommandExecutor(http_client)

    def create(
        self,
        customer_id: int,
        asset_id: int,
        task_id: int,
        subtype_id: int,
        priority_id: int | None = None,
        contact_address: str | None = None,
        compute_assignment: bool = False,
        compute_schedule: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a new work order.

        Args:
            customer_id: The customer ID.
            asset_id: The asset/location ID.
            task_id: The task ID.
            subtype_id: The work order subtype ID.
            priority_id: Optional priority ID.
            contact_address: Optional contact email/phone.
            compute_assignment: Auto-assign the work order.
            compute_schedule: Auto-schedule the work order.
            **kwargs: Additional work order fields.

        Returns:
            The created work order data.
        """
        work_order: dict[str, Any] = {
            "Customer": {"Id": customer_id},
            "SubType": {"Id": subtype_id},
            "Items": [
                {
                    "Asset": {"Id": asset_id},
                    "Task": {"Id": task_id},
                }
            ],
            "TypeCategory": kwargs.pop("type_category", "Request"),
        }

        if priority_id:
            work_order["Priority"] = {"Id": priority_id}

        if contact_address:
            work_order["ContactAddress"] = {
                "Address": contact_address,
                "AddrTypeId": "Contact",
            }

        # Add any additional fields
        work_order.update(kwargs)

        return self._commands.create_work_order(
            work_order=work_order,
            compute_assignment=compute_assignment,
            compute_schedule=compute_schedule,
        )

    def assign(
        self,
        work_order_id: int,
        employee_id: int | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Assign a work order to an employee."""
        return self._commands.assign_work_order(work_order_id, employee_id, comment)

    def pickup(self, work_order_id: int, comment: str | None = None) -> dict[str, Any]:
        """Pick up (acknowledge) a work order."""
        return self._commands.pickup_work_order(work_order_id, comment)

    def start(self, work_order_id: int, comment: str | None = None) -> dict[str, Any]:
        """Start work on a work order."""
        return self._commands.start_work_order(work_order_id, comment)

    def complete(
        self,
        work_order_id: int,
        comment: str | None = None,
        completion_note_option: int = 2,
    ) -> dict[str, Any]:
        """Complete a work order."""
        return self._commands.complete_work_order(work_order_id, comment, completion_note_option)

    def cancel(
        self,
        work_order_id: int,
        reason: str | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Cancel a work order."""
        return self._commands.cancel_work_order(work_order_id, reason, comment)

    def reopen(self, work_order_id: int, comment: str | None = None) -> dict[str, Any]:
        """Reopen a cancelled or completed work order."""
        return self._commands.reopen_work_order(work_order_id, comment)

    def hold(
        self,
        work_order_id: int,
        reason: str | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Put a work order on hold."""
        return self._commands.hold_work_order(work_order_id, reason, comment)

    def pause(self, work_order_id: int, comment: str | None = None) -> dict[str, Any]:
        """Pause a work order."""
        return self._commands.pause_work_order(work_order_id, comment)

    def flag(
        self,
        work_order_id: int,
        flag_id: int,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Set a flag on a work order."""
        return self._commands.flag_work_order(work_order_id, flag_id, comment)

    def send(self, work_order_id: int) -> dict[str, Any]:
        """Send notification to the assigned service professional."""
        return self._commands.send_work_order(work_order_id)

    def verify(
        self,
        work_order_id: int,
        rating_id: int | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Verify completed work."""
        return self._commands.verify_work(work_order_id, rating_id, comment)

    def delete(self, entity_id: int, ignore_missing: bool = False) -> dict[str, Any]:
        """
        WorkOrders cannot be deleted - use cancel() instead.

        Raises:
            NotImplementedError: Always raised.
        """
        raise NotImplementedError("WorkOrders cannot be deleted. Use cancel() instead.")

    # Query helpers

    def list_open(self, limit: int = 100, **filters: Any) -> list[dict[str, Any]]:
        """List open work orders."""
        return self.list(limit=limit, status_id="Open", **filters)

    def list_in_progress(self, limit: int = 100, **filters: Any) -> list[dict[str, Any]]:
        """List in-progress work orders."""
        return self.list(limit=limit, status_id="InProgress", **filters)

    def list_by_customer(
        self, customer_id: int, limit: int = 100, **filters: Any
    ) -> list[dict[str, Any]]:
        """List work orders for a specific customer."""
        builder = self.query().limit(limit).where_equal("Customer.Id", customer_id)
        for field, value in filters.items():
            pascal_field = "".join(word.capitalize() for word in field.split("_"))
            builder.where_equal(pascal_field, value)
        from corrigo.api.query import QueryExecutor

        return QueryExecutor(self._http, builder).execute()

    def get_by_number(self, number: str) -> dict[str, Any] | None:
        """Find a work order by its number."""
        return self.find_one(number=number)
