# my_bot_project/src/my_bot/domain/interfaces/repositories/payment_repository.py
"""
اینترفیس ریپازیتوری پرداخت (Payment Repository Interface).

این اینترفیس قراردادهای لازم برای ذخیره‌سازی، بازیابی و جستجوی
تراکنش‌های پرداخت در سیستم را تعریف می‌کند. پیاده‌سازی این اینترفیس
در لایه زیرساخت (Infrastructure) انجام می‌شود.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from my_bot.core.constants.payment_statuses import PaymentStatus
from my_bot.domain.entities.payment import Payment
from my_bot.domain.value_objects.money import Money


class PaymentRepository(ABC):
    """
    اینترفیس ریپازیتوری پرداخت.

    این کلاس مسئولیت مدیریت ذخیره‌سازی، بازیابی و جستجوی تراکنش‌های
    پرداخت در سیستم را بر عهده دارد.
    """

    @abstractmethod
    async def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """
        دریافت تراکنش با شناسه داخلی (Primary Key).

        Args:
            payment_id: شناسه تراکنش در دیتابیس.

        Returns:
            تراکنش در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """
        دریافت تراکنش با شناسه تراکنش در درگاه پرداخت.

        Args:
            transaction_id: شناسه تراکنش در درگاه.

        Returns:
            تراکنش در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_tracking_code(self, tracking_code: str) -> Optional[Payment]:
        """
        دریافت تراکنش با کد رهگیری پرداخت.

        Args:
            tracking_code: کد رهگیری پرداخت.

        Returns:
            تراکنش در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_order_id(self, order_id: str) -> Optional[Payment]:
        """
        دریافت تراکنش مرتبط با یک سفارش.

        Args:
            order_id: شناسه سفارش.

        Returns:
            تراکنش در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[PaymentStatus] = None,
    ) -> List[Payment]:
        """
        دریافت تراکنش‌های یک کاربر خاص.

        Args:
            user_id: شناسه کاربر.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            status: فیلتر بر اساس وضعیت (اختیاری).

        Returns:
            لیست تراکنش‌های کاربر.
        """
        pass

    @abstractmethod
    async def get_by_status(
        self,
        status: PaymentStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Payment]:
        """
        دریافت تراکنش‌ها با وضعیت مشخص.

        Args:
            status: وضعیت پرداخت.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست تراکنش‌ها با وضعیت مشخص.
        """
        pass

    @abstractmethod
    async def get_by_gateway(
        self,
        gateway: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Payment]:
        """
        دریافت تراکنش‌ها با درگاه پرداخت مشخص.

        Args:
            gateway: نام درگاه پرداخت.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست تراکنش‌های درگاه مشخص.
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[Payment]:
        """
        دریافت لیست تراکنش‌ها با صفحه‌بندی.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی، False برای صعودی.

        Returns:
            لیست تراکنش‌ها.
        """
        pass

    @abstractmethod
    async def save(self, payment: Payment) -> Payment:
        """
        ذخیره یا به‌روزرسانی یک تراکنش در دیتابیس.

        Args:
            payment: موجودیت پرداخت برای ذخیره‌سازی.

        Returns:
            تراکنش ذخیره‌شده با شناسه و تاریخ‌های به‌روزرسانی‌شده.
        """
        pass

    @abstractmethod
    async def delete(self, payment_id: int) -> bool:
        """
        حذف یک تراکنش از دیتابیس.

        Args:
            payment_id: شناسه تراکنش برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود تراکنش.
        """
        pass

    @abstractmethod
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        شمارش تعداد تراکنش‌ها با اعمال فیلترهای اختیاری.

        Args:
            filters: دیکشنری فیلترها (اختیاری).

        Returns:
            تعداد تراکنش‌ها.
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        payment_id: int,
        new_status: PaymentStatus,
        error_message: Optional[str] = None,
    ) -> Optional[Payment]:
        """
        به‌روزرسانی وضعیت یک تراکنش.

        Args:
            payment_id: شناسه تراکنش.
            new_status: وضعیت جدید.
            error_message: پیام خطا (در صورت ناموفق بودن).

        Returns:
            تراکنش به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def mark_as_success(
        self,
        payment_id: int,
        transaction_id: str,
        reference_id: Optional[str] = None,
        tracking_code: Optional[str] = None,
    ) -> Optional[Payment]:
        """
        علامت‌گذاری تراکنش به‌عنوان موفق.

        Args:
            payment_id: شناسه تراکنش.
            transaction_id: شناسه تراکنش در درگاه.
            reference_id: شناسه مرجع (اختیاری).
            tracking_code: کد رهگیری (اختیاری).

        Returns:
            تراکنش به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def mark_as_failed(
        self,
        payment_id: int,
        error_message: str,
    ) -> Optional[Payment]:
        """
        علامت‌گذاری تراکنش به‌عنوان ناموفق.

        Args:
            payment_id: شناسه تراکنش.
            error_message: پیام خطا.

        Returns:
            تراکنش به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def get_payments_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Payment]:
        """
        دریافت تراکنش‌ها در بازه زمانی مشخص.

        Args:
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست تراکنش‌ها در بازه زمانی.
        """
        pass

    @abstractmethod
    async def get_successful_payments(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Payment]:
        """
        دریافت تراکنش‌های موفق.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست تراکنش‌های موفق.
        """
        pass

    @abstractmethod
    async def get_failed_payments(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Payment]:
        """
        دریافت تراکنش‌های ناموفق.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست تراکنش‌های ناموفق.
        """
        pass

    @abstractmethod
    async def get_pending_payments(
        self,
        older_than_minutes: Optional[int] = None,
    ) -> List[Payment]:
        """
        دریافت تراکنش‌های در انتظار.

        Args:
            older_than_minutes: تراکنش‌های قدیمی‌تر از این دقیقه (اختیاری).

        Returns:
            لیست تراکنش‌های در انتظار.
        """
        pass

    @abstractmethod
    async def get_total_amount_by_user(self, user_id: int) -> Money:
        """
        دریافت مجموع مبلغ پرداختی یک کاربر (تراکنش‌های موفق).

        Args:
            user_id: شناسه کاربر.

        Returns:
            مجموع مبلغ پرداختی.
        """
        pass

    @abstractmethod
    async def get_total_amount_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[PaymentStatus] = PaymentStatus.SUCCESS,
    ) -> Money:
        """
        دریافت مجموع مبلغ تراکنش‌ها در بازه زمانی.

        Args:
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.
            status: وضعیت تراکنش (پیش‌فرض SUCCESS).

        Returns:
            مجموع مبلغ تراکنش‌ها.
        """
        pass

    @abstractmethod
    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        دریافت آمار کلی تراکنش‌ها.

        Args:
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            دیکشنری شامل آمار:
            - total_payments: تعداد کل تراکنش‌ها
            - successful_payments: تعداد تراکنش‌های موفق
            - failed_payments: تعداد تراکنش‌های ناموفق
            - pending_payments: تعداد تراکنش‌های در انتظار
            - total_revenue: مجموع درآمد
            - average_amount: میانگین مبلغ هر تراکنش
            - payments_today: تعداد تراکنش‌های امروز
            - payments_this_week: تعداد تراکنش‌های این هفته
            - payments_by_gateway: تعداد تراکنش‌ها به‌تفکیک درگاه
        """
        pass

    @abstractmethod
    async def get_revenue_by_gateway(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Money]:
        """
        دریافت درآمد به‌تفکیک درگاه پرداخت.

        Args:
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.

        Returns:
            دیکشنری با کلید نام درگاه و مقدار درآمد.
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
    async def get_refunded_amount_by_user(self, user_id: int) -> Money:
        """
        دریافت مجموع مبلغ بازگشت‌وجه‌شده برای یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            مجموع مبلغ بازگشت‌وجه.
        """
        pass