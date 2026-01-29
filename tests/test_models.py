"""Tests for the models module."""

import pytest

from corrigo.models.base import (
    CorrigoEntity,
    EntitySpecifier,
    PropertySet,
    MoneyValue,
    Address,
    ContactInfo,
    QueryExpression,
    FilterExpression,
    ConditionExpression,
    OrderExpression,
)
from corrigo.models.enums import (
    EntityType,
    WorkOrderStatus,
    WorkOrderType,
    AssetType,
    ConditionOperator,
    FilterOperator,
)


class TestCorrigoEntity:
    """Tests for the CorrigoEntity base class."""

    def test_create_entity_with_defaults(self):
        """Should create entity with default values."""
        entity = CorrigoEntity()

        assert entity.id is None
        assert entity.concurrency_id is None
        assert entity.is_new is None
        assert entity.is_removed is None

    def test_create_entity_with_values(self):
        """Should create entity with provided values."""
        entity = CorrigoEntity(
            id=123,
            concurrency_id=1,
            is_new=False,
            is_removed=False,
        )

        assert entity.id == 123
        assert entity.concurrency_id == 1
        assert entity.is_new is False

    def test_create_entity_from_api_response(self):
        """Should create entity from API response with PascalCase."""
        data = {
            "Id": 456,
            "ConcurrencyId": 2,
            "IsNew": True,
            "IsRemoved": False,
        }

        entity = CorrigoEntity.from_api_response(data)

        assert entity.id == 456
        assert entity.concurrency_id == 2
        assert entity.is_new is True

    def test_to_api_dict(self):
        """Should convert entity to API dict with PascalCase."""
        entity = CorrigoEntity(id=789, concurrency_id=3)

        data = entity.to_api_dict()

        assert data["Id"] == 789
        assert data["ConcurrencyId"] == 3

    def test_to_api_dict_excludes_none(self):
        """Should exclude None values by default."""
        entity = CorrigoEntity(id=100)

        data = entity.to_api_dict()

        assert "Id" in data
        assert "ConcurrencyId" not in data

    def test_extra_fields_allowed(self):
        """Should allow extra fields from API."""
        data = {
            "Id": 100,
            "ExtraField": "value",
            "AnotherField": 123,
        }

        entity = CorrigoEntity.model_validate(data)

        assert entity.id == 100


class TestEntitySpecifier:
    """Tests for EntitySpecifier."""

    def test_create_from_api_response(self):
        """Should create from API response."""
        data = {
            "EntityType": "WorkOrder",
            "Id": 12345,
            "ConcurrencyId": 1,
        }

        specifier = EntitySpecifier.model_validate(data)

        assert specifier.entity_type == "WorkOrder"
        assert specifier.id == 12345
        assert specifier.concurrency_id == 1


class TestPropertySet:
    """Tests for PropertySet."""

    def test_all_properties(self):
        """Should create wildcard property set."""
        props = PropertySet.all()

        assert props.properties == ["*"]

    def test_select_properties(self):
        """Should create property set with specific properties."""
        props = PropertySet.select("Number", "StatusId", "Priority.*")

        assert "Number" in props.properties
        assert "StatusId" in props.properties
        assert "Priority.*" in props.properties


class TestMoneyValue:
    """Tests for MoneyValue."""

    def test_create_money_value(self):
        """Should create money value."""
        money = MoneyValue(amount=100.50, currency_type="USD")

        assert money.amount == 100.50
        assert money.currency_type == "USD"

    def test_default_amount(self):
        """Should default amount to 0."""
        money = MoneyValue()

        assert money.amount == 0.0


class TestAddress:
    """Tests for Address."""

    def test_create_address(self):
        """Should create address with all fields."""
        addr = Address(
            street="123 Main St",
            city="Anytown",
            state="CA",
            zip="12345",
            country="USA",
            latitude=34.0522,
            longitude=-118.2437,
        )

        assert addr.street == "123 Main St"
        assert addr.city == "Anytown"
        assert addr.latitude == 34.0522


class TestQueryExpression:
    """Tests for QueryExpression."""

    def test_create_query_expression(self):
        """Should create query expression."""
        query = QueryExpression(
            entity_type="WorkOrder",
            property_set=PropertySet(properties=["Number", "StatusId"]),
            count=100,
            first_result_index=0,
        )

        assert query.entity_type == "WorkOrder"
        assert query.count == 100

    def test_query_with_criteria(self):
        """Should create query with filter criteria."""
        condition = ConditionExpression(
            property_name="StatusId",
            operator="Equal",
            values=["Open"],
        )
        criteria = FilterExpression(
            conditions=[condition],
            filter_operator="And",
        )
        query = QueryExpression(
            entity_type="WorkOrder",
            criteria=criteria,
        )

        assert len(query.criteria.conditions) == 1
        assert query.criteria.conditions[0].property_name == "StatusId"


class TestEnums:
    """Tests for enumerations."""

    def test_entity_type_values(self):
        """Should have correct entity type values."""
        assert EntityType.WORK_ORDER.value == "WorkOrder"
        assert EntityType.CUSTOMER.value == "Customer"
        assert EntityType.CONTACT.value == "Contact"

    def test_work_order_status_values(self):
        """Should have correct work order status values."""
        assert WorkOrderStatus.OPEN.value == "Open"
        assert WorkOrderStatus.IN_PROGRESS.value == "InProgress"
        assert WorkOrderStatus.COMPLETED.value == "Completed"

    def test_work_order_type_values(self):
        """Should have correct work order type values."""
        assert WorkOrderType.REQUEST.value == "Request"
        assert WorkOrderType.PMRM.value == "PMRM"

    def test_asset_type_values(self):
        """Should have correct asset type values."""
        assert AssetType.BUILDING == 1
        assert AssetType.UNIT == 2
        assert AssetType.EQUIPMENT == 4

    def test_condition_operator_values(self):
        """Should have correct condition operator values."""
        assert ConditionOperator.EQUAL.value == "Equal"
        assert ConditionOperator.GREATER_THAN.value == "GreaterThan"
        assert ConditionOperator.LIKE.value == "Like"
        assert ConditionOperator.IN.value == "In"

    def test_filter_operator_values(self):
        """Should have correct filter operator values."""
        assert FilterOperator.AND.value == "And"
        assert FilterOperator.OR.value == "Or"
