"""Command executor for the Corrigo Command API."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from corrigo.http import CorrigoHTTPClient


class CommandExecutor:
    """
    Executes commands against the Corrigo Command API.

    The Command API is used for operations that can't be performed via
    simple CRUD operations, such as creating WorkOrders, changing statuses,
    and other workflow operations.
    """

    def __init__(self, http_client: CorrigoHTTPClient) -> None:
        """
        Initialize the command executor.

        Args:
            http_client: The HTTP client for API requests.
        """
        self._http = http_client

    def execute(self, command_name: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute a command.

        Args:
            command_name: The command class name (e.g., "WoCreateCommand").
            **kwargs: Command parameters.

        Returns:
            Command response data.
        """
        return self._http.post(f"/cmd/{command_name}", json=kwargs)

    # Work Order Commands

    def create_work_order(
        self,
        work_order: dict[str, Any],
        compute_assignment: bool = False,
        compute_schedule: bool = False,
        skip_bill_to_logic: bool = False,
    ) -> dict[str, Any]:
        """
        Create a new work order.

        Args:
            work_order: The work order data including Items, Customer, SubType, etc.
            compute_assignment: Auto-assign the work order.
            compute_schedule: Auto-schedule the work order.
            skip_bill_to_logic: Skip billing logic.

        Returns:
            The created work order data.
        """
        return self.execute(
            "WoCreateCommand",
            WorkOrder=work_order,
            ComputeAssignment=compute_assignment,
            ComputeSchedule=compute_schedule,
            SkipBillToLogic=skip_bill_to_logic,
        )

    def assign_work_order(
        self,
        work_order_id: int,
        employee_id: int | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """
        Assign a work order to an employee.

        Args:
            work_order_id: The work order ID.
            employee_id: The employee ID to assign to.
            comment: Optional comment.

        Returns:
            Command response.
        """
        params: dict[str, Any] = {"WorkOrderId": work_order_id}
        if employee_id is not None:
            params["EmployeeId"] = employee_id
        if comment:
            params["Comment"] = comment
        return self.execute("WoAssignCommand", **params)

    def pickup_work_order(
        self,
        work_order_id: int,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """
        Pick up a work order (acknowledge assignment).

        Args:
            work_order_id: The work order ID.
            comment: Optional comment.

        Returns:
            Command response.
        """
        params: dict[str, Any] = {"WorkOrderId": work_order_id}
        if comment:
            params["Comment"] = comment
        return self.execute("WoPickUpCommand", **params)

    def start_work_order(
        self,
        work_order_id: int,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """
        Start work on a work order.

        Args:
            work_order_id: The work order ID.
            comment: Optional comment.

        Returns:
            Command response.
        """
        params: dict[str, Any] = {"WorkOrderId": work_order_id}
        if comment:
            params["Comment"] = comment
        return self.execute("WoStartCommand", **params)

    def complete_work_order(
        self,
        work_order_id: int,
        comment: str | None = None,
        completion_note_option: int = 2,
    ) -> dict[str, Any]:
        """
        Complete a work order.

        Args:
            work_order_id: The work order ID.
            comment: Completion comment.
            completion_note_option: Note option (default 2).

        Returns:
            Command response.
        """
        params: dict[str, Any] = {
            "WorkOrderId": work_order_id,
            "CompletionNoteOption": completion_note_option,
        }
        if comment:
            params["Comment"] = comment
        return self.execute("WoCompleteCommand", **params)

    def cancel_work_order(
        self,
        work_order_id: int,
        reason: str | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """
        Cancel a work order.

        Args:
            work_order_id: The work order ID.
            reason: Cancellation reason.
            comment: Optional comment.

        Returns:
            Command response.
        """
        params: dict[str, Any] = {"WorkOrderId": work_order_id}
        if reason:
            params["Reason"] = reason
        if comment:
            params["Comment"] = comment
        return self.execute("WoCancelCommand", **params)

    def reopen_work_order(
        self,
        work_order_id: int,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """
        Reopen a cancelled or completed work order.

        Args:
            work_order_id: The work order ID.
            comment: Optional comment.

        Returns:
            Command response.
        """
        params: dict[str, Any] = {"WorkOrderId": work_order_id}
        if comment:
            params["Comment"] = comment
        return self.execute("WoReopenCommand", **params)

    def hold_work_order(
        self,
        work_order_id: int,
        reason: str | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """
        Put a work order on hold.

        Args:
            work_order_id: The work order ID.
            reason: Hold reason.
            comment: Optional comment.

        Returns:
            Command response.
        """
        params: dict[str, Any] = {"WorkOrderId": work_order_id}
        if reason:
            params["Reason"] = reason
        if comment:
            params["Comment"] = comment
        return self.execute("WoOnHoldCommand", **params)

    def pause_work_order(
        self,
        work_order_id: int,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """
        Pause a work order.

        Args:
            work_order_id: The work order ID.
            comment: Optional comment.

        Returns:
            Command response.
        """
        params: dict[str, Any] = {"WorkOrderId": work_order_id}
        if comment:
            params["Comment"] = comment
        return self.execute("WoPauseCommand", **params)

    def flag_work_order(
        self,
        work_order_id: int,
        flag_id: int,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """
        Set a flag on a work order.

        Args:
            work_order_id: The work order ID.
            flag_id: The flag ID to set.
            comment: Optional comment.

        Returns:
            Command response.
        """
        params: dict[str, Any] = {
            "WorkOrderId": work_order_id,
            "FlagId": flag_id,
        }
        if comment:
            params["Comment"] = comment
        return self.execute("WoFlagCommand", **params)

    def send_work_order(self, work_order_id: int) -> dict[str, Any]:
        """
        Send a work order notification to the assigned service professional.

        Args:
            work_order_id: The work order ID.

        Returns:
            Command response.
        """
        return self.execute("SendWorkOrderCommand", WorkOrderId=work_order_id)

    def verify_work(
        self,
        work_order_id: int,
        rating_id: int | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """
        Verify completed work on a work order.

        Args:
            work_order_id: The work order ID.
            rating_id: Optional quality rating ID.
            comment: Optional verification comment.

        Returns:
            Command response.
        """
        params: dict[str, Any] = {"WorkOrderId": work_order_id}
        if rating_id is not None:
            params["WoRatingId"] = rating_id
        if comment:
            params["Comment"] = comment
        return self.execute("VerifyWorkCommand", **params)

    # Entity Creation Commands

    def create_work_zone(
        self,
        work_zone: dict[str, Any],
        asset_template_id: int,
        skip_default_settings: bool = False,
    ) -> dict[str, Any]:
        """
        Create a new work zone.

        Args:
            work_zone: The work zone data (DisplayAs, Number, WoNumberPrefix, TimeZone).
            asset_template_id: The asset template ID to use.
            skip_default_settings: Skip applying default settings.

        Returns:
            EntitySpecifier with the created work zone ID.
        """
        return self.execute(
            "WorkZoneCreateCommand",
            WorkZone=work_zone,
            AssetTemplateId=asset_template_id,
            SkipDefaultSettings=skip_default_settings,
        )

    def create_space(
        self,
        customer_id: int,
        unit_name: str,
        unit_floor_plan: str | None = None,
        street_address: dict[str, Any] | None = None,
        start_date: str | None = None,
        if_unit_already_exists: str = "Fail",
    ) -> dict[str, Any]:
        """
        Create a new space for a customer.

        Args:
            customer_id: The customer ID.
            unit_name: The unit/space name.
            unit_floor_plan: Optional floor plan reference.
            street_address: Optional address data.
            start_date: Optional start date.
            if_unit_already_exists: Behavior if unit exists ("Fail", "Skip", "Update").

        Returns:
            EntitySpecifier with the created space ID.
        """
        new_unit_specifier: dict[str, Any] = {"UnitName": unit_name}
        if unit_floor_plan:
            new_unit_specifier["UnitFloorPlan"] = unit_floor_plan
        if street_address:
            new_unit_specifier["StreetAddress"] = street_address

        params: dict[str, Any] = {
            "CustomerId": customer_id,
            "NewUnitSpecifier": new_unit_specifier,
            "IfUnitAlreadyExists": if_unit_already_exists,
        }
        if start_date:
            params["StartDate"] = start_date

        return self.execute("SpaceCreateCommand", **params)

    # Financial Commands

    def change_ap_status(
        self,
        work_order_id: int,
        vendor_invoice_status_id: int,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """
        Change the AP (vendor invoice) status on a work order.

        Args:
            work_order_id: The work order ID.
            vendor_invoice_status_id: The new status ID.
            comment: Optional comment.

        Returns:
            Command response.
        """
        params: dict[str, Any] = {
            "WorkOrderId": work_order_id,
            "VendorInvoiceStatusId": vendor_invoice_status_id,
        }
        if comment:
            params["Comment"] = comment
        return self.execute("ApStatusChangeCommand", **params)

    # Discovery Command

    def get_company_url(self, company_name: str) -> dict[str, Any]:
        """
        Discover the API endpoint URL for a company.

        Args:
            company_name: The company/tenant name.

        Returns:
            CompanyInfo with URL, CompanyId, CompanyVersion, etc.
        """
        return self.execute("GetCompanyWsdkUrlCommand", CompanyName=company_name)
