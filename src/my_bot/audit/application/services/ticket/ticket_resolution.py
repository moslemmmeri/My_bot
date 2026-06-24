# my_bot_project/src/my_bot/application/services/ticket/ticket_resolution.py
"""
سرویس حل و بستن تیکت (Ticket Resolution Service).

این سرویس مسئولیت حل کردن، بستن و بازگشایی تیکت‌های پشتیبانی را بر عهده دارد.
شامل عملیات‌های تغییر وضعیت به RESOLVED، CLOSED، بازگشایی و دریافت آمار حل است.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from my_bot.application.dtos.ticket_dto import TicketResponseDTO
from my_bot.core.exceptions.not_found_errors import TicketNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.ticket import Ticket, TicketStatus, TicketPriority
from my_bot.domain.interfaces.repositories.ticket_repository import TicketRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface

logger = get_logger(__name__)


class TicketResolutionService:
    """
    سرویس حل و بستن تیکت.

    این کلاس مسئولیت حل کردن، بستن و بازگشایی تیکت‌های پشتیبانی را بر عهده دارد.
    """

    def __init__(
        self,
        ticket_repository: TicketRepository,
        user_repository: UserRepository,
        message_publisher: Optional[MessagePublisher] = None,
        cache: Optional[CacheInterface] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس حل تیکت.

        Args:
            ticket_repository: ریپازیتوری تیکت.
            user_repository: ریپازیتوری کاربر.
            message_publisher: انتشاردهنده پیام (اختیاری).
            cache: کش برای ذخیره‌سازی موقت (اختیاری).
        """
        self._ticket_repository = ticket_repository
        self._user_repository = user_repository
        self._message_publisher = message_publisher
        self._cache = cache
        self._cache_ttl = 300  # 5 دقیقه

    async def resolve_ticket(
        self,
        ticket_id: int,
        resolved_by: int,
        resolution_note: Optional[str] = None,
    ) -> TicketResponseDTO:
        """
        حل کردن یک تیکت (تغییر وضعیت به RESOLVED).

        Args:
            ticket_id: شناسه تیکت.
            resolved_by: شناسه کاربر حل‌کننده (ادمین یا اپراتور).
            resolution_note: توضیح حل (اختیاری).

        Returns:
            TicketResponseDTO: اطلاعات تیکت حل‌شده.

        Raises:
            TicketNotFoundError: اگر تیکت وجود نداشته باشد.
            ValidationError: اگر تیکت قابل حل نباشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # دریافت تیکت
        ticket = await self._ticket_repository.get_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # بررسی وضعیت (فقط تیکت‌های OPEN یا IN_PROGRESS قابل حل هستند)
        if ticket.status not in (TicketStatus.OPEN, TicketStatus.IN_PROGRESS):
            raise ValidationError(
                message="فقط تیکت‌های باز یا در حال بررسی قابل حل هستند.",
                context={"ticket_id": ticket_id, "status": ticket.status.value},
            )

        # بررسی دسترسی (فقط ادمین یا اپراتور یا خود کاربر)
        user = await self._user_repository.get_by_id(resolved_by)
        if not user:
            raise PermissionDeniedError(
                message="کاربر نامعتبر.",
                context={"resolved_by": resolved_by},
            )

        if not user.is_admin_level() and ticket.user_id != resolved_by:
            raise PermissionDeniedError(
                message="شما مجاز به حل این تیکت نیستید.",
                context={"ticket_id": ticket_id, "user_id": resolved_by},
            )

        # حل کردن تیکت
        updated_ticket = await self._ticket_repository.resolve_ticket(
            ticket_id=ticket_id,
            reason=resolution_note,
        )
        if not updated_ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # اضافه کردن پیام حل (اگر توضیح داده شده باشد)
        if resolution_note:
            await self._ticket_repository.add_message(
                ticket_id=ticket_id,
                user_id=resolved_by,
                message=f"تیکت حل شد: {resolution_note}",
                is_internal=True,
            )

        logger.info(f"Ticket {ticket_id} resolved by {resolved_by}")

        # انتشار رویداد حل تیکت
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="ticket.resolved",
                event_data={
                    "ticket_id": ticket_id,
                    "resolved_by": resolved_by,
                    "subject": updated_ticket.subject,
                    "resolution_note": resolution_note,
                },
                source="TicketResolutionService",
            )

            # ارسال نوتیفیکیشن به کاربر صاحب تیکت
            await self._message_publisher.publish_notification(
                user_id=ticket.user_id,
                notification_type="ticket_resolved",
                data={
                    "ticket_id": ticket_id,
                    "subject": updated_ticket.subject,
                    "resolved_by": user.full_name if user else resolved_by,
                },
            )

        # حذف کش
        if self._cache:
            await self._cache.delete(f"ticket:{ticket_id}")

        return TicketResponseDTO.from_entity(updated_ticket)

    async def close_ticket(
        self,
        ticket_id: int,
        closed_by: int,
        close_reason: Optional[str] = None,
    ) -> TicketResponseDTO:
        """
        بستن یک تیکت (تغییر وضعیت به CLOSED).

        تیکت‌های بسته‌شده قابل بازگشایی هستند.

        Args:
            ticket_id: شناسه تیکت.
            closed_by: شناسه کاربر بسته‌کننده (ادمین، اپراتور یا خود کاربر).
            close_reason: دلیل بستن (اختیاری).

        Returns:
            TicketResponseDTO: اطلاعات تیکت بسته‌شده.

        Raises:
            TicketNotFoundError: اگر تیکت وجود نداشته باشد.
            ValidationError: اگر تیکت قابل بستن نباشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # دریافت تیکت
        ticket = await self._ticket_repository.get_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # بررسی وضعیت (فقط تیکت‌های RESOLVED یا CLOSED قابل بستن نیستند، بلکه هر وضعیتی جز CLOSED قابل بستن است)
        if ticket.status == TicketStatus.CLOSED:
            raise ValidationError(
                message="تیکت قبلاً بسته شده است.",
                context={"ticket_id": ticket_id},
            )

        # بررسی دسترسی (فقط ادمین، اپراتور یا خود کاربر)
        user = await self._user_repository.get_by_id(closed_by)
        if not user:
            raise PermissionDeniedError(
                message="کاربر نامعتبر.",
                context={"closed_by": closed_by},
            )

        if not user.is_admin_level() and ticket.user_id != closed_by:
            raise PermissionDeniedError(
                message="شما مجاز به بستن این تیکت نیستید.",
                context={"ticket_id": ticket_id, "user_id": closed_by},
            )

        # بستن تیکت
        updated_ticket = await self._ticket_repository.close_ticket(
            ticket_id=ticket_id,
            reason=close_reason,
        )
        if not updated_ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # اضافه کردن پیام بستن
        if close_reason:
            await self._ticket_repository.add_message(
                ticket_id=ticket_id,
                user_id=closed_by,
                message=f"تیکت بسته شد: {close_reason}",
                is_internal=True,
            )

        logger.info(f"Ticket {ticket_id} closed by {closed_by}")

        # انتشار رویداد بستن تیکت
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="ticket.closed",
                event_data={
                    "ticket_id": ticket_id,
                    "closed_by": closed_by,
                    "subject": updated_ticket.subject,
                    "close_reason": close_reason,
                },
                source="TicketResolutionService",
            )

            # ارسال نوتیفیکیشن به کاربر صاحب تیکت
            await self._message_publisher.publish_notification(
                user_id=ticket.user_id,
                notification_type="ticket_closed",
                data={
                    "ticket_id": ticket_id,
                    "subject": updated_ticket.subject,
                    "closed_by": user.full_name if user else closed_by,
                },
            )

        # حذف کش
        if self._cache:
            await self._cache.delete(f"ticket:{ticket_id}")

        return TicketResponseDTO.from_entity(updated_ticket)

    async def reopen_ticket(
        self,
        ticket_id: int,
        reopened_by: int,
        reopen_reason: Optional[str] = None,
    ) -> TicketResponseDTO:
        """
        بازگشایی یک تیکت بسته‌شده (تغییر وضعیت به OPEN).

        Args:
            ticket_id: شناسه تیکت.
            reopened_by: شناسه کاربر بازگشایی‌کننده (ادمین، اپراتور یا خود کاربر).
            reopen_reason: دلیل بازگشایی (اختیاری).

        Returns:
            TicketResponseDTO: اطلاعات تیکت بازگشایی‌شده.

        Raises:
            TicketNotFoundError: اگر تیکت وجود نداشته باشد.
            ValidationError: اگر تیکت قابل بازگشایی نباشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # دریافت تیکت
        ticket = await self._ticket_repository.get_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # بررسی وضعیت (فقط تیکت‌های RESOLVED یا CLOSED قابل بازگشایی هستند)
        if ticket.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
            raise ValidationError(
                message="فقط تیکت‌های حل‌شده یا بسته‌شده قابل بازگشایی هستند.",
                context={"ticket_id": ticket_id, "status": ticket.status.value},
            )

        # بررسی دسترسی (فقط ادمین، اپراتور یا خود کاربر)
        user = await self._user_repository.get_by_id(reopened_by)
        if not user:
            raise PermissionDeniedError(
                message="کاربر نامعتبر.",
                context={"reopened_by": reopened_by},
            )

        if not user.is_admin_level() and ticket.user_id != reopened_by:
            raise PermissionDeniedError(
                message="شما مجاز به بازگشایی این تیکت نیستید.",
                context={"ticket_id": ticket_id, "user_id": reopened_by},
            )

        # بازگشایی تیکت
        updated_ticket = await self._ticket_repository.reopen_ticket(ticket_id)
        if not updated_ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # اضافه کردن پیام بازگشایی
        if reopen_reason:
            await self._ticket_repository.add_message(
                ticket_id=ticket_id,
                user_id=reopened_by,
                message=f"تیکت بازگشایی شد: {reopen_reason}",
                is_internal=True,
            )

        logger.info(f"Ticket {ticket_id} reopened by {reopened_by}")

        # انتشار رویداد بازگشایی تیکت
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="ticket.reopened",
                event_data={
                    "ticket_id": ticket_id,
                    "reopened_by": reopened_by,
                    "subject": updated_ticket.subject,
                    "reopen_reason": reopen_reason,
                },
                source="TicketResolutionService",
            )

            # ارسال نوتیفیکیشن به کاربر صاحب تیکت
            await self._message_publisher.publish_notification(
                user_id=ticket.user_id,
                notification_type="ticket_reopened",
                data={
                    "ticket_id": ticket_id,
                    "subject": updated_ticket.subject,
                    "reopened_by": user.full_name if user else reopened_by,
                },
            )

        # حذف کش
        if self._cache:
            await self._cache.delete(f"ticket:{ticket_id}")

        return TicketResponseDTO.from_entity(updated_ticket)

    async def get_resolved_tickets(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
    ) -> List[TicketResponseDTO]:
        """
        دریافت تیکت‌های حل‌شده (RESOLVED).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            user_id: فیلتر بر اساس کاربر (اختیاری).

        Returns:
            List[TicketResponseDTO]: لیست تیکت‌های حل‌شده.
        """
        if user_id:
            tickets = await self._ticket_repository.get_by_user_id(
                user_id=user_id,
                skip=skip,
                limit=limit,
                status=TicketStatus.RESOLVED,
            )
        else:
            tickets = await self._ticket_repository.get_by_status(
                status=TicketStatus.RESOLVED,
                skip=skip,
                limit=limit,
            )
        return [TicketResponseDTO.from_entity(ticket) for ticket in tickets]

    async def get_closed_tickets(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
    ) -> List[TicketResponseDTO]:
        """
        دریافت تیکت‌های بسته‌شده (CLOSED).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            user_id: فیلتر بر اساس کاربر (اختیاری).

        Returns:
            List[TicketResponseDTO]: لیست تیکت‌های بسته‌شده.
        """
        if user_id:
            tickets = await self._ticket_repository.get_by_user_id(
                user_id=user_id,
                skip=skip,
                limit=limit,
                status=TicketStatus.CLOSED,
            )
        else:
            tickets = await self._ticket_repository.get_by_status(
                status=TicketStatus.CLOSED,
                skip=skip,
                limit=limit,
            )
        return [TicketResponseDTO.from_entity(ticket) for ticket in tickets]

    async def get_resolution_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        دریافت آمار حل تیکت‌ها.

        Args:
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            Dict[str, Any]: آمار حل شامل:
                - total_resolved: تعداد کل حل‌شده‌ها
                - total_closed: تعداد کل بسته‌شده‌ها
                - average_resolution_time_hours: میانگین زمان حل (ساعت)
                - resolved_by_priority: توزیع بر اساس اولویت
                - resolved_by_category: توزیع بر اساس دسته‌بندی
        """
        # دریافت تمام تیکت‌های حل‌شده و بسته‌شده
        resolved_tickets = await self._ticket_repository.get_by_status(
            status=TicketStatus.RESOLVED,
            skip=0,
            limit=10000,
        )
        closed_tickets = await self._ticket_repository.get_by_status(
            status=TicketStatus.CLOSED,
            skip=0,
            limit=10000,
        )

        # فیلتر بر اساس تاریخ
        if start_date or end_date:
            resolved_tickets = [
                t for t in resolved_tickets
                if (not start_date or (t.resolved_at and t.resolved_at >= start_date))
                and (not end_date or (t.resolved_at and t.resolved_at <= end_date))
            ]
            closed_tickets = [
                t for t in closed_tickets
                if (not start_date or (t.closed_at and t.closed_at >= start_date))
                and (not end_date or (t.closed_at and t.closed_at <= end_date))
            ]

        total_resolved = len(resolved_tickets)
        total_closed = len(closed_tickets)

        # میانگین زمان حل
        resolution_times = []
        for ticket in resolved_tickets + closed_tickets:
            if ticket.resolved_at and ticket.created_at:
                resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                resolution_times.append(resolution_time)

        avg_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0

        # توزیع بر اساس اولویت
        priority_dist = {}
        for ticket in resolved_tickets + closed_tickets:
            priority = ticket.priority.value
            priority_dist[priority] = priority_dist.get(priority, 0) + 1

        # توزیع بر اساس دسته‌بندی
        category_dist = {}
        for ticket in resolved_tickets + closed_tickets:
            category = ticket.category.value
            category_dist[category] = category_dist.get(category, 0) + 1

        return {
            "total_resolved": total_resolved,
            "total_closed": total_closed,
            "average_resolution_time_hours": avg_time,
            "resolved_by_priority": priority_dist,
            "resolved_by_category": category_dist,
        }

    async def get_my_resolved_tickets(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TicketResponseDTO]:
        """
        دریافت تیکت‌های حل‌شده یا بسته‌شده یک کاربر خاص.

        Args:
            user_id: شناسه کاربر.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[TicketResponseDTO]: لیست تیکت‌های حل‌شده کاربر.
        """
        tickets = await self._ticket_repository.get_by_user_id(
            user_id=user_id,
            skip=skip,
            limit=limit,
            status=TicketStatus.RESOLVED,
        )
        # همچنین تیکت‌های بسته‌شده را هم اضافه می‌کنیم
        closed_tickets = await self._ticket_repository.get_by_user_id(
            user_id=user_id,
            skip=0,
            limit=100,
            status=TicketStatus.CLOSED,
        )
        all_tickets = tickets + closed_tickets
        # مرتب‌سازی بر اساس تاریخ حل (نزولی)
        all_tickets.sort(key=lambda t: t.resolved_at or t.closed_at or t.created_at, reverse=True)
        # صفحه‌بندی
        return [TicketResponseDTO.from_entity(t) for t in all_tickets[skip:skip+limit]]

    async def clear_cache(self, ticket_id: Optional[int] = None) -> None:
        """
        پاک کردن کش تیکت‌ها.

        Args:
            ticket_id: شناسه تیکت (اختیاری).
        """
        if self._cache:
            if ticket_id:
                await self._cache.delete(f"ticket:{ticket_id}")
            else:
                await self._cache.delete_pattern("ticket:*")
            logger.info(f"Ticket resolution cache cleared for {'ticket ' + str(ticket_id) if ticket_id else 'all tickets'}")