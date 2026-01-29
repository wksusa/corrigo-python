"""Base resource class for entity-specific API operations."""

from __future__ import annotations

from typing import Any, Generic, TypeVar, TYPE_CHECKING

from corrigo.api.query import QueryBuilder, QueryExecutor

if TYPE_CHECKING:
    from corrigo.http import CorrigoHTTPClient
    from corrigo.models.base import CorrigoEntity


T = TypeVar("T", bound="CorrigoEntity")


class BaseResource(Generic[T]):
    """
    Base class for entity-specific resource managers.

    Provides common CRUD operations and query building for a specific
    entity type.

    Subclasses should set the `entity_type` class attribute and optionally
    override methods for entity-specific behavior.
    """

    entity_type: str = ""  # Override in subclass
    model_class: type[T] | None = None  # Override in subclass for typed results

    def __init__(self, http_client: CorrigoHTTPClient) -> None:
        """
        Initialize the resource manager.

        Args:
            http_client: The HTTP client for API requests.
        """
        self._http = http_client

    def get(
        self,
        entity_id: int,
        properties: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve an entity by ID.

        Args:
            entity_id: The entity ID.
            properties: List of properties to retrieve (optional).

        Returns:
            The entity data.
        """
        params = {}
        if properties:
            params["properties"] = ",".join(properties)

        response = self._http.get(f"/base/{self.entity_type}/{entity_id}", params=params)
        return response.get("Data", response)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new entity.

        Note: Some entities (WorkOrder, Space, WorkZone) require special
        commands and cannot be created via this method.

        Args:
            data: The entity data.

        Returns:
            EntitySpecifier with the created entity ID.
        """
        return self._http.post(f"/base/{self.entity_type}", json=data)

    def update(
        self,
        entity_id: int,
        data: dict[str, Any],
        properties: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Update an existing entity.

        Args:
            entity_id: The entity ID.
            data: The updated data (must include ConcurrencyId for optimistic locking).
            properties: List of properties being updated.

        Returns:
            Updated EntitySpecifier.
        """
        params = {}
        if properties:
            params["properties"] = ",".join(properties)

        return self._http.put(f"/base/{self.entity_type}/{entity_id}", json=data, params=params)

    def delete(self, entity_id: int, ignore_missing: bool = False) -> dict[str, Any]:
        """
        Delete an entity.

        Note: Some entities don't support deletion.

        Args:
            entity_id: The entity ID.
            ignore_missing: If True, don't error if entity doesn't exist.

        Returns:
            Empty response on success.
        """
        headers = {}
        if ignore_missing:
            headers["IgnoreMissingEntityOnDelete"] = "true"

        return self._http.delete(f"/base/{self.entity_type}/{entity_id}", headers=headers)

    def query(self) -> QueryBuilder:
        """
        Start building a query for this entity type.

        Returns:
            A QueryBuilder configured for this entity type.
        """
        return QueryBuilder(self.entity_type)

    def list(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """
        List entities with optional filtering.

        Args:
            limit: Maximum number of results (max 4000).
            offset: Starting index for pagination.
            **filters: Field=value pairs for filtering (uses Equal operator).

        Returns:
            List of entity data dictionaries.
        """
        builder = self.query().limit(limit).offset(offset)

        for field, value in filters.items():
            # Convert snake_case to PascalCase for API
            pascal_field = "".join(word.capitalize() for word in field.split("_"))
            builder.where_equal(pascal_field, value)

        executor = QueryExecutor(self._http, builder)
        return executor.execute()

    def find_one(self, **filters: Any) -> dict[str, Any] | None:
        """
        Find a single entity matching the filters.

        Args:
            **filters: Field=value pairs for filtering.

        Returns:
            The first matching entity, or None if not found.
        """
        results = self.list(limit=1, **filters)
        return results[0] if results else None

    def count(self, **filters: Any) -> int:
        """
        Count entities matching the filters.

        Args:
            **filters: Field=value pairs for filtering.

        Returns:
            The count of matching entities.
        """
        builder = self.query()

        for field, value in filters.items():
            pascal_field = "".join(word.capitalize() for word in field.split("_"))
            builder.where_equal(pascal_field, value)

        executor = QueryExecutor(self._http, builder)
        return executor.execute_count()

    def exists(self, entity_id: int) -> bool:
        """
        Check if an entity exists.

        Args:
            entity_id: The entity ID.

        Returns:
            True if the entity exists.
        """
        try:
            self.get(entity_id, properties=["Id"])
            return True
        except Exception:
            return False
