# my_bot_project/src/my_bot/infrastructure/cache/local_adapter.py
"""
آداپتور کش محلی (Local Cache Adapter).

این کلاس پیاده‌سازی عینی از اینترفیس CacheInterface است که از حافظه داخلی
(In-Memory) برای ذخیره‌سازی داده‌ها استفاده می‌کند. این آداپتور به‌عنوان Fallback
برای زمانی که Redis در دسترس نیست استفاده می‌شود و نیازی به سرویس خارجی ندارد.
"""

import asyncio
import time
import json
from typing import Optional, Any, Dict, List, Union
from collections import OrderedDict

from my_bot.core.exceptions.cache_errors import CacheOperationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface

logger = get_logger(__name__)


class LocalCacheItem:
    """
    یک آیتم در کش محلی.

    Attributes:
        value: مقدار ذخیره‌شده.
        expires_at: زمان انقضا (timestamp) یا None در صورت عدم انقضا.
        created_at: زمان ایجاد (timestamp).
        access_count: تعداد دفعات دسترسی (برای مدیریت حافظه).
    """

    def __init__(self, value: Any, ttl: Optional[int] = None) -> None:
        """
        مقداردهی اولیه آیتم کش.

        Args:
            value: مقدار برای ذخیره‌سازی.
            ttl: زمان انقضا بر حسب ثانیه (اختیاری).
        """
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl if ttl else None
        self.access_count = 0
        self.last_access = self.created_at

    def is_expired(self) -> bool:
        """بررسی انقضای آیتم."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def touch(self) -> None:
        """به‌روزرسانی زمان دسترسی."""
        self.last_access = time.time()
        self.access_count += 1

    def get_ttl(self) -> Optional[int]:
        """
        دریافت زمان باقی‌مانده تا انقضا.

        Returns:
            زمان باقی‌مانده بر حسب ثانیه، یا None در صورت عدم انقضا یا منقضی شدن.
        """
        if self.expires_at is None:
            return None
        remaining = self.expires_at - time.time()
        return int(remaining) if remaining > 0 else None


class LocalAdapter(CacheInterface):
    """
    آداپتور کش محلی با پشتیبانی از TTL و محدودیت اندازه.

    این کلاس با استفاده از OrderedDict و قوانین LRU (Least Recently Used)،
    کش محلی را مدیریت می‌کند و از سرریز شدن حافظه جلوگیری می‌نماید.

    Attributes:
        _cache: دیکشنری نگاشت کلید به LocalCacheItem.
        _max_size: حداکثر تعداد آیتم‌ها در کش.
        _cleanup_interval: بازه زمانی پاکسازی آیتم‌های منقضی (ثانیه).
        _last_cleanup: زمان آخرین پاکسازی.
        _lock: قفل برای عملیات اتمیک.
        _is_initialized: وضعیت مقداردهی اولیه.
    """

    def __init__(
        self,
        max_size: int = 1000,
        cleanup_interval: int = 60,
    ) -> None:
        """
        مقداردهی اولیه آداپتور کش محلی.

        Args:
            max_size: حداکثر تعداد آیتم‌ها در کش.
            cleanup_interval: بازه زمانی پاکسازی آیتم‌های منقضی (ثانیه).
        """
        self._cache: Dict[str, LocalCacheItem] = OrderedDict()
        self._max_size = max_size
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()
        self._lock = asyncio.Lock()
        self._is_initialized = False

        logger.info(
            f"LocalAdapter initialized with max_size={max_size}, "
            f"cleanup_interval={cleanup_interval}s"
        )

    async def initialize(self) -> None:
        """
        مقداردهی اولیه کش محلی.

        این متد در LocalAdapter فقط وضعیت را تنظیم می‌کند و عملیات خاصی ندارد.
        """
        if self._is_initialized:
            return

        async with self._lock:
            if self._is_initialized:
                return
            self._is_initialized = True
            logger.info("LocalAdapter initialized successfully.")

    async def _ensure_initialized(self) -> None:
        """اطمینان از مقداردهی اولیه."""
        if not self._is_initialized:
            await self.initialize()

    async def _cleanup_expired(self) -> None:
        """پاکسازی آیتم‌های منقضی از کش."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        async with self._lock:
            if now - self._last_cleanup < self._cleanup_interval:
                return

            expired_keys = []
            for key, item in self._cache.items():
                if item.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

            self._last_cleanup = now

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired items from local cache")

    async def _evict_lru(self) -> None:
        """
        حذف قدیمی‌ترین آیتم‌های استفاده‌شده (LRU) در صورت پر شدن کش.
        """
        if len(self._cache) < self._max_size:
            return

        # یافتن قدیمی‌ترین آیتم بر اساس آخرین دسترسی
        # (OrderedDict به‌صورت پیش‌فرض بر اساس زمان درج مرتب می‌شود)
        # اما ما بر اساس last_access مرتب می‌کنیم
        if not self._cache:
            return

        # مرتب‌سازی بر اساس last_access و حذف قدیمی‌ترین
        items = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_access
        )

        # حذف ۱۰٪ از آیتم‌های قدیمی
        remove_count = max(1, int(len(self._cache) * 0.1))
        for key, _ in items[:remove_count]:
            del self._cache[key]

        logger.debug(f"Evicted {remove_count} LRU items from local cache")

    async def get(self, key: str) -> Optional[Any]:
        """
        دریافت یک مقدار از کش محلی.

        Args:
            key: کلید مورد نظر.

        Returns:
            مقدار ذخیره‌شده در صورت وجود، در غیر این صورت None.
        """
        await self._ensure_initialized()

        async with self._lock:
            item = self._cache.get(key)

            if item is None:
                return None

            # بررسی انقضا
            if item.is_expired():
                del self._cache[key]
                return None

            # به‌روزرسانی زمان دسترسی
            item.touch()

            # جابجایی به انتهای OrderedDict (برای LRU)
            self._cache.move_to_end(key)

            return item.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """
        ذخیره یک مقدار در کش محلی.

        Args:
            key: کلید برای ذخیره‌سازی.
            value: مقدار برای ذخیره‌سازی.
            ttl: زمان انقضا بر حسب ثانیه (اختیاری).
        """
        await self._ensure_initialized()

        async with self._lock:
            # اگر کلید وجود دارد، حذف می‌کنیم تا دوباره به انتها اضافه شود
            if key in self._cache:
                del self._cache[key]

            # ایجاد آیتم جدید
            item = LocalCacheItem(value, ttl)
            self._cache[key] = item

            # اگر کش پر شد، آیتم‌های قدیمی را حذف می‌کنیم
            if len(self._cache) > self._max_size:
                await self._evict_lru()

    async def delete(self, key: str) -> bool:
        """
        حذف یک کلید از کش محلی.

        Args:
            key: کلید برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود کلید.
        """
        await self._ensure_initialized()

        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """
        بررسی وجود یک کلید در کش محلی.

        Args:
            key: کلید مورد نظر.

        Returns:
            True اگر کلید وجود داشته باشد و منقضی نشده باشد، در غیر این صورت False.
        """
        await self._ensure_initialized()

        async with self._lock:
            item = self._cache.get(key)
            if item is None:
                return False

            if item.is_expired():
                del self._cache[key]
                return False

            return True

    async def clear(self) -> None:
        """پاک کردن تمام کلیدها از کش محلی."""
        await self._ensure_initialized()

        async with self._lock:
            self._cache.clear()
            logger.info("Local cache cleared.")

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        دریافت زمان باقی‌مانده تا انقضای یک کلید.

        Args:
            key: کلید مورد نظر.

        Returns:
            زمان باقی‌مانده بر حسب ثانیه، یا None اگر کلید وجود نداشته باشد
            یا بدون انقضا باشد.
        """
        await self._ensure_initialized()

        async with self._lock:
            item = self._cache.get(key)
            if item is None:
                return None

            if item.is_expired():
                del self._cache[key]
                return None

            return item.get_ttl()

    async def set_ttl(self, key: str, ttl: int) -> bool:
        """
        تنظیم زمان انقضای جدید برای یک کلید.

        Args:
            key: کلید مورد نظر.
            ttl: زمان انقضا بر حسب ثانیه.

        Returns:
            True در صورت موفقیت، False در صورت عدم وجود کلید.
        """
        await self._ensure_initialized()

        async with self._lock:
            item = self._cache.get(key)
            if item is None:
                return False

            # به‌روزرسانی زمان انقضا
            item.expires_at = time.time() + ttl
            return True

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        افزایش مقدار یک کلید عددی در کش محلی (اتمیک).

        Args:
            key: کلید مورد نظر.
            amount: مقدار افزایش (پیش‌فرض ۱).

        Returns:
            مقدار جدید در صورت موفقیت، یا None اگر کلید وجود نداشته باشد یا عددی نباشد.
        """
        await self._ensure_initialized()

        async with self._lock:
            item = self._cache.get(key)
            if item is None:
                return None

            if item.is_expired():
                del self._cache[key]
                return None

            # بررسی عددی بودن مقدار
            try:
                current_value = int(item.value)
            except (ValueError, TypeError):
                logger.warning(f"Cannot increment non-integer value for key '{key}'")
                return None

            new_value = current_value + amount
            item.value = new_value
            item.touch()
            self._cache.move_to_end(key)

            return new_value

    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        کاهش مقدار یک کلید عددی در کش محلی (اتمیک).

        Args:
            key: کلید مورد نظر.
            amount: مقدار کاهش (پیش‌فرض ۱).

        Returns:
            مقدار جدید در صورت موفقیت، یا None اگر کلید وجود نداشته باشد یا عددی نباشد.
        """
        return await self.increment(key, -amount)

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        دریافت چندین مقدار از کش محلی با کلیدهای مشخص.

        Args:
            keys: لیست کلیدها.

        Returns:
            دیکشنری شامل کلیدها و مقادیر موجود.
        """
        await self._ensure_initialized()

        result = {}
        async with self._lock:
            for key in keys:
                item = self._cache.get(key)
                if item is None:
                    continue

                if item.is_expired():
                    del self._cache[key]
                    continue

                item.touch()
                self._cache.move_to_end(key)
                result[key] = item.value

        return result

    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """
        ذخیره چندین مقدار در کش محلی به‌صورت یکجا.

        Args:
            items: دیکشنری شامل کلیدها و مقادیر.
            ttl: زمان انقضای مشترک برای همه آیتم‌ها (اختیاری).
        """
        await self._ensure_initialized()

        async with self._lock:
            for key, value in items.items():
                # اگر کلید وجود دارد، حذف می‌کنیم
                if key in self._cache:
                    del self._cache[key]

                # ایجاد آیتم جدید
                item = LocalCacheItem(value, ttl)
                self._cache[key] = item

                # اگر کش پر شد، آیتم‌های قدیمی را حذف می‌کنیم
                if len(self._cache) > self._max_size:
                    await self._evict_lru()

    async def delete_many(self, keys: List[str]) -> int:
        """
        حذف چندین کلید از کش محلی.

        Args:
            keys: لیست کلیدها.

        Returns:
            تعداد کلیدهای حذف‌شده.
        """
        await self._ensure_initialized()

        deleted_count = 0
        async with self._lock:
            for key in keys:
                if key in self._cache:
                    del self._cache[key]
                    deleted_count += 1

        return deleted_count

    async def health_check(self) -> bool:
        """
        بررسی سلامت کش محلی.

        Returns:
            True اگر کش در دسترس باشد (همیشه True است).
        """
        await self._ensure_initialized()
        return True

    async def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار کش محلی.

        Returns:
            دیکشنری شامل آمار کش.
        """
        await self._ensure_initialized()

        total_items = len(self._cache)
        expired_items = 0

        async with self._lock:
            for item in self._cache.values():
                if item.is_expired():
                    expired_items += 1

            # محاسبه میانگین عمر آیتم‌ها
            ages = [time.time() - item.created_at for item in self._cache.values()]
            avg_age = sum(ages) / len(ages) if ages else 0

        return {
            "total_items": total_items,
            "expired_items": expired_items,
            "max_size": self._max_size,
            "usage_percentage": (total_items / self._max_size * 100) if self._max_size > 0 else 0,
            "cleanup_interval": self._cleanup_interval,
            "average_item_age_seconds": avg_age,
            "is_initialized": self._is_initialized,
        }

    async def close(self) -> None:
        """
        بستن کش محلی و آزادسازی منابع.

        این متد در LocalAdapter کش را پاک می‌کند.
        """
        async with self._lock:
            self._cache.clear()
            self._is_initialized = False
            logger.info("LocalAdapter closed successfully.")

    def get_size(self) -> int:
        """
        دریافت تعداد آیتم‌های موجود در کش (همزمان).

        Returns:
            تعداد آیتم‌ها.
        """
        return len(self._cache)

    def is_full(self) -> bool:
        """
        بررسی پر بودن کش.

        Returns:
            True اگر کش پر باشد.
        """
        return len(self._cache) >= self._max_size