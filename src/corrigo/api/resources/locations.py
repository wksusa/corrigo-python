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

    def list_by_customer(
        self, customer_id: int, limit: int = 500
    ) -> list[dict[str, Any]]:
        """
        List all assets/locations for a specific customer (store).

        In Corrigo, the CommunityId on Location corresponds to the Customer ID.

        Args:
            customer_id: The customer ID.
            limit: Maximum number of results.

        Returns:
            List of location/asset data for the customer.
        """
        builder = self.query().limit(limit).where_equal("CommunityId", customer_id)
        from corrigo.api.query import QueryExecutor

        return QueryExecutor(self._http, builder).execute()

    def get_with_attributes(self, asset_id: int) -> dict[str, Any]:
        """
        Get an asset/location with all its attributes (make, model, serial, etc.).

        Fetches the base Location data and joins it with AssetAttribute data,
        resolving attribute descriptor names.

        Args:
            asset_id: The asset/location ID.

        Returns:
            Asset data with an 'attributes' dict containing resolved attribute names/values.
            Example: {'Id': 123, 'Name': 'Grill 1', 'attributes': {'Model #': 'XYZ', 'Serial #': '123'}}
        """
        from corrigo.api.query import QueryBuilder, QueryExecutor

        # Get base asset data
        asset = self.get(asset_id)

        # Get asset attributes
        builder = QueryBuilder("AssetAttribute").where_equal("AssetId", asset_id).limit(100)
        executor = QueryExecutor(self._http, builder)
        raw_attrs = executor.execute()

        # Resolve descriptor names and build attributes dict
        attributes: dict[str, Any] = {}
        for attr in raw_attrs:
            desc_id = attr.get("Descriptor", {}).get("Id")
            value = attr.get("Value")
            if desc_id:
                try:
                    desc = self._http.get(f"/base/AttributeDescriptor/{desc_id}")
                    desc_name = desc.get("Data", desc).get("Name", f"Attribute {desc_id}")
                    attributes[desc_name] = value
                except Exception:
                    attributes[f"Attribute {desc_id}"] = value

        asset["attributes"] = attributes
        return asset

    def list_equipment_with_attributes(
        self, customer_id: int, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        List equipment for a customer with their attributes (make, model, serial, etc.).

        Args:
            customer_id: The customer ID.
            limit: Maximum number of equipment items.

        Returns:
            List of equipment with 'attributes' dict for each.
        """
        from corrigo.api.query import QueryBuilder, QueryExecutor

        # Get equipment for customer
        builder = (
            self.query()
            .limit(limit)
            .where_equal("CommunityId", customer_id)
            .where_equal("TypeId", "Equipment")
        )
        executor = QueryExecutor(self._http, builder)
        equipment = executor.execute()

        if not equipment:
            return []

        # Get all asset IDs
        asset_ids = [e.get("Id") for e in equipment if e.get("Id")]

        # Batch fetch all attributes for these assets
        builder = QueryBuilder("AssetAttribute").where_in("AssetId", *asset_ids).limit(5000)
        executor = QueryExecutor(self._http, builder)
        all_attrs = executor.execute()

        # Group attributes by asset ID
        attrs_by_asset: dict[int, list[dict[str, Any]]] = {}
        for attr in all_attrs:
            aid = attr.get("AssetId")
            if aid:
                if aid not in attrs_by_asset:
                    attrs_by_asset[aid] = []
                attrs_by_asset[aid].append(attr)

        # Cache descriptor lookups
        desc_cache: dict[int, str] = {}

        def get_desc_name(desc_id: int) -> str:
            if desc_id not in desc_cache:
                try:
                    desc = self._http.get(f"/base/AttributeDescriptor/{desc_id}")
                    desc_cache[desc_id] = desc.get("Data", desc).get("Name", f"Attribute {desc_id}")
                except Exception:
                    desc_cache[desc_id] = f"Attribute {desc_id}"
            return desc_cache[desc_id]

        # Attach attributes to each equipment item
        for equip in equipment:
            equip_id = equip.get("Id")
            attributes: dict[str, Any] = {}
            for attr in attrs_by_asset.get(equip_id, []):
                desc_id = attr.get("Descriptor", {}).get("Id")
                if desc_id:
                    desc_name = get_desc_name(desc_id)
                    attributes[desc_name] = attr.get("Value")
            equip["attributes"] = attributes

        return equipment
