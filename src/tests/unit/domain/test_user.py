# src/tests/unit/domain/test_user.py
import pytest
from datetime import datetime
from my_bot.domain.entities.user import User


class TestUser:
    """Unit tests for User entity."""

    def test_create_user(self):
        """Test creating a user with required fields."""
        user = User(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            is_active=True,
            level="gold",
            points=100,
        )
        assert user.telegram_id == 123456789
        assert user.username == "test_user"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_active is True
        assert user.level == "gold"
        assert user.points == 100
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_to_dict(self):
        """Test converting user to dictionary."""
        user = User(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            is_active=True,
            level="gold",
            points=100,
        )
        user.id = 1
        user.created_at = datetime(2024, 1, 1, 10, 0, 0)
        user.updated_at = datetime(2024, 1, 1, 11, 0, 0)

        data = user.to_dict()
        assert data["id"] == 1
        assert data["telegram_id"] == 123456789
        assert data["username"] == "test_user"
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"
        assert data["is_active"] is True
        assert data["level"] == "gold"
        assert data["points"] == 100
        assert data["created_at"] == "2024-01-01T10:00:00"
        assert data["updated_at"] == "2024-01-01T11:00:00"

    def test_user_from_dict(self):
        """Test creating user from dictionary."""
        data = {
            "id": 1,
            "telegram_id": 123456789,
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "is_active": True,
            "level": "gold",
            "points": 100,
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T11:00:00",
        }
        user = User.from_dict(data)
        assert user.id == 1
        assert user.telegram_id == 123456789
        assert user.username == "test_user"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_active is True
        assert user.level == "gold"
        assert user.points == 100
        assert user.created_at == datetime(2024, 1, 1, 10, 0, 0)
        assert user.updated_at == datetime(2024, 1, 1, 11, 0, 0)

    def test_user_without_optional_fields(self):
        """Test creating user without optional fields."""
        user = User(
            telegram_id=123456789,
            username=None,
            first_name="Test",
            last_name=None,
            is_active=True,
            level="normal",
            points=0,
        )
        assert user.telegram_id == 123456789
        assert user.username is None
        assert user.first_name == "Test"
        assert user.last_name is None
        assert user.is_active is True
        assert user.level == "normal"
        assert user.points == 0

    def test_user_update(self):
        """Test updating user fields."""
        user = User(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            is_active=True,
            level="gold",
            points=100,
        )
        old_updated_at = user.updated_at

        user.username = "updated_user"
        user.is_active = False
        user.level = "silver"
        user.points = 200
        user.updated_at = datetime.now()

        assert user.username == "updated_user"
        assert user.is_active is False
        assert user.level == "silver"
        assert user.points == 200
        assert user.updated_at > old_updated_at

    def test_user_equality(self):
        """Test user equality based on id."""
        user1 = User(telegram_id=123456789)
        user1.id = 1
        user2 = User(telegram_id=987654321)
        user2.id = 1
        user3 = User(telegram_id=123456789)
        user3.id = 2

        assert user1 == user2
        assert user1 != user3
        assert user2 != user3

    def test_user_hash(self):
        """Test user hashing."""
        user1 = User(telegram_id=123456789)
        user1.id = 1
        user2 = User(telegram_id=987654321)
        user2.id = 1

        assert hash(user1) == hash(user2)

    def test_user_repr(self):
        """Test user string representation."""
        user = User(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
        )
        user.id = 1
        repr_str = repr(user)
        assert "User" in repr_str
        assert "id=1" in repr_str
        assert "telegram_id=123456789" in repr_str
        assert "username='test_user'" in repr_str

    def test_user_validate_level(self):
        """Test user level validation."""
        valid_levels = ["gold", "silver", "bronze", "normal"]
        for level in valid_levels:
            user = User(telegram_id=123456789, level=level)
            assert user.level == level

        # Should accept any string for flexibility, but we can test that it stores correctly
        user = User(telegram_id=123456789, level="custom")
        assert user.level == "custom"

    def test_user_is_active_default(self):
        """Test default value for is_active."""
        user = User(telegram_id=123456789)
        assert user.is_active is True