"""Work order resource manager."""

from __future__ import annotations

import base64
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from corrigo.api.base import BaseResource
from corrigo.api.commands import CommandExecutor
from corrigo.models.enums import DocumentType

if TYPE_CHECKING:
    from corrigo.http import CorrigoHTTPClient


MAX_DOCUMENT_BYTES = 20 * 1024 * 1024  # Corrigo's 20 MB upload ceiling


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

    @staticmethod
    def _sort_action_logs(data: dict[str, Any]) -> dict[str, Any]:
        """Sort ActionLogRecords by ActionDate descending (newest first)."""
        logs = data.get("ActionLogRecords")
        if logs:
            logs.sort(key=lambda r: r.get("ActionDate", ""), reverse=True)
        return data

    def get(
        self,
        entity_id: int,
        properties: list[str] | None = None,
    ) -> dict[str, Any]:
        """Retrieve a work order by ID, with ActionLogRecords sorted newest-first."""
        result = super().get(entity_id, properties)
        return self._sort_action_logs(result)

    def list(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """List work orders, with ActionLogRecords sorted newest-first."""
        results = super().list(limit=limit, offset=offset, **filters)
        for wo in results:
            self._sort_action_logs(wo)
        return results

    def create(
        self,
        customer_id: int,
        asset_id: int,
        task_id: int,
        subtype_id: int = 259,
        contact_name: str | None = None,
        contact_phone: str | None = None,
        comment: str | None = None,
        priority_id: int | None = None,
        contact_address: str | None = None,
        compute_assignment: bool = True,
        compute_schedule: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a new work order.

        Args:
            customer_id: The customer ID.
            asset_id: The asset/location ID.
            task_id: The task ID.
            subtype_id: The work order subtype ID (default: 259 = "Request").
            contact_name: Name of the person reporting the issue.
            contact_phone: Phone number for the contact.
            comment: Description of the issue and any troubleshooting attempted.
            priority_id: Optional priority ID (omit to inherit from task).
            contact_address: Optional contact email/phone (legacy; prefer contact_phone).
            compute_assignment: Auto-assign the work order.
            compute_schedule: Auto-schedule the work order.
            **kwargs: Additional work order fields.

        Returns:
            The created work order data.
        """
        item: dict[str, Any] = {
            "Asset": {"Id": asset_id},
            "Task": {"Id": task_id},
        }
        if comment:
            item["Comment"] = comment

        work_order: dict[str, Any] = {
            "Customer": {"Id": customer_id},
            "SubType": {"Id": subtype_id},
            "Items": [item],
            "TypeCategory": kwargs.pop("type_category", "Request"),
        }

        if contact_name:
            work_order["ContactName"] = contact_name

        if contact_phone:
            work_order["ContactAddress"] = {
                "Address": contact_phone,
                "AddrTypeId": "Contact",
            }
        elif contact_address:
            work_order["ContactAddress"] = {
                "Address": contact_address,
                "AddrTypeId": "Contact",
            }

        if comment:
            work_order["TaskRefinement"] = comment

        if priority_id:
            work_order["Priority"] = {"Id": priority_id}

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
        action_reason_id: int,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Cancel a work order.

        ``action_reason_id`` is required: Corrigo's WoCancelCommand rejects
        calls without a tenant-configured reason ID. See
        :meth:`corrigo.api.commands.CommandExecutor.cancel_work_order` for how
        to obtain valid IDs.
        """
        return self._commands.cancel_work_order(work_order_id, action_reason_id, comment)

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

    def add_note(
        self,
        work_order_id: int,
        body: str,
        note_type: str = "Public",
    ) -> dict[str, Any]:
        """Add a note to a work order.

        Uses the ``POST /base/WoNote`` endpoint. Notes are separate from
        action log entries produced by status transitions.

        Valid ``note_type`` values:
        - ``"Public"``  — visible to all parties (default; can be added multiple times)
        - ``"Private"`` — internal only
        - ``"Completion"`` — technician completion summary (max one per work order)

        Args:
            work_order_id: The work order to annotate.
            body: Note text.
            note_type: One of ``"Public"``, ``"Private"``, or ``"Completion"``.

        Returns:
            ``{"EntitySpecifier": {"EntityType": "WoNote", "Id": <int>}}``
        """
        return self._http.post(
            "/base/WoNote",
            json={
                "Entity": {
                    "WorkOrderId": work_order_id,
                    "Body": body,
                    "NoteTypeId": note_type,
                }
            },
        )

    def attach_document(
        self,
        work_order_id: int,
        file: bytes | str | Path,
        *,
        filename: str | None = None,
        mime_type: str | None = None,
        doc_type: DocumentType | int = DocumentType.PICTURE,
        title: str | None = None,
        description: str | None = None,
        is_public: bool = True,
    ) -> dict[str, Any]:
        """Attach a photo, signature, or other document to a work order.

        Uses the ``POST /base/Document`` endpoint. The file content is sent
        base64-encoded in the JSON body — Corrigo Enterprise does not accept
        multipart uploads on this endpoint. Files land in Corrigo's regional
        S3 bucket and the returned record carries a ``DocUrl`` pointing at
        them.

        Args:
            work_order_id: The work order to attach the document to.
            file: File content. Either raw ``bytes``, or a filesystem path
                (``str`` or :class:`pathlib.Path`). When a path is given,
                ``filename`` and ``mime_type`` are inferred automatically
                unless overridden.
            filename: Required when ``file`` is ``bytes``; optional otherwise.
                Surfaces in the Corrigo UI as the document's filename.
            mime_type: Explicit MIME type. When omitted, inferred via
                :func:`mimetypes.guess_type`. Raises ``ValueError`` if it
                cannot be inferred — Corrigo records the MIME type and a wrong
                value is worse than failing loudly.
            doc_type: A :class:`DocumentType` member or a bare ``int`` for
                tenant-specific DocType IDs. Defaults to
                :attr:`DocumentType.PICTURE`.
            title: Display title in the UI. Defaults to ``filename`` when
                omitted.
            description: Optional long-form description.
            is_public: When ``True`` (default), the document is visible to all
                parties (technician, store, facilities team). When ``False``,
                it is internal-only.

        Returns:
            ``{"EntitySpecifier": {"EntityType": "Document", "Id": <int>}}``

        Raises:
            ValueError: If ``file`` is ``bytes`` without ``filename``, if
                ``mime_type`` cannot be inferred, or if the file exceeds the
                20 MB Corrigo upload limit.
        """
        if isinstance(file, (str, Path)):
            path = Path(file)
            file_bytes = path.read_bytes()
            if filename is None:
                filename = path.name
        else:
            file_bytes = file
            if filename is None:
                raise ValueError("filename is required when file is bytes")

        if mime_type is None:
            guessed, _ = mimetypes.guess_type(filename)
            if guessed is None:
                raise ValueError(
                    f"mime_type could not be inferred from filename {filename!r}; "
                    "pass mime_type explicitly"
                )
            mime_type = guessed

        if len(file_bytes) > MAX_DOCUMENT_BYTES:
            raise ValueError(
                f"file is {len(file_bytes)} bytes; Corrigo's upload limit is "
                f"{MAX_DOCUMENT_BYTES} bytes (20 MB)"
            )

        entity: dict[str, Any] = {
            "Title": title if title is not None else filename,
            "ActorTypeId": "WO",
            "ActorId": work_order_id,
            "StorageTypeId": "Cloud",
            "DocType": {"Id": int(doc_type)},
            "MimeType": mime_type,
            "IsPublic": is_public,
            "StartDate": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "Blob": {
                "FileName": filename,
                "Body": base64.b64encode(file_bytes).decode("ascii"),
            },
        }
        if description is not None:
            entity["Description"] = description

        return self._http.post("/base/Document", json={"Entity": entity})

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

    def list_on_hold(
        self,
        reason_id: int | None = None,
        limit: int = 4000,
    ) -> list[dict[str, Any]]:
        """List work orders currently on hold, with the current hold reason exposed.

        Each returned work order includes ``LastAction.Reason`` populated with
        ``Id``, ``DisplayAs``, ``ActionId``, and ``Descr`` — the same record
        Corrigo's admin UI uses for the "On Hold Reason" filter. Reading the
        current hold reason no longer requires walking ``ActionLogRecords``.

        When ``reason_id`` is provided, results are filtered client-side to
        work orders whose current hold reason matches. Corrigo's Query API
        rejects ``LastAction.Reason.Id`` as a server-side filter target, so
        the filter has to be applied after fetching. To make the ``limit``
        argument behave intuitively under a filter, this method always pulls
        the full OnHold pool (capped at Corrigo's 4000-per-page maximum),
        filters, and then truncates to ``limit``. Tenants typically have a
        few hundred OnHold work orders at most, so the full pull is cheap.

        Reason IDs are tenant-configured. To discover the ID for a hold reason
        in your tenant, fetch one known example and inspect
        ``LastAction.Reason.Id`` / ``LastAction.Reason.DisplayAs``.

        Args:
            reason_id: If provided, only return work orders whose current
                ``LastAction.Reason.Id`` matches this value.
            limit: Max work orders to return after filtering (capped at 4000).

        Returns:
            OnHold work orders with ``LastAction.Reason.*`` and
            ``ActionLogRecords`` populated (logs sorted newest-first).
        """
        from corrigo.api.query import QueryExecutor

        builder = (
            self.query()
            .select(
                "Id",
                "Number",
                "StatusId",
                "ShortLocation",
                "TaskRefinement",
                "Employee.Id",
                "Priority.Id",
                "DtCreated",
                "LastActionDate",
                "LastAction.*",
                "LastAction.Reason.*",
                "ActionLogRecords.*",
                "ActionLogRecords.Actor.*",
            )
            .where_equal("StatusId", "OnHold")
            .limit(4000)
        )
        results = QueryExecutor(self._http, builder).execute()
        for wo in results:
            self._sort_action_logs(wo)

        if reason_id is not None:
            results = [
                wo
                for wo in results
                if ((wo.get("LastAction") or {}).get("Reason") or {}).get("Id")
                == reason_id
            ]

        return results[: min(limit, 4000)]

    def list_documents(
        self,
        work_order_id: int,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List documents attached to a work order.

        Queries the ``Document`` entity filtered by ``ActorTypeId=WO`` and
        ``ActorId=<work_order_id>``. The returned records carry a ``DocUrl``
        field pointing at Corrigo's S3 bucket — callers can fetch the binary
        content directly without going back through this SDK.

        ``DocType`` is a scalar property on the ``Document`` entity and must
        be selected using dotted paths (``DocType.Id``, ``DocType.DisplayAs``)
        rather than as a whole — Corrigo's query API rejects bare
        ``DocType`` with ``ERROR_CODE_1003``.

        Args:
            work_order_id: The work order to query documents for.
            limit: Maximum number of results (capped at 4000 by Corrigo).

        Returns:
            List of Document data dictionaries. Empty list when no documents
            are attached.
        """
        from corrigo.api.query import QueryBuilder, QueryExecutor

        builder = (
            QueryBuilder("Document")
            .select(
                "Id",
                "Title",
                "Description",
                "MimeType",
                "StorageTypeId",
                "StartDate",
                "IsPublic",
                "DocUrl",
                "ActorTypeId",
                "ActorId",
                "DocType.Id",
                "DocType.DisplayAs",
            )
            .where_equal("ActorTypeId", "WO")
            .where_equal("ActorId", work_order_id)
            .limit(limit)
        )
        return QueryExecutor(self._http, builder).execute()

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
        """Find a work order by its display number.

        Work order numbers in Corrigo are 9-digit zero-padded strings (e.g.
        ``'072460001'``). Callers often drop the leading zero (e.g. from a
        voice caller reading aloud). This method normalises the input by
        left-padding with zeros to 9 digits when the value is all-numeric and
        shorter than 9 characters, so both ``'72460001'`` and ``'072460001'``
        resolve to the same work order.
        """
        normalized = number.strip()
        if normalized.isdigit() and len(normalized) < 9:
            normalized = normalized.zfill(9)
        return self.find_one(number=normalized)
