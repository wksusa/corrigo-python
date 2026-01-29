"""Location resource manager."""

from __future__ import annotations

from typing import Any

from corrigo.api.base import BaseResource


class LocationResource(BaseResource[Any]):
    """
    Resource manager for Location entities.

    Locations represent physical assets in the hierarchy - buildings, units,
    equipment, etc. They form the asset tree structure.
    """

    entity_type = "Location"

    def create(
        self,
        name: str,
        model_id: int,
        type_id: int = 1,  # Building by default
        address: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a new location.

        Args:
            name: Location name (max 64 chars, required).
            model_id: The model/template ID (required).
            type_id: Asset type (1=Building, 2=Unit, 3=Community, 4=Equipment).
            address: Address data (Street, City, State, Zip, etc.).
            **kwargs: Additional location fields.

        Returns:
            EntitySpecifier with the created location ID.
        """
        data: dict[str, Any] = {
            "Entity": {
                "Name": name,
                "ModelId": model_id,
                "TypeId": type_id,
            },
            "PropertySet": {"Properties": ["*"]},
        }

        if address:
            data["Entity"]["Address"] = address

        data["Entity"].update(kwargs)

        return self._http.post(f"/base/{self.entity_type}", json=data)

    def list_by_type(
        self, type_id: int, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        List locations of a specific type.

        Args:
            type_id: The asset type ID (1=Building, 2=Unit, etc.).
            limit: Maximum number of results.

        Returns:
            List of location data.
        """
        return self.list(limit=limit, type_id=type_id)

    def list_buildings(self, limit: int = 100) -> list[dict[str, Any]]:
        """List all building locations."""
        return self.list_by_type(1, limit)

    def list_units(self, limit: int = 100) -> list[dict[str, Any]]:
        """List all unit locations."""
        return self.list_by_type(2, limit)

    def list_equipment(self, limit: int = 100) -> list[dict[str, Any]]:
        """List all equipment locations."""
        return self.list_by_type(4, limit)

    def search_by_name(self, name: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Search locations by name (partial match).

        Args:
            name: Name pattern to search.
            limit: Maximum number of results.

        Returns:
            List of matching locations.
        """
        builder = self.query().limit(limit).where_like("Name", f"%{name}%")
        from corrigo.api.query import QueryExecutor

        return QueryExecutor(self._http, builder).execute()
