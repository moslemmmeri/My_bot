# my_bot_project/src/my_bot/infrastructure/cache/redis_adapter.py
"""
آداپتور Redis برای سیستم کش.

این کلاس پیاده‌سازی عینی از اینترفیس CacheInterface است که با استفاده
از کتابخانه redis-py (redis.asyncio) و Connection Pool، عملیات کش
را روی Redis انجام می‌دهد.
"""

import json
import asyncio
from typing import Optional, Any, Dict, List, Union

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from redis.exceptions import RedisError, TimeoutError, ConnectionError

from my_bot.core.config.redis_config import RedisConfig
from my_bot.core.exceptions.cache_errors import (
    CacheError,
    CacheConnectionError,
    CacheOperationError,
    CachePoolError,
    CacheTimeoutError,
)
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface

logger = get_logger(__name__)


class RedisAdapter(CacheInterface):
    """
    آداپتور Redis با پشتیبانی از Connection Pool.

    این کلاس پیاده‌سازی عینی از CacheInterface است که با Redis ارتباط برقرار می‌کند
    و از Connection Pool برای مدیریت اتصالات استفاده می‌نماید.

    Attributes:
        config: پیکربندی Redis.
        client: کلاینت Redis.
        pool: Connection Pool.
        _is_initialized: وضعیت مقداردهی اولیه.
    """

    def __init__(self, config: RedisConfig) -> None:
        """
        مقداردهی اولیه آداپتور Redis.

        Args:
            config: پیکربندی Redis.
        """
        self.config = config
        self._client: Optional[redis.Redis] = None
        self._pool: Optional[ConnectionPool] = None
        self._is_initialized = False
        self._lock = asyncio.Lock()

        logger.info(
            f"RedisAdapter initialized with host={config.host}, port={config.port}, db={config.db}"
        )

    async def initialize(self) -> None:
        """
        مقداردهی اولیه اتصال به Redis و Connection Pool.

        Raises:
            CacheConnectionError: در صورت بروز خطا در اتصال به Redis.
        """
        if self._is_initialized:
            logger.warning("RedisAdapter already initialized.")
            return

        try:
            async with self._lock:
                if self._is_initialized:
                    return

                # ایجاد Connection Pool
                connection_params = self._get_connection_params()

                self._pool = ConnectionPool(**connection_params)

                # ایجاد کلاینت با استفاده از Pool
                self._client = redis.Redis(
                    connection_pool=self._pool,
                    decode_responses=self.config.decode_responses,
                )

                # تست اتصال
                await self._test_connection()

                self._is_initialized = True
                logger.info("RedisAdapter initialized successfully.")

        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Connection failed: {str(e)}",
            )
        except redis.TimeoutError as e:
            logger.error(f"Redis connection timeout: {e}")
            raise CacheTimeoutError(
                operation="initialize",
                key=None,
                timeout_seconds=self.config.socket_connect_timeout,
            )
        except Exception as e:
            logger.error(f"Failed to initialize RedisAdapter: {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Initialization failed: {str(e)}",
            )

    def _get_connection_params(self) -> Dict[str, Any]:
        """
        دریافت پارامترهای اتصال برای Connection Pool.

        Returns:
            دیکشنری پارامترهای اتصال.
        """
        params = {
            "host": self.config.host,
            "port": self.config.port,
            "db": self.config.db,
            "max_connections": self.config.max_connections,
            "socket_timeout": self.config.socket_timeout,
            "socket_connect_timeout": self.config.socket_connect_timeout,
            "retry_on_timeout": self.config.retry_on_timeout,
            "health_check_interval": self.config.health_check_interval,
        }

        if self.config.password:
            params["password"] = self.config.password

        if self.config.ssl:
            params["ssl"] = True

        # اگر URL وجود دارد، از آن استفاده می‌کنیم
        if self.config.url and self.config.url.startswith("redis://"):
            # استفاده از URL به‌جای پارامترهای جداگانه
            return {
                "connection_class": redis.Connection,
                "max_connections": self.config.max_connections,
                "socket_timeout": self.config.socket_timeout,
                "socket_connect_timeout": self.config.socket_connect_timeout,
                "retry_on_timeout": self.config.retry_on_timeout,
                "health_check_interval": self.config.health_check_interval,
                "url": self.config.url,
            }

        return params

    async def _test_connection(self) -> None:
        """
        تست اتصال به Redis.

        Raises:
            CacheConnectionError: در صورت عدم موفقیت در تست اتصال.
        """
        if not self._client:
            raise CacheConnectionError(
                backend="Redis",
                reason="Client not initialized.",
            )

        try:
            # اجرای یک دستور ساده برای تست اتصال
            await self._client.ping()
            logger.debug("Redis connection test successful.")

        except redis.TimeoutError as e:
            logger.error(f"Redis ping timeout: {e}")
            raise CacheTimeoutError(
                operation="ping",
                key=None,
                timeout_seconds=self.config.socket_timeout,
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis ping failed: {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Ping failed: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Test failed: {str(e)}",
            )

    async def _ensure_initialized(self) -> None:
        """
        اطمینان از مقداردهی اولیه آداپتور.

        Raises:
            CacheConnectionError: در صورت عدم مقداردهی.
        """
        if not self._is_initialized:
            await self.initialize()

        if not self._client:
            raise CacheConnectionError(
                backend="Redis",
                reason="Client not initialized.",
            )

    async def get(self, key: str) -> Optional[Any]:
        """
        دریافت یک مقدار از Redis.

        Args:
            key: کلید مورد نظر.

        Returns:
            مقدار ذخیره‌شده در صورت وجود، در غیر این صورت None.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        await self._ensure_initialized()

        try:
            value = await self._client.get(key)
            if value is None:
                return None

            # تلاش برای دیسریال‌سازی JSON
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return value

        except redis.TimeoutError as e:
            logger.error(f"Redis GET timeout for key '{key}': {e}")
            raise CacheTimeoutError(
                operation="get",
                key=key,
                timeout_seconds=self.config.socket_timeout,
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on GET for key '{key}': {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Connection error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error getting key '{key}' from Redis: {e}")
            raise CacheOperationError(
                operation="get",
                key=key,
                reason=str(e),
            )

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """
        ذخیره یک مقدار در Redis.

        Args:
            key: کلید برای ذخیره‌سازی.
            value: مقدار برای ذخیره‌سازی.
            ttl: زمان انقضا بر حسب ثانیه (اختیاری).

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        await self._ensure_initialized()

        try:
            # سریال‌سازی JSON
            serialized = self._serialize_value(value)

            if ttl is not None and ttl > 0:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)

        except redis.TimeoutError as e:
            logger.error(f"Redis SET timeout for key '{key}': {e}")
            raise CacheTimeoutError(
                operation="set",
                key=key,
                timeout_seconds=self.config.socket_timeout,
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on SET for key '{key}': {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Connection error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error setting key '{key}' in Redis: {e}")
            raise CacheOperationError(
                operation="set",
                key=key,
                reason=str(e),
            )

    async def delete(self, key: str) -> bool:
        """
        حذف یک کلید از Redis.

        Args:
            key: کلید برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود کلید.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        await self._ensure_initialized()

        try:
            result = await self._client.delete(key)
            return result > 0

        except redis.TimeoutError as e:
            logger.error(f"Redis DELETE timeout for key '{key}': {e}")
            raise CacheTimeoutError(
                operation="delete",
                key=key,
                timeout_seconds=self.config.socket_timeout,
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on DELETE for key '{key}': {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Connection error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error deleting key '{key}' from Redis: {e}")
            raise CacheOperationError(
                operation="delete",
                key=key,
                reason=str(e),
            )

    async def exists(self, key: str) -> bool:
        """
        بررسی وجود یک کلید در Redis.

        Args:
            key: کلید مورد نظر.

        Returns:
            True اگر کلید وجود داشته باشد، در غیر این صورت False.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        await self._ensure_initialized()

        try:
            result = await self._client.exists(key)
            return result > 0

        except redis.TimeoutError as e:
            logger.error(f"Redis EXISTS timeout for key '{key}': {e}")
            raise CacheTimeoutError(
                operation="exists",
                key=key,
                timeout_seconds=self.config.socket_timeout,
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on EXISTS for key '{key}': {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Connection error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error checking existence of key '{key}' in Redis: {e}")
            raise CacheOperationError(
                operation="exists",
                key=key,
                reason=str(e),
            )

    async def clear(self) -> None:
        """
        پاک کردن تمام کلیدها از Redis.

        توجه: این عملیات کل دیتابیس Redis را پاک می‌کند (FLUSHDB).

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        await self._ensure_initialized()

        try:
            await self._client.flushdb()
            logger.info("Redis cache cleared (FLUSHDB).")

        except redis.TimeoutError as e:
            logger.error(f"Redis FLUSHDB timeout: {e}")
            raise CacheTimeoutError(
                operation="flushdb",
                key=None,
                timeout_seconds=self.config.socket_timeout,
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on FLUSHDB: {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Connection error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error clearing Redis cache: {e}")
            raise CacheOperationError(
                operation="clear",
                key=None,
                reason=str(e),
            )

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        دریافت زمان باقی‌مانده تا انقضای یک کلید در Redis.

        Args:
            key: کلید مورد نظر.

        Returns:
            زمان باقی‌مانده بر حسب ثانیه، یا None اگر کلید وجود نداشته باشد
            یا بدون انقضا باشد (TTL=-1).

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        await self._ensure_initialized()

        try:
            ttl = await self._client.ttl(key)
            if ttl == -2:  # کلید وجود ندارد
                return None
            if ttl == -1:  # بدون انقضا
                return None
            return ttl

        except redis.TimeoutError as e:
            logger.error(f"Redis TTL timeout for key '{key}': {e}")
            raise CacheTimeoutError(
                operation="ttl",
                key=key,
                timeout_seconds=self.config.socket_timeout,
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on TTL for key '{key}': {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Connection error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error getting TTL for key '{key}' in Redis: {e}")
            raise CacheOperationError(
                operation="get_ttl",
                key=key,
                reason=str(e),
            )

    async def set_ttl(self, key: str, ttl: int) -> bool:
        """
        تنظیم زمان انقضای جدید برای یک کلید در Redis.

        Args:
            key: کلید مورد نظر.
            ttl: زمان انقضا بر حسب ثانیه.

        Returns:
            True در صورت موفقیت، False در صورت عدم وجود کلید.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        await self._ensure_initialized()

        try:
            result = await self._client.expire(key, ttl)
            return result

        except redis.TimeoutError as e:
            logger.error(f"Redis EXPIRE timeout for key '{key}': {e}")
            raise CacheTimeoutError(
                operation="expire",
                key=key,
                timeout_seconds=self.config.socket_timeout,
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on EXPIRE for key '{key}': {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Connection error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error setting TTL for key '{key}' in Redis: {e}")
            raise CacheOperationError(
                operation="set_ttl",
                key=key,
                reason=str(e),
            )

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        افزایش مقدار یک کلید عددی در Redis (اتمیک).

        Args:
            key: کلید مورد نظر.
            amount: مقدار افزایش (پیش‌فرض ۱).

        Returns:
            مقدار جدید در صورت موفقیت، یا None اگر کلید وجود نداشته باشد.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        await self._ensure_initialized()

        try:
            # بررسی وجود کلید
            exists = await self.exists(key)
            if not exists:
                return None

            result = await self._client.incrby(key, amount)
            return result

        except redis.TimeoutError as e:
            logger.error(f"Redis INCRBY timeout for key '{key}': {e}")
            raise CacheTimeoutError(
                operation="incrby",
                key=key,
                timeout_seconds=self.config.socket_timeout,
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on INCRBY for key '{key}': {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Connection error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error incrementing key '{key}' in Redis: {e}")
            raise CacheOperationError(
                operation="increment",
                key=key,
                reason=str(e),
            )

    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        کاهش مقدار یک کلید عددی در Redis (اتمیک).

        Args:
            key: کلید مورد نظر.
            amount: مقدار کاهش (پیش‌فرض ۱).

        Returns:
            مقدار جدید در صورت موفقیت، یا None اگر کلید وجود نداشته باشد.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        await self._ensure_initialized()

        try:
            # بررسی وجود کلید
            exists = await self.exists(key)
            if not exists:
                return None

            result = await self._client.decrby(key, amount)
            return result

        except redis.TimeoutError as e:
            logger.error(f"Redis DECRBY timeout for key '{key}': {e}")
            raise CacheTimeoutError(
                operation="decrby",
                key=key,
                timeout_seconds=self.config.socket_timeout,
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on DECRBY for key '{key}': {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Connection error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error decrementing key '{key}' in Redis: {e}")
            raise CacheOperationError(
                operation="decrement",
                key=key,
                reason=str(e),
            )

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        دریافت چندین مقدار از Redis با کلیدهای مشخص.

        Args:
            keys: لیست کلیدها.

        Returns:
            دیکشنری شامل کلیدها و مقادیر موجود.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        await self._ensure_initialized()

        if not keys:
            return {}

        try:
            values = await self._client.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value is not None:
                    # تلاش برای دیسریال‌سازی JSON
                    if isinstance(value, str):
                        try:
                            result[key] = json.loads(value)
                        except json.JSONDecodeError:
                            result[key] = value
                    else:
                        result[key] = value

            return result

        except redis.TimeoutError as e:
            logger.error(f"Redis MGET timeout for {len(keys)} keys: {e}")
            raise CacheTimeoutError(
                operation="mget",
                key=None,
                timeout_seconds=self.config.socket_timeout,
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on MGET: {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Connection error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error getting many keys from Redis: {e}")
            raise CacheOperationError(
                operation="get_many",
                key=None,
                reason=str(e),
            )

    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """
        ذخیره چندین مقدار در Redis به‌صورت یکجا.

        Args:
            items: دیکشنری شامل کلیدها و مقادیر.
            ttl: زمان انقضای مشترک برای همه آیتم‌ها (اختیاری).

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        await self._ensure_initialized()

        if not items:
            return

        try:
            # سریال‌سازی مقادیر
            serialized_items = {
                key: self._serialize_value(value)
                for key, value in items.items()
            }

            # استفاده از Pipeline برای اجرای یکجا
            async with self._client.pipeline() as pipe:
                # ذخیره همه کلیدها
                pipe.mset(serialized_items)

                # تنظیم TTL برای کل کلیدها (اگر مشخص شده باشد)
                if ttl is not None and ttl > 0:
                    for key in items.keys():
                        pipe.expire(key, ttl)

                await pipe.execute()

        except redis.TimeoutError as e:
            logger.error(f"Redis MSET/EXPIRE timeout: {e}")
            raise CacheTimeoutError(
                operation="mset/expire",
                key=None,
                timeout_seconds=self.config.socket_timeout,
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on MSET/EXPIRE: {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Connection error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error setting many keys in Redis: {e}")
            raise CacheOperationError(
                operation="set_many",
                key=None,
                reason=str(e),
            )

    async def delete_many(self, keys: List[str]) -> int:
        """
        حذف چندین کلید از Redis.

        Args:
            keys: لیست کلیدها.

        Returns:
            تعداد کلیدهای حذف‌شده.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        await self._ensure_initialized()

        if not keys:
            return 0

        try:
            result = await self._client.delete(*keys)
            return result

        except redis.TimeoutError as e:
            logger.error(f"Redis DELETE timeout for {len(keys)} keys: {e}")
            raise CacheTimeoutError(
                operation="delete",
                key=None,
                timeout_seconds=self.config.socket_timeout,
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on DELETE: {e}")
            raise CacheConnectionError(
                backend="Redis",
                reason=f"Connection error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error deleting many keys from Redis: {e}")
            raise CacheOperationError(
                operation="delete_many",
                key=None,
                reason=str(e),
            )

    async def health_check(self) -> bool:
        """
        بررسی سلامت Redis.

        Returns:
            True اگر Redis در دسترس و سالم باشد، در غیر این صورت False.
        """
        try:
            if not self._is_initialized:
                await self.initialize()

            if not self._client:
                return False

            await self._client.ping()
            return True

        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار Redis.

        Returns:
            دیکشنری شامل آمار Redis.
        """
        stats = {
            "available": False,
            "host": self.config.host,
            "port": self.config.port,
            "db": self.config.db,
            "initialized": self._is_initialized,
            "max_connections": self.config.max_connections,
        }

        if not self._is_initialized or not self._client:
            return stats

        try:
            # دریافت اطلاعات از Redis
            info = await self._client.info()
            stats.update({
                "available": True,
                "used_memory": info.get("used_memory_human"),
                "used_memory_peak": info.get("used_memory_peak_human"),
                "total_connections_received": info.get("total_connections_received"),
                "total_commands_processed": info.get("total_commands_processed"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
                "connected_clients": info.get("connected_clients"),
                "blocked_clients": info.get("blocked_clients"),
                "keyspace": info.get("keyspace"),
                "redis_version": info.get("redis_version"),
            })

            # دریافت تعداد کلیدها
            db_keys = await self._client.dbsize()
            stats["total_keys"] = db_keys

            # دریافت وضعیت Pool
            if self._pool:
                stats["pool"] = {
                    "max_connections": self._pool.max_connections,
                    "connection_class": str(self._pool.connection_class),
                }

        except Exception as e:
            stats["error"] = str(e)
            stats["available"] = False

        return stats

    async def get_status(self) -> Dict[str, Any]:
        """
        دریافت وضعیت اتصال Redis.

        Returns:
            دیکشنری شامل وضعیت اتصال.
        """
        status = {
            "available": False,
            "initialized": self._is_initialized,
            "host": self.config.host,
            "port": self.config.port,
        }

        if not self._is_initialized:
            status["message"] = "Not initialized"
            return status

        try:
            await self._client.ping()
            status["available"] = True
            status["message"] = "Connected"
        except Exception as e:
            status["available"] = False
            status["error"] = str(e)

        return status

    async def close(self) -> None:
        """
        بستن اتصال Redis و آزادسازی منابع.
        """
        try:
            if self._client:
                await self._client.close()
                self._client = None

            if self._pool:
                await self._pool.disconnect()
                self._pool = None

            self._is_initialized = False
            logger.info("RedisAdapter closed successfully.")

        except Exception as e:
            logger.error(f"Error closing RedisAdapter: {e}")

    def _serialize_value(self, value: Any) -> Union[str, bytes]:
        """
        سریال‌سازی مقدار برای ذخیره در Redis.

        Args:
            value: مقدار برای سریال‌سازی.

        Returns:
            مقدار سریال‌سازی‌شده (رشته یا bytes).
        """
        # اگر مقدار از نوع رشته است، بدون تغییر برگردان
        if isinstance(value, str):
            return value

        # اگر مقدار از نوع bytes است، بدون تغییر برگردان
        if isinstance(value, bytes):
            return value

        # اگر مقدار از نوع int, float, bool, list, dict, None است، به JSON تبدیل کن
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except TypeError:
            # اگر قابل سریال‌سازی نبود، به رشته تبدیل کن
            return str(value)