# my_bot_project/src/my_bot/domain/interfaces/repositories/order_repository.py
"""
اینترفیس ریپازیتوری سفارش (Order Repository Interface).

این اینترفیس قراردادهای لازم برای ذخیره‌سازی، بازیابی و جستجوی
سفارشات در سیستم را تعریف می‌کند. پیاده‌سازی این اینترفیس در لایه
زیرساخت (Infrastructure) انجام می‌شود.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.domain.entities.order import Order
from my_bot.domain.value_objects.money import Money


class OrderRepository(ABC):
    """
    اینترفیس ریپازیتوری سفارش.

    این کلاس مسئولیت مدیریت ذخیره‌سازی، بازیابی و جستجوی سفارشات
    در سیستم را بر عهده دارد.
    """

    @abstractmethod
    async def get_by_id(self, order_id: int) -> Optional[Order]:
        """
        دریافت سفارش با شناسه داخلی (Primary Key).

        Args:
            order_id: شناسه سفارش در دیتابیس.

        Returns:
            سفارش در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_order_number(self, order_number: str) -> Optional[Order]:
        """
        دریافت سفارش با شماره سفارش.

        Args:
            order_number: شماره سفارش (Unique).

        Returns:
            سفارش در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[OrderStatus] = None,
    ) -> List[Order]:
        """
        دریافت سفارشات یک کاربر خاص.

        Args:
            user_id: شناسه کاربر.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            status: فیلتر بر اساس وضعیت (اختیاری).

        Returns:
            لیست سفارشات کاربر.
        """
        pass

    @abstractmethod
    async def get_by_status(
        self,
        status: OrderStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """
        دریافت سفارشات با وضعیت مشخص.

        Args:
            status: وضعیت سفارش.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست سفارشات با وضعیت مشخص.
        """
        pass

    @abstractmethod
    async def get_by_payment_id(self, payment_id: str) -> Optional[Order]:
        """
        دریافت سفارش با شناسه پرداخت.

        Args:
            payment_id: شناسه تراکنش پرداخت.

        Returns:
            سفارش در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[Order]:
        """
        دریافت لیست سفارشات با صفحه‌بندی.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی، False برای صعودی.

        Returns:
            لیست سفارشات.
        """
        pass

    @abstractmethod
    async def save(self, order: Order) -> Order:
        """
        ذخیره یا به‌روزرسانی یک سفارش در دیتابیس.

        Args:
            order: موجودیت سفارش برای ذخیره‌سازی.

        Returns:
            سفارش ذخیره‌شده با شناسه و تاریخ‌های به‌روزرسانی‌شده.
        """
        pass

    @abstractmethod
    async def delete(self, order_id: int) -> bool:
        """
        حذف یک سفارش از دیتابیس.

        Args:
            order_id: شناسه سفارش برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود سفارش.
        """
        pass

    @abstractmethod
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        شمارش تعداد سفارشات با اعمال فیلترهای اختیاری.

        Args:
            filters: دیکشنری فیلترها (اختیاری).

        Returns:
            تعداد سفارشات.
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        reason: Optional[str] = None,
    ) -> Optional[Order]:
        """
        به‌روزرسانی وضعیت یک سفارش.

        Args:
            order_id: شناسه سفارش.
            new_status: وضعیت جدید.
            reason: دلیل تغییر وضعیت (اختیاری).

        Returns:
            سفارش به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def add_payment_id(
        self,
        order_id: int,
        payment_id: str,
    ) -> Optional[Order]:
        """
        افزودن شناسه پرداخت به سفارش.

        Args:
            order_id: شناسه سفارش.
            payment_id: شناسه تراکنش پرداخت.

        Returns:
            سفارش به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def apply_coupon(
        self,
        order_id: int,
        coupon_code: str,
        discount_amount: Money,
    ) -> Optional[Order]:
        """
        اعمال کد تخفیف به سفارش.

        Args:
            order_id: شناسه سفارش.
            coupon_code: کد تخفیف.
            discount_amount: مبلغ تخفیف.

        Returns:
            سفارش به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def add_tracking_code(
        self,
        order_id: int,
        tracking_code: str,
    ) -> Optional[Order]:
        """
        افزودن کد رهگیری به سفارش.

        Args:
            order_id: شناسه سفارش.
            tracking_code: کد رهگیری پستی.

        Returns:
            سفارش به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def get_orders_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """
        دریافت سفارشات در بازه زمانی مشخص.

        Args:
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست سفارشات در بازه زمانی.
        """
        pass

    @abstractmethod
    async def get_pending_orders(
        self,
        older_than_minutes: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """
        دریافت سفارشات در انتظار پرداخت.

        Args:
            older_than_minutes: سفارشات قدیمی‌تر از این دقیقه (اختیاری).
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست سفارشات در انتظار پرداخت.
        """
        pass

    @abstractmethod
    async def get_orders_needing_action(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """
        دریافت سفارشاتی که نیاز به اقدام دارند (وضعیت‌های PENDING, ON_HOLD).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست سفارشات نیازمند اقدام.
        """
        pass

    @abstractmethod
    async def get_orders_by_product(
        self,
        product_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """
        دریافت سفارشات حاوی یک محصول خاص.

        Args:
            product_id: شناسه محصول.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست سفارشات حاوی محصول.
        """
        pass

    @abstractmethod
    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        دریافت آمار کلی سفارشات.

        Args:
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            دیکشنری شامل آمار:
            - total_orders: تعداد کل سفارشات
            - orders_by_status: تعداد سفارشات به‌تفکیک وضعیت
            - total_revenue: مجموع درآمد
            - average_order_value: میانگین مبلغ هر سفارش
            - orders_today: تعداد سفارشات امروز
            - orders_this_week: تعداد سفارشات این هفته
            - orders_this_month: تعداد سفارشات این ماه
        """
        pass

    @abstractmethod
    async def get_revenue_by_date(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: str = "day",  # day, week, month
    ) -> List[Dict[str, Any]]:
        """
        دریافت درآمد به‌تفکیک بازه زمانی.

        Args:
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.
            group_by: دسته‌بندی بر اساس ('day', 'week', 'month').

        Returns:
            لیست دیکشنری‌های شامل تاریخ و درآمد.
        """
        pass

    @abstractmethod
    async def get_top_products(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        دریافت محصولات پرفروش.

        Args:
            limit: حداکثر تعداد محصولات.
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            لیست دیکشنری‌های شامل شناسه محصول، نام، تعداد فروش و درآمد.
        """
        pass

    @abstractmethod
    async def get_total_spent_by_user(self, user_id: int) -> Money:
        """
        دریافت مجموع مبلغ پرداختی یک کاربر (سفارشات موفق).

        Args:
            user_id: شناسه کاربر.

        Returns:
            مجموع مبلغ پرداختی.
        """
        pass

    @abstractmethod
    async def get_order_count_by_user(self, user_id: int) -> int:
        """
        دریافت تعداد سفارشات یک کاربر (همه وضعیت‌ها).

        Args:
            user_id: شناسه کاربر.

        Returns:
            تعداد سفارشات کاربر.
        """
        pass

    @abstractmethod
    async def get_last_order_by_user(self, user_id: int) -> Optional[Order]:
        """
        دریافت آخرین سفارش یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            آخرین سفارش کاربر یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def get_canceled_orders_by_date(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Order]:
        """
        دریافت سفارشات لغو شده در بازه زمانی.

        Args:
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.

        Returns:
            لیست سفارشات لغو شده.
        """
        pass

    @abstractmethod
    async def get_refunded_orders_by_date(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Order]:
        """
        دریافت سفارشات بازگشت وجه شده در بازه زمانی.

        Args:
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.

        Returns:
            لیست سفارشات بازگشت وجه شده.
        """
        pass