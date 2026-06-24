# my_bot_project/src/my_bot/domain/interfaces/repositories/coupon_repository.py
"""
اینترفیس ریپازیتوری کوپن (Coupon Repository Interface).

این اینترفیس قراردادهای لازم برای ذخیره‌سازی، بازیابی و جستجوی
کوپن‌های تخفیف در سیستم را تعریف می‌کند. پیاده‌سازی این اینترفیس
در لایه زیرساخت (Infrastructure) انجام می‌شود.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from my_bot.domain.entities.coupon import Coupon, CouponType
from my_bot.domain.value_objects.money import Money


class CouponRepository(ABC):
    """
    اینترفیس ریپازیتوری کوپن.

    این کلاس مسئولیت مدیریت ذخیره‌سازی، بازیابی و جستجوی کوپن‌های
    تخفیف در سیستم را بر عهده دارد.
    """

    @abstractmethod
    async def get_by_id(self, coupon_id: int) -> Optional[Coupon]:
        """
        دریافت کوپن با شناسه داخلی (Primary Key).

        Args:
            coupon_id: شناسه کوپن در دیتابیس.

        Returns:
            کوپن در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Coupon]:
        """
        دریافت کوپن با کد تخفیف (Unique).

        Args:
            code: کد تخفیف.

        Returns:
            کوپن در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[Coupon]:
        """
        دریافت لیست کوپن‌ها با صفحه‌بندی و فیلتر اختیاری.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            is_active: فیلتر بر اساس فعال بودن (اختیاری).
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی، False برای صعودی.

        Returns:
            لیست کوپن‌ها.
        """
        pass

    @abstractmethod
    async def save(self, coupon: Coupon) -> Coupon:
        """
        ذخیره یا به‌روزرسانی یک کوپن در دیتابیس.

        Args:
            coupon: موجودیت کوپن برای ذخیره‌سازی.

        Returns:
            کوپن ذخیره‌شده با شناسه و تاریخ‌های به‌روزرسانی‌شده.
        """
        pass

    @abstractmethod
    async def delete(self, coupon_id: int) -> bool:
        """
        حذف یک کوپن از دیتابیس.

        Args:
            coupon_id: شناسه کوپن برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود کوپن.
        """
        pass

    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        شمارش تعداد کوپن‌ها با اعمال فیلترهای اختیاری.

        Args:
            filters: دیکشنری فیلترها (اختیاری).

        Returns:
            تعداد کوپن‌ها.
        """
        pass

    @abstractmethod
    async def exists_by_code(self, code: str) -> bool:
        """
        بررسی وجود کوپن با کد مشخص.

        Args:
            code: کد تخفیف.

        Returns:
            True اگر کوپن وجود داشته باشد، در غیر این صورت False.
        """
        pass

    @abstractmethod
    async def get_valid_coupons(
        self,
        user_id: Optional[int] = None,
        order_amount: Optional[Money] = None,
        product_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Coupon]:
        """
        دریافت کوپن‌های معتبر برای یک کاربر، مبلغ سفارش و محصول خاص.

        Args:
            user_id: شناسه کاربر (اختیاری).
            order_amount: مبلغ سفارش (اختیاری).
            product_id: شناسه محصول (اختیاری).
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کوپن‌های معتبر.
        """
        pass

    @abstractmethod
    async def get_active_coupons(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Coupon]:
        """
        دریافت کوپن‌های فعال (is_active=True و تاریخ اعتبار).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کوپن‌های فعال.
        """
        pass

    @abstractmethod
    async def get_expired_coupons(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Coupon]:
        """
        دریافت کوپن‌های منقضی‌شده.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کوپن‌های منقضی‌شده.
        """
        pass

    @abstractmethod
    async def use_coupon(self, coupon_id: int, user_id: int) -> Optional[Coupon]:
        """
        ثبت استفاده از کوپن توسط یک کاربر (افزایش شمارش استفاده).

        Args:
            coupon_id: شناسه کوپن.
            user_id: شناسه کاربر.

        Returns:
            کوپن به‌روزرسانی‌شده یا None در صورت عدم وجود یا نامعتبر بودن.
        """
        pass

    @abstractmethod
    async def reset_usage(self, coupon_id: int) -> Optional[Coupon]:
        """
        بازنشانی آمار استفاده از کوپن.

        Args:
            coupon_id: شناسه کوپن.

        Returns:
            کوپن به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def activate(self, coupon_id: int) -> Optional[Coupon]:
        """
        فعال‌سازی یک کوپن.

        Args:
            coupon_id: شناسه کوپن.

        Returns:
            کوپن به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def deactivate(self, coupon_id: int, reason: Optional[str] = None) -> Optional[Coupon]:
        """
        غیرفعال‌سازی یک کوپن.

        Args:
            coupon_id: شناسه کوپن.
            reason: دلیل غیرفعال‌سازی (اختیاری).

        Returns:
            کوپن به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def get_user_coupon_usage(self, user_id: int, coupon_id: int) -> int:
        """
        دریافت تعداد دفعات استفاده یک کاربر از یک کوپن.

        Args:
            user_id: شناسه کاربر.
            coupon_id: شناسه کوپن.

        Returns:
            تعداد دفعات استفاده.
        """
        pass

    @abstractmethod
    async def get_most_used_coupons(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        دریافت پراستفاده‌ترین کوپن‌ها.

        Args:
            limit: حداکثر تعداد کوپن‌ها.
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            لیست دیکشنری‌های شامل شناسه کوپن، کد، تعداد استفاده.
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی کوپن‌ها.

        Returns:
            دیکشنری شامل آمار:
            - total_coupons: تعداد کل کوپن‌ها
            - active_coupons: تعداد کوپن‌های فعال
            - expired_coupons: تعداد کوپن‌های منقضی
            - total_usage: تعداد کل استفاده‌ها
            - coupons_by_type: تعداد کوپن‌ها به‌تفکیک نوع
        """
        pass