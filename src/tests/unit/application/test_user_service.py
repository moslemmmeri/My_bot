# src/tests/unit/application/test_user_service.py
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from my_bot.core.exceptions import NotFoundError, ValidationError, DatabaseError
from my_bot.domain.entities.user import User
from my_bot.application.services.user.user_registration import UserRegistrationService
from my_bot.application.services.user.user_profile import UserProfileService


class TestUserRegistrationService:
    """Unit tests for UserRegistrationService."""

    @pytest.fixture
    def mock_user_repo(self):
        """Create a mock user repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_user_repo, mock_cache):
        """Create UserRegistrationService instance with mocks."""
        return UserRegistrationService(
            user_repo=mock_user_repo,
            cache=mock_cache,
        )

    @pytest.mark.asyncio
    async def test_register_user_new(self, service, mock_user_repo, mock_cache):
        """Test registering a new user."""
        # Setup
        mock_user_repo.find_by_telegram_id.return_value = None
        mock_user_repo.save.return_value = User(
            id=1,
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Execute
        result = await service.register_user(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
        )

        # Assert
        assert result.id == 1
        assert result.telegram_id == 123456789
        assert result.username == "test_user"
        assert result.first_name == "Test"
        assert result.last_name == "User"
        assert result.is_active is True
        mock_user_repo.find_by_telegram_id.assert_called_once_with(123456789)
        mock_user_repo.save.assert_called_once()
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_existing(self, service, mock_user_repo, mock_cache):
        """Test registering a user that already exists."""
        # Setup
        existing_user = User(
            id=1,
            telegram_id=123456789,
            username="existing_user",
            first_name="Existing",
            last_name="User",
            is_active=True,
        )
        mock_user_repo.find_by_telegram_id.return_value = existing_user

        # Execute
        result = await service.register_user(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
        )

        # Assert
        assert result.id == 1
        assert result.telegram_id == 123456789
        assert result.username == "existing_user"  # Should keep existing username
        mock_user_repo.find_by_telegram_id.assert_called_once_with(123456789)
        mock_user_repo.save.assert_not_called()
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_validation_error(self, service):
        """Test validation error when registering with invalid telegram_id."""
        with pytest.raises(ValidationError) as exc_info:
            await service.register_user(telegram_id=0)
        assert "Invalid telegram_id" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_register_user_database_error(self, service, mock_user_repo):
        """Test database error when registering user."""
        mock_user_repo.find_by_telegram_id.return_value = None
        mock_user_repo.save.side_effect = Exception("Database error")

        with pytest.raises(DatabaseError) as exc_info:
            await service.register_user(telegram_id=123456789)
        assert "Failed to register user" in str(exc_info.value)


class TestUserProfileService:
    """Unit tests for UserProfileService."""

    @pytest.fixture
    def mock_user_repo(self):
        """Create a mock user repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_user_repo, mock_cache):
        """Create UserProfileService instance with mocks."""
        return UserProfileService(
            user_repo=mock_user_repo,
            cache=mock_cache,
        )

    @pytest.mark.asyncio
    async def test_get_user_profile_found(self, service, mock_user_repo, mock_cache):
        """Test getting a user profile when user exists."""
        # Setup
        user = User(
            id=1,
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            is_active=True,
            level="gold",
            points=100,
        )
        mock_user_repo.find_by_id.return_value = user
        mock_cache.get.return_value = None  # Cache miss

        # Execute
        result = await service.get_user_profile(1)

        # Assert
        assert result["id"] == 1
        assert result["telegram_id"] == 123456789
        assert result["username"] == "test_user"
        assert result["first_name"] == "Test"
        assert result["last_name"] == "User"
        assert result["is_active"] is True
        assert result["level"] == "gold"
        assert result["points"] == 100
        mock_user_repo.find_by_id.assert_called_once_with(1)
        mock_cache.get.assert_called_once_with("user:1")
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_profile_from_cache(self, service, mock_user_repo, mock_cache):
        """Test getting user profile from cache."""
        # Setup
        cached_data = {
            "id": 1,
            "telegram_id": 123456789,
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "is_active": True,
            "level": "gold",
            "points": 100,
        }
        mock_cache.get.return_value = cached_data

        # Execute
        result = await service.get_user_profile(1)

        # Assert
        assert result["id"] == 1
        assert result["telegram_id"] == 123456789
        assert result["username"] == "test_user"
        mock_user_repo.find_by_id.assert_not_called()
        mock_cache.get.assert_called_once_with("user:1")

    @pytest.mark.asyncio
    async def test_get_user_profile_not_found(self, service, mock_user_repo, mock_cache):
        """Test getting user profile when user does not exist."""
        mock_user_repo.find_by_id.return_value = None
        mock_cache.get.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_user_profile(1)
        assert "User 1 not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, service, mock_user_repo, mock_cache):
        """Test updating user profile."""
        # Setup
        user = User(
            id=1,
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            is_active=True,
            level="gold",
            points=100,
        )
        mock_user_repo.find_by_id.return_value = user
        mock_user_repo.save.return_value = user

        # Execute
        result = await service.update_user_profile(
            user_id=1,
            first_name="Updated",
            last_name="Name",
            level="silver",
            points=200,
        )

        # Assert
        assert result["first_name"] == "Updated"
        assert result["last_name"] == "Name"
        assert result["level"] == "silver"
        assert result["points"] == 200
        mock_user_repo.save.assert_called_once()
        mock_cache.delete.assert_called_once_with("user:1")

    @pytest.mark.asyncio
    async def test_update_user_profile_not_found(self, service, mock_user_repo):
        """Test updating user profile when user does not exist."""
        mock_user_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.update_user_profile(user_id=1, first_name="Updated")
        assert "User 1 not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_user_profile_validation_error(self, service, mock_user_repo):
        """Test validation error when updating user profile with invalid data."""
        user = User(id=1, telegram_id=123456789)
        mock_user_repo.find_by_id.return_value = user

        with pytest.raises(ValidationError) as exc_info:
            await service.update_user_profile(user_id=1, level="invalid_level")
        assert "Invalid level" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_user_success(self, service, mock_user_repo, mock_cache):
        """Test deleting a user."""
        user = User(id=1, telegram_id=123456789)
        mock_user_repo.find_by_id.return_value = user
        mock_user_repo.delete.return_value = True

        result = await service.delete_user(1)
        assert result is True
        mock_user_repo.delete.assert_called_once_with(1)
        mock_cache.delete.assert_called_once_with("user:1")

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, service, mock_user_repo):
        """Test deleting a user that does not exist."""
        mock_user_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.delete_user(1)
        assert "User 1 not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_user_database_error(self, service, mock_user_repo):
        """Test database error when deleting user."""
        user = User(id=1, telegram_id=123456789)
        mock_user_repo.find_by_id.return_value = user
        mock_user_repo.delete.side_effect = Exception("Database error")

        with pytest.raises(DatabaseError) as exc_info:
            await service.delete_user(1)
        assert "Failed to delete user" in str(exc_info.value)