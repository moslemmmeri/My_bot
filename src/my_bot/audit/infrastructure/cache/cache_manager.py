# my_bot_project/src/my_bot/infrastructure/cache/cache_manager.py
"""
مدیریت کش (Cache Manager).

این کلاس مسئولیت مدیریت عملیات کش را با پشتیبانی از Fallback خودکار
بین Redis و Local Cache بر عهده دارد. از آداپتورهای مختلف کش استفاده می‌کند
و یک رابط یکپارچه برای ذخیره‌سازی و بازیابی داده‌ها فراهم می‌آورد.
"""

import json
import asyncio
from typing import Optional, Any, Dict, List, Union
from datetime import datetime

from my_bot.core.exceptions.cache_errors import (
    CacheError,
    CacheOperationError,
    CacheBackendError,
)
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface
from my_bot.infrastructure.cache.redis_adapter import RedisAdapter
from my_bot.infrastructure.cache.local_adapter import LocalAdapter
from my_bot.infrastructure.cache.cache_fallback import CacheFallback

logger = get_logger(__name__)


class CacheManager:
    """
    مدیر مرکزی کش با پشتیبانی از Fallback خودکار.

    این کلاس با استفاده از RedisAdapter و LocalAdapter، یک کش دو لایه
    ایجاد می‌کند که در صورت عدم دسترسی به Redis، به‌صورت خودکار به
    Local Cache Fallback می‌کند.

    Attributes:
        redis_adapter: آداپتور Redis (اختیاری).
        local_adapter: آداپتور کش محلی (اختیاری).
        fallback: مکانیزم Fallback خودکار.
        default_ttl: زمان انقضای پیش‌فرض بر حسب ثانیه.
        _is_initialized: وضعیت مقداردهی اولیه.
    """

    def __init__(
        self,
        redis_adapter: Optional[RedisAdapter] = None,
        local_adapter: Optional[LocalAdapter] = None,
        fallback_enabled: bool = True,
        default_ttl: int = 300,
        local_cache_max_size: int = 1000,
    ) -> None:
        """
        مقداردهی اولیه مدیر کش.

        Args:
            redis_adapter: آداپتور Redis (در صورت None، Redis غیرفعال است).
            local_adapter: آداپتور کش محلی (در صورت None، ایجاد می‌شود).
            fallback_enabled: فعال بودن Fallback به Local.
            default_ttl: زمان انقضای پیش‌فرض بر حسب ثانیه.
            local_cache_max_size: حداکثر اندازهٔ کش محلی.
        """
        self._redis_adapter = redis_adapter
        self._local_adapter = local_adapter or LocalAdapter(max_size=local_cache_max_size)
        self._fallback_enabled = fallback_enabled
        self._default_ttl = default_ttl
        self._is_initialized = False
        self._fallback: Optional[CacheFallback] = None

        # ثبت آداپتورها در Fallback
        if self._redis_adapter:
            self._fallback = CacheFallback(
                primary=self._redis_adapter,
                fallback=self._local_adapter,
                fallback_enabled=fallback_enabled,
            )
            logger.info(
                f"CacheManager initialized with Redis + Local fallback "
                f"(fallback_enabled={fallback_enabled})"
            )
        else:
            # فقط Local Cache
            self._fallback = None
            logger.info("CacheManager initialized with Local cache only (Redis disabled)")

    async def initialize(self) -> None:
        """
        مقداردهی اولیه آداپتورها.

        Raises:
            CacheBackendError: در صورت بروز خطا در مقداردهی.
        """
        if self._is_initialized:
            logger.warning("CacheManager already initialized.")
            return

        try:
            # مقداردهی Redis (در صورت وجود)
            if self._redis_adapter:
                await self._redis_adapter.initialize()

            # مقداردهی Local Cache
            await self._local_adapter.initialize()

            self._is_initialized = True
            logger.info("CacheManager initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize CacheManager: {e}")
            raise CacheBackendError(
                backend="CacheManager",
                reason=f"Initialization failed: {str(e)}",
            )

    async def get(self, key: str) -> Optional[Any]:
        """
        دریافت یک مقدار از کش.

        Args:
            key: کلید مورد نظر.

        Returns:
            مقدار ذخیره‌شده در صورت وجود، در غیر این صورت None.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            if self._fallback and self._redis_adapter:
                # استفاده از Fallback
                value = await self._fallback.get(key)
            else:
                # فقط Local Cache
                value = await self._local_adapter.get(key)

            if value is not None:
                logger.debug(f"Cache hit: key={key}")
                return value

            logger.debug(f"Cache miss: key={key}")
            return None

        except Exception as e:
            logger.error(f"Error getting key '{key}' from cache: {e}")
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
        ذخیره یک مقدار در کش.

        Args:
            key: کلید برای ذخیره‌سازی.
            value: مقدار برای ذخیره‌سازی.
            ttl: زمان انقضا بر حسب ثانیه (در صورت None، از default_ttl استفاده می‌شود).

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            ttl = ttl or self._default_ttl

            if self._fallback and self._redis_adapter:
                # استفاده از Fallback
                await self._fallback.set(key, value, ttl)
            else:
                # فقط Local Cache
                await self._local_adapter.set(key, value, ttl)

            logger.debug(f"Cache set: key={key}, ttl={ttl}")

        except Exception as e:
            logger.error(f"Error setting key '{key}' in cache: {e}")
            raise CacheOperationError(
                operation="set",
                key=key,
                reason=str(e),
            )

    async def delete(self, key: str) -> bool:
        """
        حذف یک کلید از کش.

        Args:
            key: کلید برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود کلید.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            if self._fallback and self._redis_adapter:
                result = await self._fallback.delete(key)
            else:
                result = await self._local_adapter.delete(key)

            if result:
                logger.debug(f"Cache delete: key={key}")
            else:
                logger.debug(f"Cache delete failed (key not found): key={key}")

            return result

        except Exception as e:
            logger.error(f"Error deleting key '{key}' from cache: {e}")
            raise CacheOperationError(
                operation="delete",
                key=key,
                reason=str(e),
            )

    async def exists(self, key: str) -> bool:
        """
        بررسی وجود یک کلید در کش.

        Args:
            key: کلید مورد نظر.

        Returns:
            True اگر کلید وجود داشته باشد، در غیر این صورت False.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            if self._fallback and self._redis_adapter:
                return await self._fallback.exists(key)
            else:
                return await self._local_adapter.exists(key)

        except Exception as e:
            logger.error(f"Error checking existence of key '{key}': {e}")
            raise CacheOperationError(
                operation="exists",
                key=key,
                reason=str(e),
            )

    async def clear(self) -> None:
        """
        پاک کردن تمام کلیدها از کش.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            if self._fallback and self._redis_adapter:
                await self._fallback.clear()
            else:
                await self._local_adapter.clear()

            logger.info("Cache cleared.")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            raise CacheOperationError(
                operation="clear",
                key=None,
                reason=str(e),
            )

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        دریافت زمان باقی‌مانده تا انقضای یک کلید.

        Args:
            key: کلید مورد نظر.

        Returns:
            زمان باقی‌مانده بر حسب ثانیه، یا None اگر کلید وجود نداشته باشد.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            if self._fallback and self._redis_adapter:
                return await self._fallback.get_ttl(key)
            else:
                return await self._local_adapter.get_ttl(key)

        except Exception as e:
            logger.error(f"Error getting TTL for key '{key}': {e}")
            raise CacheOperationError(
                operation="get_ttl",
                key=key,
                reason=str(e),
            )

    async def set_ttl(self, key: str, ttl: int) -> bool:
        """
        تنظیم زمان انقضای جدید برای یک کلید.

        Args:
            key: کلید مورد نظر.
            ttl: زمان انقضا بر حسب ثانیه.

        Returns:
            True در صورت موفقیت، False در صورت عدم وجود کلید.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            if self._fallback and self._redis_adapter:
                return await self._fallback.set_ttl(key, ttl)
            else:
                return await self._local_adapter.set_ttl(key, ttl)

        except Exception as e:
            logger.error(f"Error setting TTL for key '{key}': {e}")
            raise CacheOperationError(
                operation="set_ttl",
                key=key,
                reason=str(e),
            )

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        افزایش مقدار یک کلید عددی در کش (اتمیک).

        Args:
            key: کلید مورد نظر.
            amount: مقدار افزایش (پیش‌فرض ۱).

        Returns:
            مقدار جدید در صورت موفقیت، یا None اگر کلید وجود نداشته باشد.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            if self._fallback and self._redis_adapter:
                return await self._fallback.increment(key, amount)
            else:
                return await self._local_adapter.increment(key, amount)

        except Exception as e:
            logger.error(f"Error incrementing key '{key}': {e}")
            raise CacheOperationError(
                operation="increment",
                key=key,
                reason=str(e),
            )

    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        کاهش مقدار یک کلید عددی در کش (اتمیک).

        Args:
            key: کلید مورد نظر.
            amount: مقدار کاهش (پیش‌فرض ۱).

        Returns:
            مقدار جدید در صورت موفقیت، یا None اگر کلید وجود نداشته باشد.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            if self._fallback and self._redis_adapter:
                return await self._fallback.decrement(key, amount)
            else:
                return await self._local_adapter.decrement(key, amount)

        except Exception as e:
            logger.error(f"Error decrementing key '{key}': {e}")
            raise CacheOperationError(
                operation="decrement",
                key=key,
                reason=str(e),
            )

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        دریافت چندین مقدار از کش با کلیدهای مشخص.

        Args:
            keys: لیست کلیدها.

        Returns:
            دیکشنری شامل کلیدها و مقادیر موجود.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            if self._fallback and self._redis_adapter:
                return await self._fallback.get_many(keys)
            else:
                return await self._local_adapter.get_many(keys)

        except Exception as e:
            logger.error(f"Error getting many keys from cache: {e}")
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
        ذخیره چندین مقدار در کش به‌صورت یکجا.

        Args:
            items: دیکشنری شامل کلیدها و مقادیر.
            ttl: زمان انقضای مشترک برای همه آیتم‌ها (اختیاری).

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            ttl = ttl or self._default_ttl

            if self._fallback and self._redis_adapter:
                await self._fallback.set_many(items, ttl)
            else:
                await self._local_adapter.set_many(items, ttl)

            logger.debug(f"Cache set_many: {len(items)} items, ttl={ttl}")

        except Exception as e:
            logger.error(f"Error setting many keys in cache: {e}")
            raise CacheOperationError(
                operation="set_many",
                key=None,
                reason=str(e),
            )

    async def delete_many(self, keys: List[str]) -> int:
        """
        حذف چندین کلید از کش.

        Args:
            keys: لیست کلیدها.

        Returns:
            تعداد کلیدهای حذف‌شده.

        Raises:
            CacheOperationError: در صورت بروز خطا در عملیات.
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            if self._fallback and self._redis_adapter:
                return await self._fallback.delete_many(keys)
            else:
                return await self._local_adapter.delete_many(keys)

        except Exception as e:
            logger.error(f"Error deleting many keys from cache: {e}")
            raise CacheOperationError(
                operation="delete_many",
                key=None,
                reason=str(e),
            )

    async def health_check(self) -> bool:
        """
        بررسی سلامت سرویس کش.

        Returns:
            True اگر کش در دسترس و سالم باشد، در غیر این صورت False.
        """
        if not self._is_initialized:
            try:
                await self.initialize()
            except Exception:
                return False

        try:
            # تست با یک کلید موقت
            test_key = "_health_check"
            test_value = "ok"
            await self.set(test_key, test_value, ttl=1)
            result = await self.get(test_key)
            await self.delete(test_key)
            return result == test_value

        except Exception as e:
            logger.warning(f"Cache health check failed: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار کش.

        Returns:
            دیکشنری شامل آمار کش.
        """
        stats = {
            "initialized": self._is_initialized,
            "fallback_enabled": self._fallback_enabled,
            "default_ttl": self._default_ttl,
            "redis_enabled": self._redis_adapter is not None,
        }

        # آمار از آداپتورها
        if self._redis_adapter:
            try:
                redis_stats = await self._redis_adapter.get_stats()
                stats["redis"] = redis_stats
            except Exception as e:
                stats["redis_error"] = str(e)

        try:
            local_stats = await self._local_adapter.get_stats()
            stats["local"] = local_stats
        except Exception as e:
            stats["local_error"] = str(e)

        return stats

    async def close(self) -> None:
        """
        بستن تمام اتصالات و آزادسازی منابع.
        """
        try:
            if self._redis_adapter:
                await self._redis_adapter.close()

            await self._local_adapter.close()
            self._is_initialized = False
            logger.info("CacheManager closed successfully.")

        except Exception as e:
            logger.error(f"Error closing CacheManager: {e}")

    async def get_redis_status(self) -> Dict[str, Any]:
        """
        دریافت وضعیت Redis.

        Returns:
            دیکشنری شامل وضعیت Redis.
        """
        if not self._redis_adapter:
            return {"available": False, "message": "Redis not configured"}

        try:
            return await self._redis_adapter.get_status()
        except Exception as e:
            return {"available": False, "error": str(e)}

    def set_default_ttl(self, ttl: int) -> None:
        """
        تنظیم زمان انقضای پیش‌فرض.

        Args:
            ttl: زمان انقضا بر حسب ثانیه.
        """
        if ttl < 0:
            raise ValueError("TTL cannot be negative")
        self._default_ttl = ttl
        logger.info(f"Default TTL set to {ttl} seconds")