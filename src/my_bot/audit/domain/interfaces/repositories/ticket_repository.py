# my_bot_project/src/my_bot/domain/interfaces/repositories/ticket_repository.py
"""
اینترفیس ریپازیتوری تیکت (Ticket Repository Interface).

این اینترفیس قراردادهای لازم برای ذخیره‌سازی، بازیابی و جستجوی
تیکت‌های پشتیبانی در سیستم را تعریف می‌کند. پیاده‌سازی این اینترفیس
در لایه زیرساخت (Infrastructure) انجام می‌شود.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from my_bot.domain.entities.ticket import Ticket, TicketStatus, TicketPriority, TicketCategory
from my_bot.domain.entities.ticket import TicketMessage


class TicketRepository(ABC):
    """
    اینترفیس ریپازیتوری تیکت.

    این کلاس مسئولیت مدیریت ذخیره‌سازی، بازیابی و جستجوی تیکت‌های
    پشتیبانی در سیستم را بر عهده دارد.
    """

    @abstractmethod
    async def get_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """
        دریافت تیکت با شناسه داخلی (Primary Key).

        Args:
            ticket_id: شناسه تیکت در دیتابیس.

        Returns:
            تیکت در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TicketStatus] = None,
    ) -> List[Ticket]:
        """
        دریافت تیکت‌های یک کاربر خاص.

        Args:
            user_id: شناسه کاربر.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            status: فیلتر بر اساس وضعیت (اختیاری).

        Returns:
            لیست تیکت‌های کاربر.
        """
        pass

    @abstractmethod
    async def get_by_status(
        self,
        status: TicketStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Ticket]:
        """
        دریافت تیکت‌ها با وضعیت مشخص.

        Args:
            status: وضعیت تیکت.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست تیکت‌ها با وضعیت مشخص.
        """
        pass

    @abstractmethod
    async def get_by_assignee(
        self,
        assignee_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TicketStatus] = None,
    ) -> List[Ticket]:
        """
        دریافت تیکت‌های اختصاص‌یافته به یک ادمین خاص.

        Args:
            assignee_id: شناسه کاربر مسئول.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            status: فیلتر بر اساس وضعیت (اختیاری).

        Returns:
            لیست تیکت‌های اختصاص‌یافته.
        """
        pass

    @abstractmethod
    async def get_by_category(
        self,
        category: TicketCategory,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Ticket]:
        """
        دریافت تیکت‌ها با دسته‌بندی مشخص.

        Args:
            category: دسته‌بندی تیکت.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست تیکت‌ها با دسته‌بندی مشخص.
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[Ticket]:
        """
        دریافت لیست تیکت‌ها با صفحه‌بندی.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی، False برای صعودی.

        Returns:
            لیست تیکت‌ها.
        """
        pass

    @abstractmethod
    async def save(self, ticket: Ticket) -> Ticket:
        """
        ذخیره یا به‌روزرسانی یک تیکت در دیتابیس.

        Args:
            ticket: موجودیت تیکت برای ذخیره‌سازی.

        Returns:
            تیکت ذخیره‌شده با شناسه و تاریخ‌های به‌روزرسانی‌شده.
        """
        pass

    @abstractmethod
    async def delete(self, ticket_id: int) -> bool:
        """
        حذف یک تیکت از دیتابیس.

        Args:
            ticket_id: شناسه تیکت برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود تیکت.
        """
        pass

    @abstractmethod
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        شمارش تعداد تیکت‌ها با اعمال فیلترهای اختیاری.

        Args:
            filters: دیکشنری فیلترها (اختیاری).

        Returns:
            تعداد تیکت‌ها.
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        ticket_id: int,
        new_status: TicketStatus,
        reason: Optional[str] = None,
    ) -> Optional[Ticket]:
        """
        به‌روزرسانی وضعیت یک تیکت.

        Args:
            ticket_id: شناسه تیکت.
            new_status: وضعیت جدید.
            reason: دلیل تغییر وضعیت (اختیاری).

        Returns:
            تیکت به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def assign_to(
        self,
        ticket_id: int,
        assignee_id: int,
    ) -> Optional[Ticket]:
        """
        اختصاص تیکت به یک ادمین یا اپراتور.

        Args:
            ticket_id: شناسه تیکت.
            assignee_id: شناسه کاربر مسئول.

        Returns:
            تیکت به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def add_message(
        self,
        ticket_id: int,
        user_id: int,
        message: str,
        is_internal: bool = False,
    ) -> Optional[Ticket]:
        """
        افزودن پیام جدید به تیکت.

        Args:
            ticket_id: شناسه تیکت.
            user_id: شناسه کاربر فرستنده.
            message: متن پیام.
            is_internal: پیام داخلی (فقط برای ادمین‌ها).

        Returns:
            تیکت به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def get_messages(
        self,
        ticket_id: int,
        skip: int = 0,
        limit: int = 100,
        include_internal: bool = False,
    ) -> List[TicketMessage]:
        """
        دریافت پیام‌های یک تیکت.

        Args:
            ticket_id: شناسه تیکت.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            include_internal: شامل پیام‌های داخلی (فقط برای ادمین‌ها).

        Returns:
            لیست پیام‌های تیکت.
        """
        pass

    @abstractmethod
    async def search_tickets(
        self,
        query: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Ticket]:
        """
        جستجوی تیکت‌ها با استفاده از متن (موضوع، توضیحات، پیام‌ها).

        Args:
            query: عبارت جستجو.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست تیکت‌های مطابق با عبارت جستجو.
        """
        pass

    @abstractmethod
    async def get_tickets_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Ticket]:
        """
        دریافت تیکت‌های ایجادشده در بازه زمانی مشخص.

        Args:
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست تیکت‌ها در بازه زمانی.
        """
        pass

    @abstractmethod
    async def get_open_tickets(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Ticket]:
        """
        دریافت تیکت‌های باز (OPEN و IN_PROGRESS).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست تیکت‌های باز.
        """
        pass

    @abstractmethod
    async def get_tickets_needing_response(
        self,
        older_than_hours: int = 24,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Ticket]:
        """
        دریافت تیکت‌هایی که بیش از تعداد ساعت مشخص پاسخ دریافت نکرده‌اند.

        Args:
            older_than_hours: تعداد ساعت‌های عدم پاسخ.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست تیکت‌های نیازمند پاسخ.
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی تیکت‌ها.

        Returns:
            دیکشنری شامل آمار:
            - total_tickets: تعداد کل تیکت‌ها
            - open_tickets: تعداد تیکت‌های باز
            - in_progress_tickets: تعداد تیکت‌های در حال بررسی
            - resolved_tickets: تعداد تیکت‌های حل‌شده
            - closed_tickets: تعداد تیکت‌های بسته‌شده
            - tickets_by_category: تعداد تیکت‌ها به‌تفکیک دسته‌بندی
            - tickets_by_priority: تعداد تیکت‌ها به‌تفکیک اولویت
            - average_resolution_time: میانگین زمان حل (ساعت)
            - tickets_today: تعداد تیکت‌های ایجادشده امروز
        """
        pass

    @abstractmethod
    async def get_tickets_by_priority(
        self,
        priority: TicketPriority,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Ticket]:
        """
        دریافت تیکت‌ها با اولویت مشخص.

        Args:
            priority: اولویت تیکت.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست تیکت‌ها با اولویت مشخص.
        """
        pass

    @abstractmethod
    async def resolve_ticket(self, ticket_id: int, reason: Optional[str] = None) -> Optional[Ticket]:
        """
        حل کردن یک تیکت (تغییر وضعیت به RESOLVED).

        Args:
            ticket_id: شناسه تیکت.
            reason: دلیل حل (اختیاری).

        Returns:
            تیکت به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def close_ticket(self, ticket_id: int, reason: Optional[str] = None) -> Optional[Ticket]:
        """
        بستن یک تیکت (تغییر وضعیت به CLOSED).

        Args:
            ticket_id: شناسه تیکت.
            reason: دلیل بستن (اختیاری).

        Returns:
            تیکت به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def reopen_ticket(self, ticket_id: int) -> Optional[Ticket]:
        """
        بازگشایی یک تیکت (تغییر وضعیت به OPEN).

        Args:
            ticket_id: شناسه تیکت.

        Returns:
            تیکت به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass