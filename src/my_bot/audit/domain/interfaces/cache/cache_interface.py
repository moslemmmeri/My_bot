# my_bot_project/src/my_bot/domain/interfaces/cache/cache_interface.py
"""
اینترفیس کش (Cache Interface).

این اینترفیس قراردادهای لازم برای سیستم‌های کش (مانند Redis و Local Cache)
را تعریف می‌کند. پیاده‌سازی این اینترفیس در لایه زیرساخت (Infrastructure)
انجام می‌شود و امکان تعویض پشت‌پرده (backend) کش را فراهم می‌کند.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List


class CacheInterface(ABC):
    """
    اینترفیس کش.

    این کلاس مسئولیت مدیریت ذخیره‌سازی و بازیابی داده‌ها در کش را بر عهده دارد.
    تمام متدها به‌صورت async تعریف شده‌اند تا با معماری غیرهمگام پروژه سازگار باشند.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        دریافت یک مقدار از کش با کلید مشخص.

        Args:
            key: کلید مورد نظر.

        Returns:
            مقدار ذخیره‌شده در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """
        ذخیره یک مقدار در کش با کلید مشخص و زمان انقضای اختیاری.

        Args:
            key: کلید برای ذخیره‌سازی.
            value: مقدار برای ذخیره‌سازی (هر نوع قابل سریال‌سازی).
            ttl: زمان انقضا بر حسب ثانیه (اختیاری).
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        حذف یک کلید از کش.

        Args:
            key: کلید برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود کلید.
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        بررسی وجود یک کلید در کش.

        Args:
            key: کلید مورد نظر.

        Returns:
            True اگر کلید وجود داشته باشد، در غیر این صورت False.
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """
        پاک کردن تمام کلیدها از کش.
        """
        pass

    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        دریافت زمان باقی‌مانده تا انقضای یک کلید.

        Args:
            key: کلید مورد نظر.

        Returns:
            زمان باقی‌مانده بر حسب ثانیه، یا None اگر کلید وجود نداشته باشد
            یا بدون انقضا باشد.
        """
        pass

    @abstractmethod
    async def set_ttl(self, key: str, ttl: int) -> bool:
        """
        تنظیم زمان انقضای جدید برای یک کلید.

        Args:
            key: کلید مورد نظر.
            ttl: زمان انقضا بر حسب ثانیه.

        Returns:
            True در صورت موفقیت، False در صورت عدم وجود کلید.
        """
        pass

    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        افزایش مقدار یک کلید عددی در کش (اتمیک).

        Args:
            key: کلید مورد نظر.
            amount: مقدار افزایش (پیش‌فرض ۱).

        Returns:
            مقدار جدید در صورت موفقیت، یا None اگر کلید وجود نداشته باشد.
        """
        pass

    @abstractmethod
    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        کاهش مقدار یک کلید عددی در کش (اتمیک).

        Args:
            key: کلید مورد نظر.
            amount: مقدار کاهش (پیش‌فرض ۱).

        Returns:
            مقدار جدید در صورت موفقیت، یا None اگر کلید وجود نداشته باشد.
        """
        pass

    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        دریافت چندین مقدار از کش با کلیدهای مشخص.

        Args:
            keys: لیست کلیدها.

        Returns:
            دیکشنری شامل کلیدها و مقادیر موجود (کلیدهای ناموجود در نتیجه نیستند).
        """
        pass

    @abstractmethod
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
        """
        pass

    @abstractmethod
    async def delete_many(self, keys: List[str]) -> int:
        """
        حذف چندین کلید از کش.

        Args:
            keys: لیست کلیدها.

        Returns:
            تعداد کلیدهای حذف‌شده.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        بررسی سلامت سرویس کش.

        Returns:
            True اگر کش در دسترس و سالم باشد، در غیر این صورت False.
        """
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار کش (تعداد کلیدها، حافظه استفاده‌شده، و ...).

        Returns:
            دیکشنری شامل آمار کش.
        """
        pass