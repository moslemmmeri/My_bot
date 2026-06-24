# my_bot_project/src/my_bot/core/feature_flags/flag_cache.py
"""
کش کردن Feature Flags برای افزایش سرعت دسترسی.

این ماژول شامل کلاس `FlagCache` است که با استفاده از Redis یا Local Cache
وضعیت ویژگی‌ها را کش می‌کند و از Fallback خودکار پشتیبانی می‌کند.
"""

import json
from typing import Any, Dict, Optional

from my_bot.core.exceptions.cache_errors import CacheError, CacheOperationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class FlagCache:
    """
    کش برای Feature Flags با پشتیبانی از Redis و Local Fallback.

    این کلاس با استفاده از یک کش (Redis یا Local) وضعیت ویژگی‌ها را ذخیره
    و بازیابی می‌کند. در صورت عدم دسترسی به Redis، به‌صورت خودکار
    به Local Cache Fallback می‌کند.

    Attributes:
        cache_adapter: آداپتور کش (Redis یا Local).
        fallback_enabled: فعال بودن Fallback به Local.
        _local_cache: کش محلی برای Fallback.
        ttl: زمان انقضای کش بر حسب ثانیه.
    """

    def __init__(
        self,
        cache_adapter,
        fallback_enabled: bool = True,
        ttl: int = 300,
        local_cache_max_size: int = 100,
    ) -> None:
        """
        مقداردهی اولیه کش.

        Args:
            cache_adapter: آداپتور کش (معمولاً RedisAdapter یا LocalAdapter).
            fallback_enabled: فعال بودن Fallback به Local (پیش‌فرض True).
            ttl: زمان انقضای کش بر حسب ثانیه (پیش‌فرض ۳۰۰).
            local_cache_max_size: حداکثر اندازهٔ کش محلی (پیش‌فرض ۱۰۰).
        """
        self._cache_adapter = cache_adapter
        self._fallback_enabled = fallback_enabled
        self._ttl = ttl
        self._local_cache: Dict[str, Dict[str, Any]] = {}
        self._local_cache_max_size = local_cache_max_size
        self._redis_available = True

        # لاگ برای تشخیص نوع کش
        cache_type = getattr(cache_adapter, "__class__.__name__", "Unknown")
        logger.info(f"FlagCache initialized with adapter: {cache_type}, fallback={fallback_enabled}")

    async def get(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات یک ویژگی از کش.

        Args:
            feature_name: نام ویژگی.

        Returns:
            دیکشنری اطلاعات ویژگی یا None در صورت عدم وجود.

        Raises:
            CacheOperationError: در صورت بروز خطا در کش (غیر از عدم وجود کلید).
        """
        # تلاش برای دریافت از کش اصلی (Redis)
        if self._redis_available:
            try:
                value = await self._cache_adapter.get(self._get_key(feature_name))
                if value is not None:
                    # دیسریال‌سازی JSON
                    if isinstance(value, str):
                        try:
                            return json.loads(value)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in cache for '{feature_name}'")
                            return None
                    return value
            except Exception as e:
                logger.warning(f"Redis error in get('{feature_name}'): {e}")
                self._redis_available = False
                # Fallback به Local
                if self._fallback_enabled:
                    logger.info(f"Falling back to local cache for '{feature_name}'")
                    return self._get_local(feature_name)
                # اگر Fallback غیرفعال باشد، خطا را propagate می‌کنیم
                raise CacheOperationError(
                    "get",
                    feature_name,
                    f"Redis error and fallback disabled: {e}"
                )

        # اگر Redis در دسترس نباشد، از Local استفاده می‌کنیم
        if self._fallback_enabled:
            return self._get_local(feature_name)

        return None

    async def set(self, feature_name: str, data: Dict[str, Any]) -> None:
        """
        ذخیره اطلاعات یک ویژگی در کش.

        Args:
            feature_name: نام ویژگی.
            data: دیکشنری اطلاعات ویژگی.

        Raises:
            CacheOperationError: در صورت بروز خطا در کش.
        """
        # سریال‌سازی داده‌ها به JSON
        try:
            serialized = json.dumps(data, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error serializing data for '{feature_name}': {e}")
            raise CacheOperationError("set", feature_name, f"Serialization error: {e}")

        # ذخیره در کش اصلی (Redis)
        if self._redis_available:
            try:
                await self._cache_adapter.set(
                    self._get_key(feature_name),
                    serialized,
                    ttl=self._ttl
                )
                # همچنین در Local نیز ذخیره می‌کنیم تا در صورت Fallback در دسترس باشد
                if self._fallback_enabled:
                    self._set_local(feature_name, data)
                return
            except Exception as e:
                logger.warning(f"Redis error in set('{feature_name}'): {e}")
                self._redis_available = False
                # Fallback به Local
                if self._fallback_enabled:
                    logger.info(f"Falling back to local cache for '{feature_name}'")
                    self._set_local(feature_name, data)
                    return
                # اگر Fallback غیرفعال باشد، خطا را propagate می‌کنیم
                raise CacheOperationError(
                    "set",
                    feature_name,
                    f"Redis error and fallback disabled: {e}"
                )

        # اگر Redis در دسترس نباشد، از Local استفاده می‌کنیم
        if self._fallback_enabled:
            self._set_local(feature_name, data)
        else:
            raise CacheOperationError("set", feature_name, "Cache not available")

    async def delete(self, feature_name: str) -> None:
        """
        حذف یک ویژگی از کش.

        Args:
            feature_name: نام ویژگی.

        Raises:
            CacheOperationError: در صورت بروز خطا در کش.
        """
        # حذف از کش اصلی
        if self._redis_available:
            try:
                await self._cache_adapter.delete(self._get_key(feature_name))
            except Exception as e:
                logger.warning(f"Redis error in delete('{feature_name}'): {e}")
                self._redis_available = False

        # حذف از Local (اگر Fallback فعال باشد)
        if self._fallback_enabled:
            self._delete_local(feature_name)

    async def clear(self) -> None:
        """
        پاک کردن تمام کش (هم Redis و هم Local).

        Raises:
            CacheOperationError: در صورت بروز خطا در کش.
        """
        # پاک کردن کش اصلی
        if self._redis_available:
            try:
                # توجه: باید الگوی کلیدها را بدانیم (مثلاً feature_flags:*)
                pattern = self._get_key("*")
                await self._cache_adapter.delete_pattern(pattern)
            except Exception as e:
                logger.warning(f"Redis error in clear(): {e}")
                self._redis_available = False

        # پاک کردن Local
        if self._fallback_enabled:
            self._local_cache.clear()
            logger.info("Local flag cache cleared.")

    def _get_key(self, feature_name: str) -> str:
        """تولید کلید مناسب برای کش."""
        return f"feature_flags:{feature_name}"

    def _get_local(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """
        دریافت از کش محلی.
        """
        data = self._local_cache.get(feature_name)
        if data is not None:
            # بررسی زمان انقضا (اگر ذخیره شده باشد)
            if "cached_at" in data:
                import time
                if time.time() - data["cached_at"] > self._ttl:
                    # منقضی شده
                    self._delete_local(feature_name)
                    return None
            return data
        return None

    def _set_local(self, feature_name: str, data: Dict[str, Any]) -> None:
        """
        ذخیره در کش محلی.
        """
        # مدیریت اندازهٔ کش
        if len(self._local_cache) >= self._local_cache_max_size:
            # حذف قدیمی‌ترین آیتم (با استفاده از کلید تصادفی ساده)
            oldest_key = next(iter(self._local_cache))
            self._delete_local(oldest_key)

        # افزودن زمان ذخیره‌سازی برای بررسی انقضا
        import time
        data_copy = data.copy()
        data_copy["cached_at"] = time.time()
        self._local_cache[feature_name] = data_copy

    def _delete_local(self, feature_name: str) -> None:
        """
        حذف از کش محلی.
        """
        if feature_name in self._local_cache:
            del self._local_cache[feature_name]

    async def is_redis_available(self) -> bool:
        """
        بررسی در دسترس بودن Redis.

        Returns:
            True اگر Redis در دسترس باشد.
        """
        if not self._redis_available:
            return False

        try:
            # سعی می‌کنیم یک کلید تست را set و get کنیم
            await self._cache_adapter.set("_test_key", "ok", ttl=1)
            result = await self._cache_adapter.get("_test_key")
            await self._cache_adapter.delete("_test_key")
            return result == "ok"
        except Exception:
            self._redis_available = False
            return False

    async def get_ttl(self) -> int:
        """
        دریافت زمان انقضای کش.

        Returns:
            زمان انقضا بر حسب ثانیه.
        """
        return self._ttl

    async def set_ttl(self, ttl: int) -> None:
        """
        تنظیم زمان انقضای کش (برای آیتم‌های جدید).

        Args:
            ttl: زمان انقضا بر حسب ثانیه.
        """
        if ttl < 0:
            raise ValueError("TTL cannot be negative")
        self._ttl = ttl
        logger.info(f"Flag cache TTL set to {ttl} seconds")

    async def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار کش.

        Returns:
            دیکشنری شامل آمار (نوع کش، تعداد آیتم‌ها، وضعیت Redis, ...).
        """
        stats = {
            "redis_available": self._redis_available,
            "fallback_enabled": self._fallback_enabled,
            "ttl": self._ttl,
            "local_cache_size": len(self._local_cache),
            "local_cache_max_size": self._local_cache_max_size,
        }

        # تلاش برای دریافت آمار از Redis
        if self._redis_available:
            try:
                # می‌توانیم از INFO یا DBSIZE استفاده کنیم
                info = await self._cache_adapter.info()
                stats["redis_info"] = {
                    "used_memory": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "total_commands_processed": info.get("total_commands_processed"),
                }
            except Exception as e:
                stats["redis_error"] = str(e)

        return stats