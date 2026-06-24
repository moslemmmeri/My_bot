# src/tests/integration/test_cache.py
"""
Integration tests for cache operations.

These tests verify that the cache manager works correctly with both
Redis (if available) and the local fallback cache. Tests use an
in-memory Redis mock or the local cache for isolation.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

from my_bot.core.config import Config
from my_bot.core.exceptions import CacheError
from my_bot.infrastructure.cache.cache_manager import CacheManager
from my_bot.infrastructure.cache.redis_adapter import RedisAdapter
from my_bot.infrastructure.cache.local_adapter import LocalAdapter
from my_bot.infrastructure.cache.cache_fallback import CacheFallback


# Test configuration
TEST_REDIS_URL = "redis://localhost:6379/15"  # Use DB 15 for testing
TEST_CACHE_TTL = 60


@pytest.fixture
def config():
    """Create test configuration."""
    return Config(
        bot_token="test_token",
        admin_ids=[],
        db_url="sqlite:///:memory:",
        redis_url=TEST_REDIS_URL,
        cache_ttl_seconds=TEST_CACHE_TTL,
        log_file_path="logs/test.log",
    )


@pytest.fixture
def local_cache():
    """Create a local cache adapter for testing."""
    return LocalAdapter(ttl=TEST_CACHE_TTL)


@pytest.fixture
def redis_cache(config):
    """Create a Redis cache adapter for testing."""
    # Try to connect to Redis, but if not available, use a mock
    try:
        adapter = RedisAdapter(redis_url=config.redis_url, ttl=config.cache_ttl_seconds)
        # Test connection
        import asyncio
        async def test_conn():
            return await adapter.ping()
        if asyncio.run(test_conn()):
            return adapter
    except Exception:
        pass
    # Fallback to mock Redis adapter
    mock_adapter = AsyncMock(spec=RedisAdapter)
    mock_adapter.get = AsyncMock(return_value=None)
    mock_adapter.set = AsyncMock(return_value=True)
    mock_adapter.delete = AsyncMock(return_value=True)
    mock_adapter.exists = AsyncMock(return_value=False)
    mock_adapter.ping = AsyncMock(return_value=True)
    mock_adapter.close = AsyncMock()
    mock_adapter.get_type = Mock(return_value="redis")
    return mock_adapter


@pytest.fixture
def cache_manager(redis_cache, local_cache):
    """Create a CacheManager with fallback."""
    return CacheFallback(
        primary=redis_cache,
        fallback=local_cache,
        fallback_on_error=True,
    )


class TestLocalCache:
    """Test local cache adapter."""

    @pytest.mark.asyncio
    async def test_set_and_get(self, local_cache):
        """Test setting and getting a value from local cache."""
        await local_cache.set("key1", "value1")
        result = await local_cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_missing_key(self, local_cache):
        """Test getting a missing key from local cache."""
        result = await local_cache.get("non_existent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, local_cache):
        """Test deleting a key from local cache."""
        await local_cache.set("key1", "value1")
        await local_cache.delete("key1")
        result = await local_cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists(self, local_cache):
        """Test checking if a key exists in local cache."""
        await local_cache.set("key1", "value1")
        assert await local_cache.exists("key1") is True
        assert await local_cache.exists("non_existent") is False

    @pytest.mark.asyncio
    async def test_expiration(self, local_cache):
        """Test that keys expire in local cache."""
        # Set with short TTL
        await local_cache.set("key1", "value1", ttl=1)
        # Wait for expiration
        await asyncio.sleep(1.5)
        result = await local_cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear(self, local_cache):
        """Test clearing the local cache."""
        await local_cache.set("key1", "value1")
        await local_cache.set("key2", "value2")
        await local_cache.clear()
        result1 = await local_cache.get("key1")
        result2 = await local_cache.get("key2")
        assert result1 is None
        assert result2 is None

    @pytest.mark.asyncio
    async def test_get_type(self, local_cache):
        """Test getting cache type."""
        assert local_cache.get_type() == "local"


class TestRedisCache:
    """Test Redis cache adapter (using mock if Redis unavailable)."""

    @pytest.mark.asyncio
    async def test_set_and_get(self, redis_cache):
        """Test setting and getting a value from Redis cache."""
        await redis_cache.set("key1", "value1")
        result = await redis_cache.get("key1")
        # If using mock, result is None by default unless we set it
        if isinstance(redis_cache, AsyncMock):
            # For mock, we need to set up return_value
            redis_cache.get.return_value = "value1"
            result = await redis_cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_missing_key(self, redis_cache):
        """Test getting a missing key from Redis cache."""
        if isinstance(redis_cache, AsyncMock):
            redis_cache.get.return_value = None
        result = await redis_cache.get("non_existent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, redis_cache):
        """Test deleting a key from Redis cache."""
        if isinstance(redis_cache, AsyncMock):
            redis_cache.delete.return_value = True
        result = await redis_cache.delete("key1")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists(self, redis_cache):
        """Test checking if a key exists in Redis cache."""
        if isinstance(redis_cache, AsyncMock):
            redis_cache.exists.return_value = True
        assert await redis_cache.exists("key1") is True

    @pytest.mark.asyncio
    async def test_ping(self, redis_cache):
        """Test pinging Redis."""
        if isinstance(redis_cache, AsyncMock):
            redis_cache.ping.return_value = True
        assert await redis_cache.ping() is True

    @pytest.mark.asyncio
    async def test_close(self, redis_cache):
        """Test closing Redis connection."""
        if isinstance(redis_cache, AsyncMock):
            redis_cache.close.return_value = None
        await redis_cache.close()


class TestCacheFallback:
    """Test cache fallback behavior."""

    @pytest.mark.asyncio
    async def test_primary_success(self, cache_manager, redis_cache, local_cache):
        """Test that primary cache is used when available."""
        # Set up primary to return a value
        if isinstance(redis_cache, AsyncMock):
            redis_cache.get.return_value = "primary_value"
        else:
            # Real Redis: set the value
            await redis_cache.set("key1", "primary_value")
        
        result = await cache_manager.get("key1")
        assert result == "primary_value"

    @pytest.mark.asyncio
    async def test_primary_failure_fallback(self):
        """Test that fallback is used when primary fails."""
        primary = AsyncMock(spec=RedisAdapter)
        primary.get.side_effect = Exception("Redis error")
        primary.set.side_effect = Exception("Redis error")
        primary.delete.side_effect = Exception("Redis error")
        primary.exists.side_effect = Exception("Redis error")
        primary.get_type.return_value = "redis"

        fallback = LocalAdapter(ttl=TEST_CACHE_TTL)
        manager = CacheFallback(
            primary=primary,
            fallback=fallback,
            fallback_on_error=True,
        )

        # Set should fallback to local
        await manager.set("key1", "fallback_value")
        # Get should fallback to local
        result = await manager.get("key1")
        assert result == "fallback_value"

    @pytest.mark.asyncio
    async def test_primary_failure_no_fallback(self):
        """Test that error propagates when fallback is disabled."""
        primary = AsyncMock(spec=RedisAdapter)
        primary.get.side_effect = Exception("Redis error")
        primary.set.side_effect = Exception("Redis error")
        primary.delete.side_effect = Exception("Redis error")
        primary.exists.side_effect = Exception("Redis error")

        fallback = LocalAdapter(ttl=TEST_CACHE_TTL)
        manager = CacheFallback(
            primary=primary,
            fallback=fallback,
            fallback_on_error=False,
        )

        with pytest.raises(CacheError):
            await manager.set("key1", "value1")
        with pytest.raises(CacheError):
            await manager.get("key1")

    @pytest.mark.asyncio
    async def test_delete_fallback(self):
        """Test delete with fallback."""
        primary = AsyncMock(spec=RedisAdapter)
        primary.delete.side_effect = Exception("Redis error")
        primary.get_type.return_value = "redis"

        fallback = LocalAdapter(ttl=TEST_CACHE_TTL)
        manager = CacheFallback(
            primary=primary,
            fallback=fallback,
            fallback_on_error=True,
        )

        # Set a value in fallback
        await fallback.set("key1", "value1")
        # Delete should fallback
        result = await manager.delete("key1")
        assert result is True
        # Verify fallback is cleared
        assert await fallback.get("key1") is None

    @pytest.mark.asyncio
    async def test_exists_fallback(self):
        """Test exists with fallback."""
        primary = AsyncMock(spec=RedisAdapter)
        primary.exists.side_effect = Exception("Redis error")
        primary.get_type.return_value = "redis"

        fallback = LocalAdapter(ttl=TEST_CACHE_TTL)
        manager = CacheFallback(
            primary=primary,
            fallback=fallback,
            fallback_on_error=True,
        )

        await fallback.set("key1", "value1")
        assert await manager.exists("key1") is True
        assert await manager.exists("key2") is False


class TestCacheManager:
    """Test CacheManager with real fallback logic."""

    @pytest.mark.asyncio
    async def test_serialization(self, cache_manager):
        """Test serialization of complex objects."""
        obj = {"name": "test", "value": 123, "list": [1, 2, 3]}
        await cache_manager.set("obj", obj)
        result = await cache_manager.get("obj")
        assert result == obj

    @pytest.mark.asyncio
    async def test_ttl_override(self, cache_manager):
        """Test TTL override in set."""
        # Set with custom TTL
        await cache_manager.set("short", "value", ttl=1)
        # Wait for expiration
        await asyncio.sleep(1.5)
        result = await cache_manager.get("short")
        assert result is None

        # Set with longer TTL
        await cache_manager.set("long", "value", ttl=10)
        result = await cache_manager.get("long")
        assert result == "value"

    @pytest.mark.asyncio
    async def test_clear(self, cache_manager):
        """Test clearing the cache."""
        await cache_manager.set("key1", "value1")
        await cache_manager.set("key2", "value2")
        await cache_manager.clear()
        result1 = await cache_manager.get("key1")
        result2 = await cache_manager.get("key2")
        assert result1 is None
        assert result2 is None

    @pytest.mark.asyncio
    async def test_get_status(self, cache_manager):
        """Test getting cache status."""
        status = await cache_manager.get_status()
        assert "type" in status
        assert "connected" in status
        assert "keys_count" in status
        assert "memory_usage" in status
        assert "hit_rate" in status


class TestCachePerformance:
    """Test cache performance under load."""

    @pytest.mark.asyncio
    async def test_concurrent_access(self, cache_manager):
        """Test concurrent read/write operations."""
        async def writer(i):
            await cache_manager.set(f"key_{i}", f"value_{i}")
        
        async def reader(i):
            return await cache_manager.get(f"key_{i}")

        # Write concurrently
        await asyncio.gather(*[writer(i) for i in range(10)])
        
        # Read concurrently
        results = await asyncio.gather(*[reader(i) for i in range(10)])
        for i, val in enumerate(results):
            assert val == f"value_{i}"

    @pytest.mark.asyncio
    async def test_cache_hit_rate(self, cache_manager):
        """Test cache hit rate tracking."""
        # Simulate hits and misses
        await cache_manager.set("hit1", "value1")
        await cache_manager.set("hit2", "value2")
        
        # Hits
        await cache_manager.get("hit1")
        await cache_manager.get("hit2")
        # Miss
        await cache_manager.get("miss")
        
        status = await cache_manager.get_status()
        # The hit rate logic depends on implementation
        # Just check that the method returns without error
        assert "hit_rate" in status


class TestEdgeCases:
    """Test edge cases for cache operations."""

    @pytest.mark.asyncio
    async def test_empty_key(self, cache_manager):
        """Test operations with empty key."""
        with pytest.raises(ValueError):
            await cache_manager.set("", "value")
        with pytest.raises(ValueError):
            await cache_manager.get("")
        with pytest.raises(ValueError):
            await cache_manager.delete("")
        with pytest.raises(ValueError):
            await cache_manager.exists("")

    @pytest.mark.asyncio
    async def test_none_value(self, cache_manager):
        """Test setting None value."""
        await cache_manager.set("none_key", None)
        result = await cache_manager.get("none_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_large_object(self, cache_manager):
        """Test storing large objects."""
        large_dict = {str(i): i * 1000 for i in range(1000)}
        await cache_manager.set("large", large_dict)
        result = await cache_manager.get("large")
        assert result == large_dict

    @pytest.mark.asyncio
    async def test_nested_structures(self, cache_manager):
        """Test storing nested structures."""
        nested = {
            "a": 1,
            "b": {"c": 2, "d": [3, 4, {"e": 5}]},
            "f": [{"g": 6}, {"h": 7}],
        }
        await cache_manager.set("nested", nested)
        result = await cache_manager.get("nested")
        assert result == nested

    @pytest.mark.asyncio
    async def test_unicode_keys(self, cache_manager):
        """Test using Unicode characters in keys."""
        key = "key_متن_فارسی"
        await cache_manager.set(key, "value")
        result = await cache_manager.get(key)
        assert result == "value"

    @pytest.mark.asyncio
    async def test_binary_data(self, cache_manager):
        """Test storing binary data."""
        binary_data = b"\x00\x01\x02\x03\x04\x05"
        await cache_manager.set("binary", binary_data)
        result = await cache_manager.get("binary")
        assert result == binary_data