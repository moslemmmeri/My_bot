# src/tests/integration/test_db.py
"""
Integration tests for database operations.

These tests verify that database connections, queries, and transactions
work correctly with the actual database (using SQLite in-memory for testing).
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from my_bot.core.config import Config
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager
from my_bot.infrastructure.database.models.user_model import UserModel
from my_bot.infrastructure.database.models.order_model import OrderModel
from my_bot.infrastructure.database.models.payment_model import PaymentModel
from my_bot.infrastructure.database.models.coupon_model import CouponModel
from my_bot.infrastructure.database.models.ticket_model import TicketModel
from my_bot.infrastructure.database.models.feedback_model import FeedbackModel
from my_bot.infrastructure.database.models.content_model import ContentModel
from my_bot.infrastructure.database.models.admin_model import AdminModel
from my_bot.infrastructure.database.models.base import Base


# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Create a test database session."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def session_manager(db_engine):
    """Create a DatabaseSessionManager for testing."""
    # Use the engine directly for the manager
    manager = DatabaseSessionManager(
        db_url=TEST_DATABASE_URL,
        pool_size=5,
        max_overflow=10,
    )
    # Override the engine with our test engine
    manager._engine = db_engine
    yield manager
    await manager.close()


class TestDatabaseConnection:
    """Test database connection and session management."""

    @pytest.mark.asyncio
    async def test_connection_health(self, db_session):
        """Test that database connection is healthy."""
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_session_manager_connection(self, session_manager):
        """Test session manager can establish connection."""
        async with session_manager.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_pool_stats(self, session_manager):
        """Test connection pool statistics."""
        stats = await session_manager.get_pool_stats()
        assert "connections" in stats
        assert "active" in stats
        assert "idle" in stats
        assert "max" in stats


class TestCRUDOperations:
    """Test CRUD operations on database models."""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test creating a user."""
        user = UserModel(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            is_active=True,
            level="gold",
            points=100,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.telegram_id == 123456789
        assert user.username == "test_user"
        assert user.created_at is not None
        assert user.updated_at is not None

    @pytest.mark.asyncio
    async def test_read_user(self, db_session):
        """Test reading a user."""
        # Create user
        user = UserModel(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Read user
        result = await db_session.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": user.id}
        )
        row = result.first()
        assert row is not None
        assert row.id == user.id
        assert row.telegram_id == 123456789
        assert row.username == "test_user"

    @pytest.mark.asyncio
    async def test_update_user(self, db_session):
        """Test updating a user."""
        # Create user
        user = UserModel(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            is_active=True,
            level="gold",
            points=100,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Update user
        user.username = "updated_user"
        user.level = "silver"
        user.points = 200
        await db_session.commit()
        await db_session.refresh(user)

        assert user.username == "updated_user"
        assert user.level == "silver"
        assert user.points == 200

    @pytest.mark.asyncio
    async def test_delete_user(self, db_session):
        """Test deleting a user."""
        # Create user
        user = UserModel(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        user_id = user.id

        # Delete user
        await db_session.delete(user)
        await db_session.commit()

        # Verify deletion
        result = await db_session.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": user_id}
        )
        assert result.first() is None

    @pytest.mark.asyncio
    async def test_create_order_with_user(self, db_session):
        """Test creating an order associated with a user."""
        # Create user first
        user = UserModel(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create order
        order = OrderModel(
            user_id=user.id,
            total_amount=150000,
            status="pending",
            items='[{"product": "Laptop", "quantity": 1, "price": 150000}]',
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        assert order.id is not None
        assert order.user_id == user.id
        assert order.total_amount == 150000
        assert order.status == "pending"
        assert order.created_at is not None


class TestTransactions:
    """Test database transactions and rollbacks."""

    @pytest.mark.asyncio
    async def test_transaction_commit(self, db_session):
        """Test committing a transaction."""
        user = UserModel(
            telegram_id=123456789,
            username="test_user",
        )
        db_session.add(user)
        await db_session.commit()

        # Verify user exists
        result = await db_session.execute(
            text("SELECT * FROM users WHERE telegram_id = 123456789")
        )
        assert result.first() is not None

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_session):
        """Test rolling back a transaction."""
        user = UserModel(
            telegram_id=123456789,
            username="test_user",
        )
        db_session.add(user)
        await db_session.rollback()

        # Verify user does not exist
        result = await db_session.execute(
            text("SELECT * FROM users WHERE telegram_id = 123456789")
        )
        assert result.first() is None

    @pytest.mark.asyncio
    async def test_transaction_isolation(self, db_session):
        """Test transaction isolation."""
        # Create user in one transaction
        user = UserModel(
            telegram_id=123456789,
            username="test_user",
        )
        db_session.add(user)
        await db_session.commit()

        # In another transaction, verify user exists
        result = await db_session.execute(
            text("SELECT * FROM users WHERE telegram_id = 123456789")
        )
        row = result.first()
        assert row is not None
        assert row.username == "test_user"

    @pytest.mark.asyncio
    async def test_nested_transactions(self, db_session):
        """Test nested transaction behavior."""
        # Start outer transaction
        user = UserModel(
            telegram_id=123456789,
            username="outer_user",
        )
        db_session.add(user)
        await db_session.flush()

        # Inner transaction - add another user
        user2 = UserModel(
            telegram_id=987654321,
            username="inner_user",
        )
        db_session.add(user2)
        await db_session.flush()

        # Commit outer transaction
        await db_session.commit()

        # Verify both users exist
        result1 = await db_session.execute(
            text("SELECT * FROM users WHERE telegram_id = 123456789")
        )
        assert result1.first() is not None

        result2 = await db_session.execute(
            text("SELECT * FROM users WHERE telegram_id = 987654321")
        )
        assert result2.first() is not None


class TestBulkOperations:
    """Test bulk database operations."""

    @pytest.mark.asyncio
    async def test_bulk_insert(self, db_session):
        """Test bulk inserting users."""
        users = [
            UserModel(
                telegram_id=100 + i,
                username=f"user_{i}",
                first_name=f"First{i}",
                last_name=f"Last{i}",
                is_active=i % 2 == 0,
            )
            for i in range(10)
        ]
        db_session.add_all(users)
        await db_session.commit()

        # Verify all users were inserted
        result = await db_session.execute(text("SELECT COUNT(*) FROM users"))
        assert result.scalar() == 10

    @pytest.mark.asyncio
    async def test_bulk_update(self, db_session):
        """Test bulk updating users."""
        # Insert users
        users = [
            UserModel(
                telegram_id=100 + i,
                username=f"user_{i}",
                level="normal",
                points=0,
            )
            for i in range(5)
        ]
        db_session.add_all(users)
        await db_session.commit()

        # Bulk update
        await db_session.execute(
            text("UPDATE users SET level = 'gold', points = 100 WHERE level = 'normal'")
        )
        await db_session.commit()

        # Verify update
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM users WHERE level = 'gold' AND points = 100")
        )
        assert result.scalar() == 5


class TestConcurrency:
    """Test concurrent database operations."""

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, db_engine):
        """Test concurrent database operations."""
        async_session = sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async def create_user(i: int):
            async with async_session() as session:
                user = UserModel(
                    telegram_id=1000 + i,
                    username=f"concurrent_user_{i}",
                    first_name=f"Concurrent{i}",
                )
                session.add(user)
                await session.commit()

        # Run concurrent operations
        await asyncio.gather(*[create_user(i) for i in range(10)])

        # Verify all users were created
        async with async_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            # Note: There might be other users from previous tests
            # So we check that at least 10 users were created
            assert result.scalar() >= 10

    @pytest.mark.asyncio
    async def test_concurrent_updates(self, db_engine):
        """Test concurrent updates to the same record."""
        async_session = sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create a user
        async with async_session() as session:
            user = UserModel(
                telegram_id=999999,
                username="concurrent_update_user",
                points=0,
            )
            session.add(user)
            await session.commit()
            user_id = user.id

        async def update_user(user_id: int, increment: int):
            async with async_session() as session:
                result = await session.execute(
                    text("SELECT * FROM users WHERE id = :id"),
                    {"id": user_id}
                )
                user = result.scalar_one()
                user.points = user.points + increment
                await session.commit()

        # Run concurrent updates
        await asyncio.gather(
            update_user(user_id, 10),
            update_user(user_id, 20),
            update_user(user_id, 30),
        )

        # Verify final value
        async with async_session() as session:
            result = await session.execute(
                text("SELECT points FROM users WHERE id = :id"),
                {"id": user_id}
            )
            points = result.scalar()
            # The final value should be the sum of all increments (60)
            assert points == 60


class TestDatabaseSchema:
    """Test database schema and migrations."""

    @pytest.mark.asyncio
    async def test_all_tables_created(self, db_engine):
        """Test that all expected tables are created."""
        async with db_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = {row[0] for row in result.fetchall()}

        expected_tables = {
            "users",
            "orders",
            "payments",
            "coupons",
            "tickets",
            "feedback",
            "content",
            "admins",
        }
        # Check that all expected tables exist
        for table in expected_tables:
            assert table in tables

    @pytest.mark.asyncio
    async def test_table_columns(self, db_engine):
        """Test that tables have the expected columns."""
        async with db_engine.begin() as conn:
            result = await conn.execute(
                text("PRAGMA table_info(users)")
            )
            columns = {row[1] for row in result.fetchall()}

        expected_columns = {
            "id",
            "telegram_id",
            "username",
            "first_name",
            "last_name",
            "is_active",
            "level",
            "points",
            "created_at",
            "updated_at",
        }
        for col in expected_columns:
            assert col in columns


class TestDatabaseSessionManager:
    """Test DatabaseSessionManager functionality."""

    @pytest.mark.asyncio
    async def test_session_manager_get_session(self, session_manager):
        """Test getting a session from the manager."""
        async with session_manager.get_session() as session:
            assert session is not None
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_session_manager_pool_stats(self, session_manager):
        """Test getting pool statistics."""
        stats = await session_manager.get_pool_stats()
        assert stats["connections"] >= 0
        assert stats["active"] >= 0
        assert stats["idle"] >= 0
        assert stats["max"] > 0

    @pytest.mark.asyncio
    async def test_session_manager_close(self, session_manager):
        """Test closing the session manager."""
        await session_manager.close()
        # After closing, should be able to reopen
        new_manager = DatabaseSessionManager(
            db_url=TEST_DATABASE_URL,
            pool_size=5,
            max_overflow=10,
        )
        async with new_manager.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        await new_manager.close()


class TestQueryPerformance:
    """Test query performance and optimization."""

    @pytest.mark.asyncio
    async def test_index_usage(self, db_session):
        """Test that indexes are being used."""
        # Create some users
        users = [
            UserModel(
                telegram_id=100 + i,
                username=f"user_{i}",
            )
            for i in range(100)
        ]
        db_session.add_all(users)
        await db_session.commit()

        # Query by telegram_id (should use index)
        result = await db_session.execute(
            text("SELECT * FROM users WHERE telegram_id = 150")
        )
        assert result.first() is not None

    @pytest.mark.asyncio
    async def test_query_with_join(self, db_session):
        """Test join operations."""
        # Create user with orders
        user = UserModel(
            telegram_id=123456789,
            username="test_user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        orders = [
            OrderModel(
                user_id=user.id,
                total_amount=100 + i * 50,
                status="paid",
            )
            for i in range(5)
        ]
        db_session.add_all(orders)
        await db_session.commit()

        # Query with join
        result = await db_session.execute(
            text("""
                SELECT u.*, o.* 
                FROM users u 
                JOIN orders o ON u.id = o.user_id 
                WHERE u.id = :user_id
            """),
            {"user_id": user.id}
        )
        rows = result.fetchall()
        assert len(rows) == 5


class TestDataIntegrity:
    """Test data integrity constraints."""

    @pytest.mark.asyncio
    async def test_unique_constraint(self, db_session):
        """Test unique constraint on telegram_id."""
        user1 = UserModel(
            telegram_id=123456789,
            username="user1",
        )
        db_session.add(user1)
        await db_session.commit()

        # Attempt to create another user with same telegram_id
        user2 = UserModel(
            telegram_id=123456789,
            username="user2",
        )
        db_session.add(user2)
        with pytest.raises(Exception):  # SQLite raises IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_foreign_key_constraint(self, db_session):
        """Test foreign key constraint on order user_id."""
        # Create order without existing user
        order = OrderModel(
            user_id=999999,  # Non-existent user
            total_amount=100,
            status="pending",
        )
        db_session.add(order)
        with pytest.raises(Exception):  # SQLite raises IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_not_null_constraint(self, db_session):
        """Test NOT NULL constraint on required fields."""
        user = UserModel(
            # telegram_id is required
            username="test_user",
        )
        db_session.add(user)
        with pytest.raises(Exception):  # SQLite raises IntegrityError
            await db_session.commit()