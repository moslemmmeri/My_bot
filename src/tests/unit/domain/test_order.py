# src/tests/unit/domain/test_order.py
import pytest
from datetime import datetime
from decimal import Decimal

from my_bot.domain.entities.order import Order


class TestOrder:
    """Unit tests for Order entity."""

    def test_create_order(self):
        """Test creating an order with required fields."""
        order = Order(
            user_id=1,
            total_amount=150000,
            status="pending",
            items=[{"product": "Laptop", "quantity": 1, "price": 150000}],
        )
        assert order.user_id == 1
        assert order.total_amount == 150000
        assert order.status == "pending"
        assert order.items == [{"product": "Laptop", "quantity": 1, "price": 150000}]
        assert order.created_at is not None
        assert order.updated_at is not None

    def test_order_to_dict(self):
        """Test converting order to dictionary."""
        order = Order(
            user_id=1,
            total_amount=150000,
            status="pending",
            items=[{"product": "Laptop", "quantity": 1, "price": 150000}],
        )
        order.id = 100
        order.created_at = datetime(2024, 1, 1, 10, 0, 0)
        order.updated_at = datetime(2024, 1, 1, 11, 0, 0)

        data = order.to_dict()
        assert data["id"] == 100
        assert data["user_id"] == 1
        assert data["total_amount"] == 150000
        assert data["status"] == "pending"
        assert data["items"] == [{"product": "Laptop", "quantity": 1, "price": 150000}]
        assert data["created_at"] == "2024-01-01T10:00:00"
        assert data["updated_at"] == "2024-01-01T11:00:00"

    def test_order_from_dict(self):
        """Test creating order from dictionary."""
        data = {
            "id": 100,
            "user_id": 1,
            "total_amount": 150000,
            "status": "pending",
            "items": [{"product": "Laptop", "quantity": 1, "price": 150000}],
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T11:00:00",
        }
        order = Order.from_dict(data)
        assert order.id == 100
        assert order.user_id == 1
        assert order.total_amount == 150000
        assert order.status == "pending"
        assert order.items == [{"product": "Laptop", "quantity": 1, "price": 150000}]
        assert order.created_at == datetime(2024, 1, 1, 10, 0, 0)
        assert order.updated_at == datetime(2024, 1, 1, 11, 0, 0)

    def test_order_without_optional_fields(self):
        """Test creating order without optional fields."""
        order = Order(
            user_id=1,
            total_amount=150000,
            status="pending",
            items=None,
        )
        assert order.user_id == 1
        assert order.total_amount == 150000
        assert order.status == "pending"
        assert order.items == []  # Should default to empty list

    def test_order_update(self):
        """Test updating order fields."""
        order = Order(
            user_id=1,
            total_amount=150000,
            status="pending",
            items=[{"product": "Laptop", "quantity": 1, "price": 150000}],
        )
        old_updated_at = order.updated_at

        order.status = "paid"
        order.total_amount = 180000
        order.items = [{"product": "Mouse", "quantity": 2, "price": 30000}]
        order.updated_at = datetime.now()

        assert order.status == "paid"
        assert order.total_amount == 180000
        assert order.items == [{"product": "Mouse", "quantity": 2, "price": 30000}]
        assert order.updated_at > old_updated_at

    def test_order_equality(self):
        """Test order equality based on id."""
        order1 = Order(user_id=1, total_amount=100, status="pending")
        order1.id = 1
        order2 = Order(user_id=2, total_amount=200, status="paid")
        order2.id = 1
        order3 = Order(user_id=3, total_amount=300, status="cancelled")
        order3.id = 2

        assert order1 == order2
        assert order1 != order3
        assert order2 != order3

    def test_order_hash(self):
        """Test order hashing."""
        order1 = Order(user_id=1, total_amount=100, status="pending")
        order1.id = 1
        order2 = Order(user_id=2, total_amount=200, status="paid")
        order2.id = 1

        assert hash(order1) == hash(order2)

    def test_order_repr(self):
        """Test order string representation."""
        order = Order(
            user_id=1,
            total_amount=150000,
            status="pending",
            items=[{"product": "Laptop", "quantity": 1, "price": 150000}],
        )
        order.id = 100
        repr_str = repr(order)
        assert "Order" in repr_str
        assert "id=100" in repr_str
        assert "user_id=1" in repr_str
        assert "total_amount=150000" in repr_str
        assert "status='pending'" in repr_str

    def test_order_status_values(self):
        """Test that order status accepts valid statuses."""
        valid_statuses = ["pending", "paid", "shipped", "delivered", "cancelled", "failed"]
        for status in valid_statuses:
            order = Order(user_id=1, total_amount=100, status=status)
            assert order.status == status

        # Should accept any string for flexibility
        order = Order(user_id=1, total_amount=100, status="custom")
        assert order.status == "custom"

    def test_order_items_default_empty(self):
        """Test items default to empty list if None provided."""
        order = Order(user_id=1, total_amount=100, status="pending", items=None)
        assert order.items == []

    def test_order_amount_can_be_float_or_int(self):
        """Test total_amount can be int or float."""
        order1 = Order(user_id=1, total_amount=100, status="pending")
        assert order1.total_amount == 100

        order2 = Order(user_id=1, total_amount=100.50, status="pending")
        assert order2.total_amount == 100.50