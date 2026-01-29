"""Work zone resource manager."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from corrigo.api.base import BaseResource
from corrigo.api.commands import CommandExecutor

if TYPE_CHECKING:
    from corrigo.http import CorrigoHTTPClient


class WorkZoneResource(BaseResource[Any]):
    """
    Resource manager for WorkZone entities.

    Work Zones define service delivery areas with operational parameters.
    They are the root container for Customers, Work Orders, and Assets.

    Note: WorkZones cannot be created via POST - use the create() method
    which internally uses WorkZoneCreateCommand.
    """

    entity_type = "WorkZone"

    def __init__(self, http_client: CorrigoHTTPClient) -> None:
        super().__init__(http_client)
        self._commands = CommandExecutor(http_client)

    def create(
        self,
        display_as: str,
        asset_template_id: int,
        number: str | None = None,
        wo_number_prefix: str | None = None,
        time_zone: int | None = None,
        skip_default_settings: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a new work zone.

        Args:
            display_as: Display name for the work zone.
            asset_template_id: The asset template ID to use.
            number: Work zone number/identifier.
            wo_number_prefix: Prefix for work order numbers.
            time_zone: Time zone ID.
            skip_default_settings: Skip applying default settings.
            **kwargs: Additional work zone fields.

        Returns:
            EntitySpecifier with the created work zone ID.
        """
        work_zone: dict[str, Any] = {
            "DisplayAs": display_as,
        }

        if number:
            work_zone["Number"] = number
        if wo_number_prefix:
            work_zone["WoNumberPrefix"] = wo_number_prefix
        if time_zone is not None:
            work_zone["TimeZone"] = time_zone

        work_zone.update(kwargs)

        return self._commands.create_work_zone(
            work_zone=work_zone,
            asset_template_id=asset_template_id,
            skip_default_settings=skip_default_settings,
        )

    def delete(self, entity_id: int, ignore_missing: bool = False) -> dict[str, Any]:
        """
        WorkZones cannot be deleted.

        Raises:
            NotImplementedError: Always raised.
        """
        raise NotImplementedError("WorkZones cannot be deleted.")

    def get_by_number(self, number: str) -> dict[str, Any] | None:
        """
        Find a work zone by number.

        Args:
            number: The work zone number.

        Returns:
            Work zone data or None if not found.
        """
        return self.find_one(number=number)
