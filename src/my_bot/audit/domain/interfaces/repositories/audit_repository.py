# my_bot_project/src/my_bot/domain/interfaces/repositories/audit_repository.py
"""
اینترفیس ریپازیتوری لاگ حسابرسی (Audit Log Repository Interface).

این اینترفیس قراردادهای لازم برای ذخیره‌سازی، بازیابی و جستجوی
لاگ‌های حسابرسی در سیستم را تعریف می‌کند. پیاده‌سازی این اینترفیس
در لایه زیرساخت (Infrastructure) انجام می‌شود.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from my_bot.domain.entities.audit_log import AuditLog, AuditAction, AuditStatus


class AuditRepository(ABC):
    """
    اینترفیس ریپازیتوری لاگ حسابرسی.

    این کلاس مسئولیت مدیریت ذخیره‌سازی، بازیابی و جستجوی لاگ‌های
    حسابرسی در سیستم را بر عهده دارد.
    """

    @abstractmethod
    async def get_by_id(self, log_id: int) -> Optional[AuditLog]:
        """
        دریافت لاگ حسابرسی با شناسه داخلی (Primary Key).

        Args:
            log_id: شناسه لاگ در دیتابیس.

        Returns:
            لاگ در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        action: Optional[AuditAction] = None,
    ) -> List[AuditLog]:
        """
        دریافت لاگ‌های یک کاربر خاص.

        Args:
            user_id: شناسه کاربر.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            action: فیلتر بر اساس نوع عملیات (اختیاری).

        Returns:
            لیست لاگ‌های کاربر.
        """
        pass

    @abstractmethod
    async def get_by_action(
        self,
        action: AuditAction,
        skip: int = 0,
        limit: int = 100,
        status: Optional[AuditStatus] = None,
    ) -> List[AuditLog]:
        """
        دریافت لاگ‌ها با نوع عملیات مشخص.

        Args:
            action: نوع عملیات.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            status: فیلتر بر اساس وضعیت (اختیاری).

        Returns:
            لیست لاگ‌ها با نوع عملیات مشخص.
        """
        pass

    @abstractmethod
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        دریافت لاگ‌های مربوط به یک موجودیت خاص (مثلاً یک سفارش یا کاربر).

        Args:
            entity_type: نوع موجودیت.
            entity_id: شناسه موجودیت.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست لاگ‌های موجودیت.
        """
        pass

    @abstractmethod
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        دریافت لاگ‌ها در بازه زمانی مشخص.

        Args:
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست لاگ‌ها در بازه زمانی.
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[AuditLog]:
        """
        دریافت لیست لاگ‌ها با صفحه‌بندی.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی، False برای صعودی.

        Returns:
            لیست لاگ‌ها.
        """
        pass

    @abstractmethod
    async def save(self, log: AuditLog) -> AuditLog:
        """
        ذخیره یک لاگ حسابرسی در دیتابیس.

        Args:
            log: موجودیت لاگ برای ذخیره‌سازی.

        Returns:
            لاگ ذخیره‌شده با شناسه و تاریخ ایجاد.
        """
        pass

    @abstractmethod
    async def delete_old_logs(self, older_than_days: int) -> int:
        """
        حذف لاگ‌های قدیمی‌تر از تعداد روز مشخص.

        Args:
            older_than_days: تعداد روزهای نگهداری لاگ.

        Returns:
            تعداد لاگ‌های حذف‌شده.
        """
        pass

    @abstractmethod
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        شمارش تعداد لاگ‌ها با اعمال فیلترهای اختیاری.

        Args:
            filters: دیکشنری فیلترها (اختیاری).

        Returns:
            تعداد لاگ‌ها.
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[AuditLog]:
        """
        جستجوی لاگ‌ها با استفاده از متن (پیام، نام کاربری، نوع موجودیت).

        Args:
            query: عبارت جستجو.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست لاگ‌های مطابق با عبارت جستجو.
        """
        pass

    @abstractmethod
    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        دریافت آمار کلی لاگ‌ها.

        Args:
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            دیکشنری شامل آمار:
            - total_logs: تعداد کل لاگ‌ها
            - logs_by_action: تعداد لاگ‌ها به‌تفکیک نوع عملیات
            - logs_by_status: تعداد لاگ‌ها به‌تفکیک وضعیت
            - logs_today: تعداد لاگ‌های امروز
            - logs_this_week: تعداد لاگ‌های این هفته
            - logs_this_month: تعداد لاگ‌های این ماه
            - most_active_users: کاربران با بیشترین لاگ
            - most_common_actions: پرتکرارترین عملیات‌ها
        """
        pass

    @abstractmethod
    async def get_actions_summary(
        self,
        action: Optional[AuditAction] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        دریافت خلاصه عملیات‌ها (گروه‌بندی بر اساس کاربر و موجودیت).

        Args:
            action: نوع عملیات (اختیاری).
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            لیست دیکشنری‌های شامل کاربر، موجودیت، تعداد عملیات.
        """
        pass

    @abstractmethod
    async def get_latest_logs(
        self,
        limit: int = 10,
        action: Optional[AuditAction] = None,
    ) -> List[AuditLog]:
        """
        دریافت آخرین لاگ‌های ثبت‌شده.

        Args:
            limit: حداکثر تعداد لاگ‌ها.
            action: نوع عملیات (اختیاری).

        Returns:
            لیست آخرین لاگ‌ها.
        """
        pass