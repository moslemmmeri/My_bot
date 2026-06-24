# my_bot_project/src/my_bot/infrastructure/cache/cache_fallback.py
"""
مکانیزم Fallback کش (Cache Fallback).

این ماژول شامل کلاس `CacheFallback` است که یک مکانیزم Fallback خودکار
بین کش اصلی (Primary) و کش پشتیبان (Fallback) فراهم می‌کند.
اگر کش اصلی در دسترس نباشد، به‌صورت خودکار به کش پشتیبان Fallback می‌کند.
"""

import asyncio
from typing import Optional, Any, Dict, List, Union
from functools import wraps

from my_bot.core.exceptions.cache_errors import CacheError, CacheOperationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface

logger = get_logger(__name__)


class CacheFallback:
    """
    مکانیزم Fallback خودکار بین دو کش.

    این کلاس با استفاده از یک کش اصلی (Primary) و یک کش پشتیبان (Fallback)،
    عملیات‌های کش را انجام می‌دهد. اگر کش اصلی با خطا مواجه شود،
    به‌صورت خودکار به کش پشتیبان Fallback می‌کند.

    Attributes:
        primary: کش اصلی (معمولاً Redis).
        fallback: کش پشتیبان (معمولاً Local Cache).
        fallback_enabled: آیا Fallback فعال است.
        fallback_on_error: آیا در صورت خطا به Fallback برود.
        _primary_available: وضعیت در دسترس بودن کش اصلی.
        _lock: قفل برای عملیات اتمیک.
    """

    def __init__(
        self,
        primary: CacheInterface,
        fallback: CacheInterface,
        fallback_enabled: bool = True,
        fallback_on_error: bool = True,
    ) -> None:
        """
        مقداردهی اولیه مکانیزم Fallback.

        Args:
            primary: کش اصلی (معمولاً Redis).
            fallback: کش پشتیبان (معمولاً Local Cache).
            fallback_enabled: آیا Fallback فعال است.
            fallback_on_error: آیا در صورت خطا به Fallback برود.
        """
        self._primary = primary
        self._fallback = fallback
        self._fallback_enabled = fallback_enabled
        self._fallback_on_error = fallback_on_error
        self._primary_available = True
        self._lock = asyncio.Lock()

        logger.info(
            f"CacheFallback initialized: primary={primary.__class__.__name__}, "
            f"fallback={fallback.__class__.__name__}, "
            f"fallback_enabled={fallback_enabled}, "
            f"fallback_on_error={fallback_on_error}"
        )

    async def _execute_with_fallback(
        self,
        operation: str,
        primary_func,
        fallback_func,
        *args,
        **kwargs,
    ) -> Any:
        """
        اجرای یک عملیات با مکانیزم Fallback.

        Args:
            operation: نام عملیات (برای لاگ).
            primary_func: تابع کش اصلی.
            fallback_func: تابع کش پشتیبان.
            *args: پارامترهای توابع.
            **kwargs: پارامترهای نام‌دار توابع.

        Returns:
            نتیجه عملیات.

        Raises:
            CacheOperationError: در صورت بروز خطا در هر دو کش.
        """
        # اگر Fallback غیرفعال است، فقط از کش اصلی استفاده کن
        if not self._fallback_enabled:
            return await primary_func(*args, **kwargs)

        # اگر کش اصلی در دسترس است، از آن استفاده کن
        if self._primary_available:
            try:
                result = await primary_func(*args, **kwargs)
                # اگر عملیات موفق بود، نتیجه را برگردان
                return result

            except Exception as e:
                logger.warning(
                    f"Primary cache {operation} failed: {e}. "
                    f"Falling back to fallback cache."
                )

                # علامت‌گذاری کش اصلی به‌عنوان غیرقابل دسترس
                async with self._lock:
                    self._primary_available = False

                # اگر Fallback_on_error فعال است، از Fallback استفاده کن
                if self._fallback_on_error:
                    try:
                        return await fallback_func(*args, **kwargs)
                    except Exception as fallback_e:
                        logger.error(
                            f"Both primary and fallback cache {operation} failed. "
                            f"Primary error: {e}, Fallback error: {fallback_e}"
                        )
                        raise CacheOperationError(
                            operation=operation,
                            key=kwargs.get("key"),
                            reason=f"Primary error: {e}, Fallback error: {fallback_e}",
                        )
                else:
                    raise

        # اگر کش اصلی در دسترس نیست، از Fallback استفاده کن
        else:
            try:
                # اگر کش اصلی در دسترس نیست، فقط از Fallback استفاده کن
                return await fallback_func(*args, **kwargs)

            except Exception as fallback_e:
                logger.error(f"Fallback cache {operation} failed: {fallback_e}")
                raise CacheOperationError(
                    operation=operation,
                    key=kwargs.get("key"),
                    reason=f"Fallback error: {fallback_e}",
                )

    async def _try_primary_and_fallback(self, operation: str, primary_func, fallback_func, *args, **kwargs) -> Any:
        """
        تلاش برای اجرای عملیات روی کش اصلی و سپس Fallback (برای عملیات‌های نوشتاری).

        این متد برای عملیات‌هایی استفاده می‌شود که باید هم روی کش اصلی و هم روی Fallback
        انجام شوند (مثلاً set, delete).

        Args:
            operation: نام عملیات (برای لاگ).
            primary_func: تابع کش اصلی.
            fallback_func: تابع کش پشتیبان.
            *args: پارامترهای توابع.
            **kwargs: پارامترهای نام‌دار توابع.

        Returns:
            نتیجه عملیات از کش اصلی (یا Fallback در صورت خطا).

        Raises:
            CacheOperationError: در صورت بروز خطا در هر دو کش.
        """
        # اگر Fallback غیرفعال است، فقط از کش اصلی استفاده کن
        if not self._fallback_enabled:
            return await primary_func(*args, **kwargs)

        primary_result = None
        primary_error = None

        # ابتدا روی کش اصلی امتحان کن
        try:
            primary_result = await primary_func(*args, **kwargs)
            # اگر کش اصلی کار کرد، نتیجه را برگردان
            # اما اگر کش اصلی قبلاً غیرقابل دسترس علامت‌گذاری شده بود، وضعیت را به‌روز کن
            if not self._primary_available:
                async with self._lock:
                    self._primary_available = True
                    logger.info("Primary cache recovered.")

            # همچنین روی Fallback هم بنویس (برای هماهنگی)
            try:
                await fallback_func(*args, **kwargs)
            except Exception as fallback_e:
                logger.warning(
                    f"Fallback cache {operation} failed (but primary succeeded): {fallback_e}"
                )

            return primary_result

        except Exception as e:
            primary_error = e
            logger.warning(
                f"Primary cache {operation} failed: {e}. "
                f"Falling back to fallback cache."
            )

            # علامت‌گذاری کش اصلی به‌عنوان غیرقابل دسترس
            async with self._lock:
                self._primary_available = False

            # اگر Fallback_on_error فعال است، از Fallback استفاده کن
            if self._fallback_on_error:
                try:
                    fallback_result = await fallback_func(*args, **kwargs)
                    logger.info(f"Fallback cache {operation} succeeded.")
                    return fallback_result
                except Exception as fallback_e:
                    logger.error(
                        f"Both primary and fallback cache {operation} failed. "
                        f"Primary error: {primary_error}, Fallback error: {fallback_e}"
                    )
                    raise CacheOperationError(
                        operation=operation,
                        key=kwargs.get("key"),
                        reason=f"Primary error: {primary_error}, Fallback error: {fallback_e}",
                    )
            else:
                raise

    # ----------------------------------------------
    # عملیات‌های کش با Fallback
    # ----------------------------------------------

    async def get(self, key: str) -> Optional[Any]:
        """
        دریافت یک مقدار از کش (با Fallback).

        Args:
            key: کلید مورد نظر.

        Returns:
            مقدار ذخیره‌شده در صورت وجود، در غیر این صورت None.
        """
        return await self._execute_with_fallback(
            "get",
            self._primary.get,
            self._fallback.get,
            key=key,
        )

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """
        ذخیره یک مقدار در کش (با Fallback).

        Args:
            key: کلید برای ذخیره‌سازی.
            value: مقدار برای ذخیره‌سازی.
            ttl: زمان انقضا بر حسب ثانیه (اختیاری).
        """
        await self._try_primary_and_fallback(
            "set",
            self._primary.set,
            self._fallback.set,
            key,
            value,
            ttl,
            key=key,
        )

    async def delete(self, key: str) -> bool:
        """
        حذف یک کلید از کش (با Fallback).

        Args:
            key: کلید برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود کلید.
        """
        return await self._try_primary_and_fallback(
            "delete",
            self._primary.delete,
            self._fallback.delete,
            key,
            key=key,
        )

    async def exists(self, key: str) -> bool:
        """
        بررسی وجود یک کلید در کش (با Fallback).

        Args:
            key: کلید مورد نظر.

        Returns:
            True اگر کلید وجود داشته باشد، در غیر این صورت False.
        """
        return await self._execute_with_fallback(
            "exists",
            self._primary.exists,
            self._fallback.exists,
            key=key,
        )

    async def clear(self) -> None:
        """
        پاک کردن تمام کلیدها از کش (با Fallback).
        """
        await self._try_primary_and_fallback(
            "clear",
            self._primary.clear,
            self._fallback.clear,
        )

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        دریافت زمان باقی‌مانده تا انقضای یک کلید (با Fallback).

        Args:
            key: کلید مورد نظر.

        Returns:
            زمان باقی‌مانده بر حسب ثانیه، یا None اگر کلید وجود نداشته باشد.
        """
        return await self._execute_with_fallback(
            "get_ttl",
            self._primary.get_ttl,
            self._fallback.get_ttl,
            key=key,
        )

    async def set_ttl(self, key: str, ttl: int) -> bool:
        """
        تنظیم زمان انقضای جدید برای یک کلید (با Fallback).

        Args:
            key: کلید مورد نظر.
            ttl: زمان انقضا بر حسب ثانیه.

        Returns:
            True در صورت موفقیت، False در صورت عدم وجود کلید.
        """
        return await self._try_primary_and_fallback(
            "set_ttl",
            self._primary.set_ttl,
            self._fallback.set_ttl,
            key,
            ttl,
            key=key,
        )

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        افزایش مقدار یک کلید عددی در کش (با Fallback).

        Args:
            key: کلید مورد نظر.
            amount: مقدار افزایش (پیش‌فرض ۱).

        Returns:
            مقدار جدید در صورت موفقیت، یا None اگر کلید وجود نداشته باشد.
        """
        return await self._execute_with_fallback(
            "increment",
            self._primary.increment,
            self._fallback.increment,
            key,
            amount,
            key=key,
        )

    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        کاهش مقدار یک کلید عددی در کش (با Fallback).

        Args:
            key: کلید مورد نظر.
            amount: مقدار کاهش (پیش‌فرض ۱).

        Returns:
            مقدار جدید در صورت موفقیت، یا None اگر کلید وجود نداشته باشد.
        """
        return await self._execute_with_fallback(
            "decrement",
            self._primary.decrement,
            self._fallback.decrement,
            key,
            amount,
            key=key,
        )

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        دریافت چندین مقدار از کش با کلیدهای مشخص (با Fallback).

        Args:
            keys: لیست کلیدها.

        Returns:
            دیکشنری شامل کلیدها و مقادیر موجود.
        """
        return await self._execute_with_fallback(
            "get_many",
            self._primary.get_many,
            self._fallback.get_many,
            keys,
        )

    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """
        ذخیره چندین مقدار در کش به‌صورت یکجا (با Fallback).

        Args:
            items: دیکشنری شامل کلیدها و مقادیر.
            ttl: زمان انقضای مشترک برای همه آیتم‌ها (اختیاری).
        """
        await self._try_primary_and_fallback(
            "set_many",
            self._primary.set_many,
            self._fallback.set_many,
            items,
            ttl,
        )

    async def delete_many(self, keys: List[str]) -> int:
        """
        حذف چندین کلید از کش (با Fallback).

        Args:
            keys: لیست کلیدها.

        Returns:
            تعداد کلیدهای حذف‌شده.
        """
        return await self._try_primary_and_fallback(
            "delete_many",
            self._primary.delete_many,
            self._fallback.delete_many,
            keys,
        )

    async def health_check(self) -> bool:
        """
        بررسی سلامت سرویس کش (با Fallback).

        Returns:
            True اگر حداقل یکی از کش‌ها سالم باشد.
        """
        primary_ok = await self._primary.health_check()
        if primary_ok:
            if not self._primary_available:
                async with self._lock:
                    self._primary_available = True
            return True

        # اگر کش اصلی سالم نیست، Fallback را بررسی کن
        fallback_ok = await self._fallback.health_check()
        if fallback_ok:
            async with self._lock:
                self._primary_available = False
            return True

        return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار کش (با Fallback).

        Returns:
            دیکشنری شامل آمار هر دو کش.
        """
        stats = {
            "primary_available": self._primary_available,
            "fallback_enabled": self._fallback_enabled,
            "fallback_on_error": self._fallback_on_error,
        }

        try:
            primary_stats = await self._primary.get_stats()
            stats["primary"] = primary_stats
        except Exception as e:
            stats["primary_error"] = str(e)

        try:
            fallback_stats = await self._fallback.get_stats()
            stats["fallback"] = fallback_stats
        except Exception as e:
            stats["fallback_error"] = str(e)

        return stats

    async def sync_to_primary(self, key: str) -> bool:
        """
        همگام‌سازی یک کلید از Fallback به Primary.

        Args:
            key: کلید برای همگام‌سازی.

        Returns:
            True در صورت موفقیت، False در صورت خطا.
        """
        # اگر کش اصلی در دسترس نیست، همگام‌سازی ممکن نیست
        if not self._primary_available:
            logger.warning(f"Cannot sync key '{key}' to primary: primary unavailable")
            return False

        try:
            # دریافت مقدار از Fallback
            value = await self._fallback.get(key)
            if value is None:
                return False

            # دریافت TTL از Fallback
            ttl = await self._fallback.get_ttl(key)

            # ذخیره در Primary
            await self._primary.set(key, value, ttl)
            logger.debug(f"Synced key '{key}' from fallback to primary")
            return True

        except Exception as e:
            logger.error(f"Failed to sync key '{key}' to primary: {e}")
            return False

    async def sync_all_to_primary(self) -> Dict[str, int]:
        """
        همگام‌سازی تمام کلیدها از Fallback به Primary.

        Returns:
            دیکشنری شامل تعداد کلیدهای همگام‌سازی‌شده و خطاها.
        """
        if not self._primary_available:
            logger.warning("Cannot sync to primary: primary unavailable")
            return {"synced": 0, "failed": 0, "total": 0}

        try:
            # دریافت آمار Fallback
            stats = await self._fallback.get_stats()
            total_keys = stats.get("total_items", 0)

            synced = 0
            failed = 0

            # در اینجا نمی‌توانیم کلیدها را لیست کنیم (API کش لیست کلیدها را ندارد)
            # بنابراین این متد فقط برای نمایش است
            logger.info(f"Sync all to primary not fully implemented. Total keys: {total_keys}")

            return {"synced": synced, "failed": failed, "total": total_keys}

        except Exception as e:
            logger.error(f"Failed to sync all to primary: {e}")
            return {"synced": 0, "failed": 0, "total": 0}

    async def close(self) -> None:
        """
        بستن هر دو کش و آزادسازی منابع.
        """
        try:
            await self._primary.close()
        except Exception as e:
            logger.error(f"Error closing primary cache: {e}")

        try:
            await self._fallback.close()
        except Exception as e:
            logger.error(f"Error closing fallback cache: {e}")

        logger.info("CacheFallback closed successfully.")