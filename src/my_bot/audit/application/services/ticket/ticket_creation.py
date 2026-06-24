# my_bot_project/src/my_bot/application/services/ticket/ticket_creation.py
"""
سرویس ایجاد تیکت پشتیبانی (Ticket Creation Service).

این سرویس مسئولیت ایجاد تیکت‌های جدید در سیستم را بر عهده دارد.
شامل اعتبارسنجی، ذخیره‌سازی، انتشار رویدادها و ارسال نوتیفیکیشن‌ها است.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from my_bot.application.dtos.ticket_dto import (
    TicketCreateDTO,
    TicketUpdateDTO,
    TicketResponseDTO,
    TicketMessageDTO,
)
from my_bot.core.exceptions.not_found_errors import TicketNotFoundError, UserNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.ticket import Ticket, TicketStatus, TicketPriority, TicketCategory
from my_bot.domain.entities.ticket import TicketMessage
from my_bot.domain.interfaces.repositories.ticket_repository import TicketRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface

logger = get_logger(__name__)


class TicketCreationService:
    """
    سرویس ایجاد تیکت پشتیبانی.

    این کلاس مسئولیت ایجاد تیکت‌های جدید و مدیریت اولیه آنها را بر عهده دارد.
    """

    def __init__(
        self,
        ticket_repository: TicketRepository,
        user_repository: UserRepository,
        message_publisher: Optional[MessagePublisher] = None,
        cache: Optional[CacheInterface] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس ایجاد تیکت.

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

    async def create_ticket(
        self,
        data: TicketCreateDTO,
        user_id: int,
    ) -> TicketResponseDTO:
        """
        ایجاد یک تیکت جدید در سیستم.

        Args:
            data: اطلاعات تیکت (DTO).
            user_id: شناسه کاربر ایجادکننده.

        Returns:
            TicketResponseDTO: اطلاعات تیکت ایجادشده.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
            ValidationError: اگر داده‌ها نامعتبر باشند.
        """
        # بررسی وجود کاربر
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # اعتبارسنجی داده‌ها
        if not data.subject or not data.subject.strip():
            raise ValidationError(
                message="موضوع تیکت نمی‌تواند خالی باشد.",
                context={"user_id": user_id},
            )

        if not data.description or not data.description.strip():
            raise ValidationError(
                message="شرح تیکت نمی‌تواند خالی باشد.",
                context={"user_id": user_id},
            )

        # تبدیل Enumها
        try:
            priority = TicketPriority(data.priority) if data.priority else TicketPriority.MEDIUM
        except ValueError:
            raise ValidationError(
                message=f"اولویت '{data.priority}' نامعتبر است.",
                context={"priority": data.priority},
            )

        try:
            category = TicketCategory(data.category) if data.category else TicketCategory.GENERAL
        except ValueError:
            raise ValidationError(
                message=f"دسته‌بندی '{data.category}' نامعتبر است.",
                context={"category": data.category},
            )

        # ایجاد موجودیت تیکت
        ticket = Ticket(
            user_id=user_id,
            subject=data.subject,
            description=data.description,
            priority=priority,
            category=category,
            status=TicketStatus.OPEN,
            metadata=data.metadata,
        )

        # ذخیره در دیتابیس
        saved_ticket = await self._ticket_repository.save(ticket)

        # اگر پیام اولیه وجود دارد، به تیکت اضافه می‌کنیم
        if data.initial_message:
            await self._ticket_repository.add_message(
                ticket_id=saved_ticket.id or 0,
                user_id=user_id,
                message=data.initial_message,
                is_internal=False,
            )

        logger.info(f"Ticket created: id={saved_ticket.id}, user={user_id}, subject={saved_ticket.subject}")

        # انتشار رویداد ایجاد تیکت
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="ticket.created",
                event_data={
                    "ticket_id": saved_ticket.id,
                    "user_id": user_id,
                    "subject": saved_ticket.subject,
                    "priority": saved_ticket.priority.value,
                    "category": saved_ticket.category.value,
                },
                source="TicketCreationService",
            )

            # ارسال نوتیفیکیشن به ادمین‌ها (در صورت وجود)
            # در اینجا می‌توان لیست ادمین‌ها را دریافت و به همه نوتیفیکیشن ارسال کرد
            # برای سادگی، فقط یک رویداد عمومی منتشر می‌کنیم

        # ذخیره در کش
        if self._cache:
            await self._cache.set(
                f"ticket:{saved_ticket.id}",
                saved_ticket.to_dict(),
                ttl=self._cache_ttl,
            )

        return TicketResponseDTO.from_entity(saved_ticket)

    async def get_ticket(
        self,
        ticket_id: int,
        user_id: Optional[int] = None,
    ) -> TicketResponseDTO:
        """
        دریافت اطلاعات یک تیکت.

        Args:
            ticket_id: شناسه تیکت.
            user_id: شناسه کاربر (برای بررسی دسترسی، اختیاری).

        Returns:
            TicketResponseDTO: اطلاعات تیکت.

        Raises:
            TicketNotFoundError: اگر تیکت وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # تلاش از کش
        if self._cache:
            cached = await self._cache.get(f"ticket:{ticket_id}")
            if cached:
                try:
                    ticket = Ticket.from_dict(cached)
                    # بررسی دسترسی
                    if user_id is not None and ticket.user_id != user_id:
                        # بررسی ادمین بودن کاربر
                        user = await self._user_repository.get_by_id(user_id)
                        if not user or not user.is_admin():
                            raise PermissionDeniedError(
                                message="شما مجاز به مشاهده این تیکت نیستید.",
                                context={"ticket_id": ticket_id, "user_id": user_id},
                            )
                    return TicketResponseDTO.from_entity(ticket)
                except Exception:
                    # اگر داده‌های کش نامعتبر بود، از دیتابیس می‌خوانیم
                    pass

        # دریافت از دیتابیس
        ticket = await self._ticket_repository.get_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # بررسی دسترسی
        if user_id is not None and ticket.user_id != user_id:
            user = await self._user_repository.get_by_id(user_id)
            if not user or not user.is_admin():
                raise PermissionDeniedError(
                    message="شما مجاز به مشاهده این تیکت نیستید.",
                    context={"ticket_id": ticket_id, "user_id": user_id},
                )

        # ذخیره در کش
        if self._cache:
            await self._cache.set(
                f"ticket:{ticket_id}",
                ticket.to_dict(),
                ttl=self._cache_ttl,
            )

        return TicketResponseDTO.from_entity(ticket)

    async def get_user_tickets(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        status: Optional[TicketStatus] = None,
    ) -> List[TicketResponseDTO]:
        """
        دریافت لیست تیکت‌های یک کاربر.

        Args:
            user_id: شناسه کاربر.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            status: فیلتر بر اساس وضعیت (اختیاری).

        Returns:
            List[TicketResponseDTO]: لیست تیکت‌های کاربر.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        tickets = await self._ticket_repository.get_by_user_id(
            user_id=user_id,
            skip=skip,
            limit=limit,
            status=status,
        )

        return [TicketResponseDTO.from_entity(ticket) for ticket in tickets]

    async def get_all_tickets(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        category: Optional[TicketCategory] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[TicketResponseDTO]:
        """
        دریافت لیست تمام تیکت‌ها (فقط برای ادمین‌ها).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            status: فیلتر بر اساس وضعیت (اختیاری).
            priority: فیلتر بر اساس اولویت (اختیاری).
            category: فیلتر بر اساس دسته‌بندی (اختیاری).
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی، False برای صعودی.

        Returns:
            List[TicketResponseDTO]: لیست تیکت‌ها.
        """
        tickets = await self._ticket_repository.get_all(
            skip=skip,
            limit=limit,
            order_by=order_by,
            order_desc=order_desc,
        )

        # اعمال فیلترهای اضافی
        if status:
            tickets = [t for t in tickets if t.status == status]
        if priority:
            tickets = [t for t in tickets if t.priority == priority]
        if category:
            tickets = [t for t in tickets if t.category == category]

        return [TicketResponseDTO.from_entity(ticket) for ticket in tickets]

    async def add_message(
        self,
        ticket_id: int,
        user_id: int,
        message: str,
        is_internal: bool = False,
    ) -> TicketResponseDTO:
        """
        افزودن پیام به یک تیکت.

        Args:
            ticket_id: شناسه تیکت.
            user_id: شناسه کاربر فرستنده.
            message: متن پیام.
            is_internal: پیام داخلی (فقط برای ادمین‌ها).

        Returns:
            TicketResponseDTO: اطلاعات تیکت به‌روزرسانی‌شده.

        Raises:
            TicketNotFoundError: اگر تیکت وجود نداشته باشد.
            ValidationError: اگر پیام خالی باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # دریافت تیکت
        ticket = await self._ticket_repository.get_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # بررسی دسترسی
        if ticket.user_id != user_id:
            user = await self._user_repository.get_by_id(user_id)
            if not user or not user.is_admin():
                raise PermissionDeniedError(
                    message="شما مجاز به ارسال پیام در این تیکت نیستید.",
                    context={"ticket_id": ticket_id, "user_id": user_id},
                )

        # اعتبارسنجی پیام
        if not message or not message.strip():
            raise ValidationError(
                message="متن پیام نمی‌تواند خالی باشد.",
                context={"ticket_id": ticket_id},
            )

        # افزودن پیام
        updated_ticket = await self._ticket_repository.add_message(
            ticket_id=ticket_id,
            user_id=user_id,
            message=message,
            is_internal=is_internal,
        )

        if not updated_ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        logger.info(f"Message added to ticket {ticket_id} by user {user_id}")

        # انتشار رویداد پیام جدید
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="ticket.message_added",
                event_data={
                    "ticket_id": ticket_id,
                    "user_id": user_id,
                    "is_internal": is_internal,
                    "message_preview": message[:50] + "..." if len(message) > 50 else message,
                },
                source="TicketCreationService",
            )

        # حذف کش
        if self._cache:
            await self._cache.delete(f"ticket:{ticket_id}")

        return TicketResponseDTO.from_entity(updated_ticket)

    async def search_tickets(
        self,
        query: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[TicketResponseDTO]:
        """
        جستجوی تیکت‌ها با استفاده از متن (موضوع، توضیحات، پیام‌ها).

        Args:
            query: عبارت جستجو.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[TicketResponseDTO]: لیست تیکت‌های مطابق با جستجو.
        """
        tickets = await self._ticket_repository.search_tickets(
            query=query,
            skip=skip,
            limit=limit,
        )
        return [TicketResponseDTO.from_entity(ticket) for ticket in tickets]

    async def get_ticket_messages(
        self,
        ticket_id: int,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TicketMessageDTO]:
        """
        دریافت پیام‌های یک تیکت.

        Args:
            ticket_id: شناسه تیکت.
            user_id: شناسه کاربر (برای بررسی دسترسی).
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[TicketMessageDTO]: لیست پیام‌های تیکت.

        Raises:
            TicketNotFoundError: اگر تیکت وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # دریافت تیکت
        ticket = await self._ticket_repository.get_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundError(ticket_id=str(ticket_id))

        # بررسی دسترسی
        if user_id is not None and ticket.user_id != user_id:
            user = await self._user_repository.get_by_id(user_id)
            if not user or not user.is_admin():
                raise PermissionDeniedError(
                    message="شما مجاز به مشاهده پیام‌های این تیکت نیستید.",
                    context={"ticket_id": ticket_id, "user_id": user_id},
                )

        # تعیین اینکه آیا پیام‌های داخلی نمایش داده شوند
        include_internal = False
        if user_id is not None:
            user = await self._user_repository.get_by_id(user_id)
            if user and user.is_admin():
                include_internal = True

        messages = await self._ticket_repository.get_messages(
            ticket_id=ticket_id,
            skip=skip,
            limit=limit,
            include_internal=include_internal,
        )

        return [TicketMessageDTO.from_entity(msg) for msg in messages]

    async def get_ticket_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی تیکت‌ها.

        Returns:
            Dict[str, Any]: آمار تیکت‌ها.
        """
        return await self._ticket_repository.get_statistics()

    async def get_ticket_count(
        self,
        user_id: Optional[int] = None,
        status: Optional[TicketStatus] = None,
    ) -> int:
        """
        دریافت تعداد تیکت‌ها با فیلترهای اختیاری.

        Args:
            user_id: شناسه کاربر (اختیاری).
            status: وضعیت تیکت (اختیاری).

        Returns:
            int: تعداد تیکت‌ها.
        """
        filters = {}
        if user_id is not None:
            filters["user_id"] = user_id
        if status is not None:
            filters["status"] = status.value

        return await self._ticket_repository.count(filters=filters)

    async def get_open_tickets(self, skip: int = 0, limit: int = 100) -> List[TicketResponseDTO]:
        """
        دریافت تیکت‌های باز (OPEN و IN_PROGRESS).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[TicketResponseDTO]: لیست تیکت‌های باز.
        """
        tickets = await self._ticket_repository.get_open_tickets(
            skip=skip,
            limit=limit,
        )
        return [TicketResponseDTO.from_entity(ticket) for ticket in tickets]

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
            logger.info(f"Ticket cache cleared for {'ticket ' + str(ticket_id) if ticket_id else 'all tickets'}")