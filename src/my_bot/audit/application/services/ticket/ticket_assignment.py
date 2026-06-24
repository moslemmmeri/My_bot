# my_bot_project/src/my_bot/application/services/ticket/ticket_assignment.py
"""
سرویس تخصیص تیکت (Ticket Assignment Service).

این سرویس مسئولیت تخصیص تیکت‌های پشتیبانی به ادمین‌ها و اپراتورها
را بر عهده دارد. شامل عملیات‌های تخصیص، تغییر تخصیص، رها کردن تیکت
و تخصیص خودکار بر اساس بار کاری است.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from my_bot.application.dtos.ticket_dto import TicketResponseDTO
from my_bot.core.constants.user_roles import UserRole
from my_bot.core.exceptions.not_found_errors import TicketNotFoundError, UserNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.ticket import Ticket, TicketStatus
from my_bot.domain.interfaces.repositories.ticket_repository import TicketRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface

logger = get_logger(__name__)


class TicketAssignmentService:
    """
    سرویس تخصیص تیکت.

    این کلاس مسئولیت تخصیص تیکت‌های پشتیبانی به ادمین‌ها و اپراتورها را بر عهده دارد.
    """

    def __init__(
        self,
        ticket_repository: TicketRepository,
        user_repository: UserRepository,
        message_publisher: Optional[MessagePublisher] = None,
        cache: Optional[CacheInterface] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس تخصیص تیکت.

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
        self._max_tickets_per_admin = 20  # حداکثر تیکت برای هر ادمین

    async def assign_ticket(
        self,
        ticket_id: int,
        assignee_id: int,
        assigned_by: int,
    ) -> TicketResponseDTO:
        """
        تخصیص یک تیکت به یک ادمین یا اپراتور.

        Args:
            ticket_id: شناسه تیکت.
            assignee_id: شناسه کاربر مسئول (ادمین یا اپراتور).
            assigned_by: شناسه کاربر تخصیص‌دهنده (ادمین).

        Returns:
            TicketResponseDTO: اطلاعات تیکت تخصیص‌یافته.

        Raises:
            TicketNotFoundError: اگر تیکت وجود نداشته باشد.
            UserNotFoundError: اگر کاربر مسئول وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
            ValidationError: اگر کاربر مسئول نقش مناسب نداشته باشد.
        """
        # دریافت تیکت
        ticket = await self._ticket_repository.get_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # بررسی وضعیت تیکت (فقط تیکت‌های باز قابل تخصیص هستند)
        if ticket.status not in (TicketStatus.OPEN, TicketStatus.IN_PROGRESS):
            raise ValidationError(
                message="فقط تیکت‌های باز یا در حال بررسی قابل تخصیص هستند.",
                context={"ticket_id": ticket_id, "status": ticket.status.value},
            )

        # بررسی وجود کاربر مسئول
        assignee = await self._user_repository.get_by_id(assignee_id)
        if not assignee:
            raise UserNotFoundError(user_id=assignee_id)

        # بررسی نقش کاربر مسئول (باید ادمین یا اپراتور باشد)
        if not assignee.role.is_admin_level():
            raise ValidationError(
                message="کاربر مسئول باید دارای نقش ادمین یا اپراتور باشد.",
                context={"assignee_id": assignee_id, "role": assignee.role.value},
            )

        # بررسی دسترسی کاربر تخصیص‌دهنده
        assigner = await self._user_repository.get_by_id(assigned_by)
        if not assigner or not assigner.can_manage_users():
            raise PermissionDeniedError(
                message="شما مجاز به تخصیص تیکت نیستید.",
                context={"assigned_by": assigned_by},
            )

        # بررسی بار کاری کاربر مسئول
        current_assigned = await self._ticket_repository.get_by_assignee(
            assignee_id=assignee_id,
            skip=0,
            limit=1000,
            status=TicketStatus.IN_PROGRESS,
        )
        if len(current_assigned) >= self._max_tickets_per_admin:
            raise ValidationError(
                message=f"کاربر مسئول در حال حاضر {len(current_assigned)} تیکت در حال بررسی دارد.",
                context={"assignee_id": assignee_id, "current_count": len(current_assigned), "max": self._max_tickets_per_admin},
            )

        # تخصیص تیکت
        updated_ticket = await self._ticket_repository.assign_to(ticket_id, assignee_id)
        if not updated_ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # اگر تیکت در وضعیت OPEN بود، به IN_PROGRESS تغییر می‌دهیم
        if updated_ticket.status == TicketStatus.OPEN:
            updated_ticket.status = TicketStatus.IN_PROGRESS
            updated_ticket = await self._ticket_repository.save(updated_ticket)

        logger.info(f"Ticket {ticket_id} assigned to user {assignee_id} by {assigned_by}")

        # انتشار رویداد تخصیص تیکت
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="ticket.assigned",
                event_data={
                    "ticket_id": ticket_id,
                    "assignee_id": assignee_id,
                    "assigned_by": assigned_by,
                    "subject": updated_ticket.subject,
                },
                source="TicketAssignmentService",
            )

            # ارسال نوتیفیکیشن به کاربر مسئول
            await self._message_publisher.publish_notification(
                user_id=assignee_id,
                notification_type="ticket_assigned",
                data={
                    "ticket_id": ticket_id,
                    "subject": updated_ticket.subject,
                    "assigned_by": assigner.full_name if assigner else assigned_by,
                },
            )

        # حذف کش
        if self._cache:
            await self._cache.delete(f"ticket:{ticket_id}")

        return TicketResponseDTO.from_entity(updated_ticket)

    async def unassign_ticket(
        self,
        ticket_id: int,
        unassigned_by: int,
    ) -> TicketResponseDTO:
        """
        رها کردن یک تیکت (حذف تخصیص).

        Args:
            ticket_id: شناسه تیکت.
            unassigned_by: شناسه کاربر رهاکننده (ادمین یا خود کاربر مسئول).

        Returns:
            TicketResponseDTO: اطلاعات تیکت رها شده.

        Raises:
            TicketNotFoundError: اگر تیکت وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
            ValidationError: اگر تیکت تخصیص داده نشده باشد.
        """
        # دریافت تیکت
        ticket = await self._ticket_repository.get_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # بررسی تخصیص
        if not ticket.assigned_to:
            raise ValidationError(
                message="این تیکت تخصیص داده نشده است.",
                context={"ticket_id": ticket_id},
            )

        # بررسی دسترسی
        user = await self._user_repository.get_by_id(unassigned_by)
        if not user:
            raise UserNotFoundError(user_id=unassigned_by)

        # فقط ادمین یا خود کاربر مسئول می‌تواند تیکت را رها کند
        if ticket.assigned_to != unassigned_by and not user.can_manage_users():
            raise PermissionDeniedError(
                message="شما مجاز به رها کردن این تیکت نیستید.",
                context={"ticket_id": ticket_id, "unassigned_by": unassigned_by},
            )

        # رها کردن تیکت
        updated_ticket = await self._ticket_repository.assign_to(ticket_id, 0)
        if not updated_ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # تغییر وضعیت به OPEN
        updated_ticket.status = TicketStatus.OPEN
        updated_ticket = await self._ticket_repository.save(updated_ticket)

        logger.info(f"Ticket {ticket_id} unassigned by {unassigned_by}")

        # انتشار رویداد رها کردن تیکت
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="ticket.unassigned",
                event_data={
                    "ticket_id": ticket_id,
                    "unassigned_by": unassigned_by,
                    "previous_assignee": ticket.assigned_to,
                },
                source="TicketAssignmentService",
            )

        # حذف کش
        if self._cache:
            await self._cache.delete(f"ticket:{ticket_id}")

        return TicketResponseDTO.from_entity(updated_ticket)

    async def reassign_ticket(
        self,
        ticket_id: int,
        new_assignee_id: int,
        reassigned_by: int,
    ) -> TicketResponseDTO:
        """
        تغییر تخصیص تیکت از یک ادمین به ادمین دیگر.

        Args:
            ticket_id: شناسه تیکت.
            new_assignee_id: شناسه کاربر مسئول جدید.
            reassigned_by: شناسه کاربر تغییردهنده (ادمین).

        Returns:
            TicketResponseDTO: اطلاعات تیکت با تخصیص جدید.

        Raises:
            TicketNotFoundError: اگر تیکت وجود نداشته باشد.
            UserNotFoundError: اگر کاربر جدید وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # ابتدا تیکت را رها می‌کنیم
        await self.unassign_ticket(ticket_id, reassigned_by)

        # سپس تخصیص جدید انجام می‌دهیم
        return await self.assign_ticket(ticket_id, new_assignee_id, reassigned_by)

    async def get_assigned_tickets(
        self,
        assignee_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TicketStatus] = None,
    ) -> List[TicketResponseDTO]:
        """
        دریافت تیکت‌های تخصیص‌یافته به یک کاربر.

        Args:
            assignee_id: شناسه کاربر مسئول.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            status: فیلتر بر اساس وضعیت (اختیاری).

        Returns:
            List[TicketResponseDTO]: لیست تیکت‌های تخصیص‌یافته.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        # بررسی وجود کاربر
        user = await self._user_repository.get_by_id(assignee_id)
        if not user:
            raise UserNotFoundError(user_id=assignee_id)

        tickets = await self._ticket_repository.get_by_assignee(
            assignee_id=assignee_id,
            skip=skip,
            limit=limit,
            status=status,
        )

        return [TicketResponseDTO.from_entity(ticket) for ticket in tickets]

    async def get_unassigned_tickets(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TicketResponseDTO]:
        """
        دریافت تیکت‌های بدون تخصیص (OPEN).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[TicketResponseDTO]: لیست تیکت‌های بدون تخصیص.
        """
        tickets = await self._ticket_repository.get_by_assignee(
            assignee_id=0,
            skip=skip,
            limit=limit,
            status=TicketStatus.OPEN,
        )
        return [TicketResponseDTO.from_entity(ticket) for ticket in tickets]

    async def get_assignee_statistics(
        self,
        assignee_id: int,
    ) -> Dict[str, Any]:
        """
        دریافت آمار تخصیص‌های یک کاربر.

        Args:
            assignee_id: شناسه کاربر مسئول.

        Returns:
            Dict[str, Any]: آمار تخصیص‌ها.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        # بررسی وجود کاربر
        user = await self._user_repository.get_by_id(assignee_id)
        if not user:
            raise UserNotFoundError(user_id=assignee_id)

        # دریافت تمام تیکت‌های تخصیص‌یافته
        tickets = await self._ticket_repository.get_by_assignee(
            assignee_id=assignee_id,
            skip=0,
            limit=10000,
        )

        total = len(tickets)
        open_count = sum(1 for t in tickets if t.status == TicketStatus.OPEN)
        in_progress_count = sum(1 for t in tickets if t.status == TicketStatus.IN_PROGRESS)
        resolved_count = sum(1 for t in tickets if t.status == TicketStatus.RESOLVED)
        closed_count = sum(1 for t in tickets if t.status == TicketStatus.CLOSED)

        # محاسبه میانگین زمان حل (برای تیکت‌های حل شده)
        resolution_times = []
        for ticket in tickets:
            if ticket.resolved_at and ticket.created_at:
                resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600  # ساعت
                resolution_times.append(resolution_time)

        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0

        return {
            "assignee_id": assignee_id,
            "assignee_name": user.full_name,
            "total_assigned": total,
            "open": open_count,
            "in_progress": in_progress_count,
            "resolved": resolved_count,
            "closed": closed_count,
            "average_resolution_time_hours": avg_resolution_time,
            "load_percentage": (in_progress_count / self._max_tickets_per_admin) * 100 if self._max_tickets_per_admin > 0 else 0,
        }

    async def get_all_assignees_stats(self) -> List[Dict[str, Any]]:
        """
        دریافت آمار تخصیص برای تمام ادمین‌ها و اپراتورها.

        Returns:
            List[Dict[str, Any]]: لیست آمار هر کاربر.
        """
        # دریافت تمام کاربران با نقش ادمین و اپراتور
        admin_users = await self._user_repository.get_by_role(
            role=UserRole.ADMIN,
            skip=0,
            limit=1000,
        )
        manager_users = await self._user_repository.get_by_role(
            role=UserRole.MANAGER,
            skip=0,
            limit=1000,
        )
        operator_users = await self._user_repository.get_by_role(
            role=UserRole.OPERATOR,
            skip=0,
            limit=1000,
        )

        all_staff = admin_users + manager_users + operator_users
        stats = []

        for user in all_staff:
            if user.id:
                stat = await self.get_assignee_statistics(user.id)
                stats.append(stat)

        # مرتب‌سازی بر اساس بار کاری (نزولی)
        stats.sort(key=lambda x: x.get("in_progress", 0), reverse=True)

        return stats

    async def auto_assign_ticket(
        self,
        ticket_id: int,
        assigned_by: int,
    ) -> Optional[TicketResponseDTO]:
        """
        تخصیص خودکار یک تیکت به بهترین ادمین یا اپراتور موجود.

        الگوریتم: کاربری با کمترین بار کاری انتخاب می‌شود.

        Args:
            ticket_id: شناسه تیکت.
            assigned_by: شناسه کاربر تخصیص‌دهنده (ادمین).

        Returns:
            Optional[TicketResponseDTO]: اطلاعات تیکت تخصیص‌یافته یا None در صورت عدم وجود ادمین.

        Raises:
            TicketNotFoundError: اگر تیکت وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # دریافت تیکت
        ticket = await self._ticket_repository.get_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # بررسی دسترسی
        user = await self._user_repository.get_by_id(assigned_by)
        if not user or not user.can_manage_users():
            raise PermissionDeniedError(
                message="شما مجاز به تخصیص خودکار تیکت نیستید.",
                context={"assigned_by": assigned_by},
            )

        # دریافت تمام ادمین‌ها و اپراتورها
        admin_users = await self._user_repository.get_by_role(
            role=UserRole.ADMIN,
            skip=0,
            limit=1000,
        )
        manager_users = await self._user_repository.get_by_role(
            role=UserRole.MANAGER,
            skip=0,
            limit=1000,
        )
        operator_users = await self._user_repository.get_by_role(
            role=UserRole.OPERATOR,
            skip=0,
            limit=1000,
        )

        all_staff = admin_users + manager_users + operator_users

        if not all_staff:
            logger.warning("No staff available for auto-assignment.")
            return None

        # محاسبه بار کاری هر کاربر
        best_user = None
        best_load = float("inf")

        for staff in all_staff:
            if not staff.id:
                continue

            # دریافت تعداد تیکت‌های در حال بررسی
            assigned_tickets = await self._ticket_repository.get_by_assignee(
                assignee_id=staff.id,
                skip=0,
                limit=1000,
                status=TicketStatus.IN_PROGRESS,
            )
            load = len(assigned_tickets)

            if load < best_load and load < self._max_tickets_per_admin:
                best_load = load
                best_user = staff

        if not best_user or not best_user.id:
            logger.warning("No available staff found for auto-assignment.")
            return None

        # تخصیص به بهترین کاربر
        return await self.assign_ticket(
            ticket_id=ticket_id,
            assignee_id=best_user.id,
            assigned_by=assigned_by,
        )

    async def get_load_balancing_suggestion(self) -> Dict[str, Any]:
        """
        دریافت پیشنهادات برای توزیع متوازن تیکت‌ها بین ادمین‌ها.

        Returns:
            Dict[str, Any]: پیشنهادات توزیع بار.
        """
        stats = await self.get_all_assignees_stats()

        if not stats:
            return {
                "message": "هیچ ادمین یا اپراتوری در سیستم وجود ندارد.",
                "suggestions": [],
            }

        # محاسبه میانگین بار
        total_load = sum(s.get("in_progress", 0) for s in stats)
        avg_load = total_load / len(stats) if stats else 0

        suggestions = []
        for stat in stats:
            load = stat.get("in_progress", 0)
            if load > avg_load + 5:  # اگر بار بیشتر از میانگین + ۵ باشد
                suggestions.append({
                    "assignee_id": stat["assignee_id"],
                    "name": stat["assignee_name"],
                    "current_load": load,
                    "suggestion": "بار کاری بالا است. پیشنهاد می‌شود برخی تیکت‌ها به کاربران دیگر منتقل شوند.",
                })
            elif load < avg_load - 3:  # اگر بار کمتر از میانگین - ۳ باشد
                suggestions.append({
                    "assignee_id": stat["assignee_id"],
                    "name": stat["assignee_name"],
                    "current_load": load,
                    "suggestion": "بار کاری پایین است. می‌تواند تیکت‌های بیشتری را بپذیرد.",
                })

        return {
            "average_load": avg_load,
            "total_staff": len(stats),
            "total_open_tickets": sum(s.get("open", 0) + s.get("in_progress", 0) for s in stats),
            "suggestions": suggestions,
        }

    async def clear_cache(self, ticket_id: Optional[int] = None) -> None:
        """
        پاک کردن کش تخصیص تیکت‌ها.

        Args:
            ticket_id: شناسه تیکت (اختیاری).
        """
        if self._cache:
            if ticket_id:
                await self._cache.delete(f"ticket:{ticket_id}")
            else:
                await self._cache.delete_pattern("ticket:*")
            logger.info(f"Ticket assignment cache cleared for {'ticket ' + str(ticket_id) if ticket_id else 'all tickets'}")