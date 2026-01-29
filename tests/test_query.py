"""Tests for the query builder module."""

import pytest

from corrigo.api.query import QueryBuilder
from corrigo.models.enums import ConditionOperator, FilterOperator


class TestQueryBuilder:
    """Tests for the QueryBuilder class."""

    def test_basic_query(self):
        """Should build a basic query with entity type."""
        query = QueryBuilder("WorkOrder").build()

        assert "PropertySet" in query
        assert query["PropertySet"]["Properties"] == ["*"]

    def test_select_properties(self):
        """Should include selected properties."""
        query = QueryBuilder("WorkOrder").select("Number", "StatusId").build()

        assert query["PropertySet"]["Properties"] == ["Number", "StatusId"]

    def test_select_all(self):
        """Should use wildcard for select_all."""
        query = QueryBuilder("WorkOrder").select_all().build()

        assert query["PropertySet"]["Properties"] == ["*"]

    def test_nested_properties(self):
        """Should handle nested property selection."""
        query = (
            QueryBuilder("WorkOrder")
            .select("Number", "Priority.*", "Customer.Name")
            .build()
        )

        assert "Priority.*" in query["PropertySet"]["Properties"]
        assert "Customer.Name" in query["PropertySet"]["Properties"]

    def test_where_condition(self):
        """Should add filter conditions."""
        query = (
            QueryBuilder("WorkOrder")
            .where("StatusId", ConditionOperator.EQUAL, "Open")
            .build()
        )

        assert "Criteria" in query
        assert len(query["Criteria"]["Conditions"]) == 1
        assert query["Criteria"]["Conditions"][0]["PropertyName"] == "StatusId"
        assert query["Criteria"]["Conditions"][0]["Operator"] == "Equal"
        assert query["Criteria"]["Conditions"][0]["Values"] == ["Open"]

    def test_multiple_conditions(self):
        """Should add multiple conditions with AND operator."""
        query = (
            QueryBuilder("WorkOrder")
            .where("StatusId", ConditionOperator.EQUAL, "Open")
            .where("Priority.Id", ConditionOperator.EQUAL, 1)
            .build()
        )

        assert len(query["Criteria"]["Conditions"]) == 2
        assert query["Criteria"]["FilterOperator"] == "And"

    def test_or_conditions(self):
        """Should use OR operator when specified."""
        query = (
            QueryBuilder("WorkOrder")
            .where("StatusId", ConditionOperator.EQUAL, "Open")
            .where("StatusId", ConditionOperator.EQUAL, "InProgress")
            .or_conditions()
            .build()
        )

        assert query["Criteria"]["FilterOperator"] == "Or"

    def test_where_shortcuts(self):
        """Should provide shortcut methods for common operators."""
        builder = QueryBuilder("WorkOrder")

        # Test various shortcuts
        builder.where_equal("Status", "Open")
        builder.where_not_equal("Status", "Closed")
        builder.where_greater_than("Id", 100)
        builder.where_less_than("Id", 1000)
        builder.where_like("Number", "WO%")
        builder.where_in("Status", "Open", "InProgress")

        query = builder.build()
        conditions = query["Criteria"]["Conditions"]

        assert len(conditions) == 6
        assert conditions[0]["Operator"] == "Equal"
        assert conditions[1]["Operator"] == "NotEqual"
        assert conditions[2]["Operator"] == "GreaterThan"
        assert conditions[3]["Operator"] == "LessThan"
        assert conditions[4]["Operator"] == "Like"
        assert conditions[5]["Operator"] == "In"

    def test_where_between(self):
        """Should handle between operator with two values."""
        query = (
            QueryBuilder("WorkOrder")
            .where_between("Id", 100, 200)
            .build()
        )

        condition = query["Criteria"]["Conditions"][0]
        assert condition["Operator"] == "Between"
        assert condition["Values"] == [100, 200]

    def test_where_is_null(self):
        """Should handle null checks."""
        query = (
            QueryBuilder("WorkOrder")
            .where_is_null("AssignedTo")
            .where_is_not_null("Customer")
            .build()
        )

        conditions = query["Criteria"]["Conditions"]
        assert conditions[0]["Operator"] == "IsNull"
        assert conditions[1]["Operator"] == "IsNotNull"

    def test_order_by_ascending(self):
        """Should add ascending order."""
        query = QueryBuilder("WorkOrder").order_by("Number").build()

        assert "Order" in query
        assert query["Order"]["PropertyName"] == "Number"
        assert query["Order"]["Direction"] == "Ascending"

    def test_order_by_descending(self):
        """Should add descending order."""
        query = QueryBuilder("WorkOrder").order_by("DtCreated", descending=True).build()

        assert query["Order"]["Direction"] == "Descending"

    def test_limit(self):
        """Should add count limit."""
        query = QueryBuilder("WorkOrder").limit(50).build()

        assert query["Count"] == 50

    def test_limit_max_4000(self):
        """Should cap limit at API maximum of 4000."""
        query = QueryBuilder("WorkOrder").limit(10000).build()

        assert query["Count"] == 4000

    def test_offset(self):
        """Should add pagination offset."""
        query = QueryBuilder("WorkOrder").offset(100).build()

        assert query["FirstResultIndex"] == 100

    def test_distinct(self):
        """Should add distinct flag."""
        query = QueryBuilder("WorkOrder").distinct().build()

        assert query["Distinct"] is True

    def test_chaining(self):
        """Should support fluent chaining."""
        query = (
            QueryBuilder("WorkOrder")
            .select("Number", "StatusId")
            .where_equal("StatusId", "Open")
            .order_by("DtCreated", descending=True)
            .limit(100)
            .offset(50)
            .build()
        )

        assert query["PropertySet"]["Properties"] == ["Number", "StatusId"]
        assert len(query["Criteria"]["Conditions"]) == 1
        assert query["Order"]["PropertyName"] == "DtCreated"
        assert query["Count"] == 100
        assert query["FirstResultIndex"] == 50

    def test_to_expression(self):
        """Should convert to QueryExpression model."""
        builder = (
            QueryBuilder("WorkOrder")
            .select("Number")
            .where_equal("Status", "Open")
            .limit(10)
        )

        expr = builder.to_expression()

        assert expr.entity_type == "WorkOrder"
        assert expr.property_set is not None
        assert expr.criteria is not None
        assert expr.count == 10
