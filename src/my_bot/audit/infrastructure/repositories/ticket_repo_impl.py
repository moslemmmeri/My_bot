# my_bot_project/src/my_bot/infrastructure/repositories/ticket_repo_impl.py
"""
پیاده‌سازی ریپازیتوری تیکت (Ticket Repository Implementation).

این کلاس پیاده‌سازی عینی از اینترفیس TicketRepository است که با استفاده
از SQLAlchemy و DatabaseSessionManager، عملیات CRUD و جستجو روی
جداول tickets و ticket_messages را انجام می‌دهد.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, delete, update, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from my_bot.core.exceptions.db_errors import DatabaseError, QueryError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.ticket import Ticket, TicketStatus, TicketPriority, TicketCategory
from my_bot.domain.entities.ticket import TicketMessage
from my_bot.domain.interfaces.repositories.ticket_repository import TicketRepository
from my_bot.infrastructure.database.models.ticket_model import TicketModel
from my_bot.infrastructure.database.models.ticket_message_model import TicketMessageModel
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager

logger = get_logger(__name__)


class TicketRepositoryImpl(TicketRepository):
    """
    پیاده‌سازی ریپازیتوری تیکت با استفاده از SQLAlchemy.

    این کلاس تمام متدهای اینترفیس TicketRepository را پیاده‌سازی می‌کند
    و از DatabaseSessionManager برای دریافت جلسات دیتابیس استفاده می‌کند.

    Attributes:
        session_manager: مدیر جلسات دیتابیس.
    """

    def __init__(self, session_manager: DatabaseSessionManager) -> None:
        """
        مقداردهی اولیه ریپازیتوری.

        Args:
            session_manager: مدیر جلسات دیتابیس.
        """
        self._session_manager = session_manager
        logger.info("TicketRepositoryImpl initialized.")

    # ----------------------------------------------
    # متدهای اصلی CRUD
    # ----------------------------------------------

    async def get_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """
        دریافت تیکت با شناسه داخلی.

        Args:
            ticket_id: شناسه تیکت در دیتابیس.

        Returns:
            تیکت در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(TicketModel)
                    .where(TicketModel.id == ticket_id)
                    .options(
                        selectinload(TicketModel.user),
                        selectinload(TicketModel.assignee),
                        selectinload(TicketModel.messages),
                    )
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting ticket by id {ticket_id}: {e}")
                raise QueryError(
                    query="SELECT tickets WHERE id = :ticket_id",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = select(TicketModel).where(TicketModel.user_id == user_id)
                if status:
                    stmt = stmt.where(TicketModel.status == status.value)
                stmt = (
                    stmt.options(
                        selectinload(TicketModel.user),
                        selectinload(TicketModel.assignee),
                        selectinload(TicketModel.messages),
                    )
                    .order_by(desc(TicketModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting tickets for user {user_id}: {e}")
                raise QueryError(
                    query="SELECT tickets WHERE user_id = :user_id",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(TicketModel)
                    .where(TicketModel.status == status.value)
                    .options(
                        selectinload(TicketModel.user),
                        selectinload(TicketModel.assignee),
                        selectinload(TicketModel.messages),
                    )
                    .order_by(desc(TicketModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting tickets by status {status.value}: {e}")
                raise QueryError(
                    query="SELECT tickets WHERE status = :status",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = select(TicketModel).where(TicketModel.assigned_to == assignee_id)
                if status:
                    stmt = stmt.where(TicketModel.status == status.value)
                stmt = (
                    stmt.options(
                        selectinload(TicketModel.user),
                        selectinload(TicketModel.assignee),
                        selectinload(TicketModel.messages),
                    )
                    .order_by(desc(TicketModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting tickets for assignee {assignee_id}: {e}")
                raise QueryError(
                    query="SELECT tickets WHERE assigned_to = :assignee_id",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(TicketModel)
                    .where(TicketModel.category == category.value)
                    .options(
                        selectinload(TicketModel.user),
                        selectinload(TicketModel.assignee),
                        selectinload(TicketModel.messages),
                    )
                    .order_by(desc(TicketModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting tickets by category {category.value}: {e}")
                raise QueryError(
                    query="SELECT tickets WHERE category = :category",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                order_col = getattr(TicketModel, order_by, TicketModel.created_at)
                order_expr = order_col.desc() if order_desc else order_col.asc()

                stmt = (
                    select(TicketModel)
                    .options(
                        selectinload(TicketModel.user),
                        selectinload(TicketModel.assignee),
                        selectinload(TicketModel.messages),
                    )
                    .order_by(order_expr)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting all tickets: {e}")
                raise QueryError(
                    query="SELECT tickets WITH pagination",
                    reason=str(e),
                )

    async def save(self, ticket: Ticket) -> Ticket:
        """
        ذخیره یا به‌روزرسانی یک تیکت در دیتابیس.

        Args:
            ticket: موجودیت تیکت برای ذخیره‌سازی.

        Returns:
            تیکت ذخیره‌شده با شناسه و تاریخ‌های به‌روزرسانی‌شده.
        """
        async with self._session_manager.session() as session:
            try:
                if ticket.id:
                    # به‌روزرسانی
                    stmt = (
                        update(TicketModel)
                        .where(TicketModel.id == ticket.id)
                        .values(
                            user_id=ticket.user_id,
                            subject=ticket.subject,
                            description=ticket.description,
                            status=ticket.status.value if ticket.status else TicketStatus.OPEN.value,
                            priority=ticket.priority.value if ticket.priority else TicketPriority.MEDIUM.value,
                            category=ticket.category.value if ticket.category else TicketCategory.GENERAL.value,
                            assigned_to=ticket.assigned_to,
                            resolved_at=ticket.resolved_at,
                            closed_at=ticket.closed_at,
                            updated_at=datetime.now(),
                            metadata=ticket.metadata,
                        )
                        .returning(TicketModel)
                    )
                    result = await session.execute(stmt)
                    model = result.scalar_one_or_none()
                    await session.commit()
                    if model:
                        logger.debug(f"Ticket updated: id={model.id}")
                        return model.to_domain()
                    raise DatabaseError(
                        message=f"Ticket with id {ticket.id} not found for update.",
                        context={"ticket_id": ticket.id},
                    )
                else:
                    # ایجاد جدید
                    model = TicketModel.from_domain(ticket)
                    session.add(model)
                    await session.commit()
                    await session.refresh(model)
                    logger.info(f"Ticket created: id={model.id}, subject={model.subject}")
                    return model.to_domain()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving ticket: {e}")
                raise DatabaseError(
                    message=f"خطا در ذخیره‌سازی تیکت: {str(e)}",
                    context={"ticket_id": ticket.id, "subject": ticket.subject},
                )

    async def delete(self, ticket_id: int) -> bool:
        """
        حذف یک تیکت از دیتابیس.

        Args:
            ticket_id: شناسه تیکت برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود تیکت.
        """
        async with self._session_manager.session() as session:
            try:
                # پیام‌ها به‌صورت خودکار با CASCADE حذف می‌شوند
                stmt = delete(TicketModel).where(TicketModel.id == ticket_id)
                result = await session.execute(stmt)
                await session.commit()
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Ticket deleted: id={ticket_id}")
                else:
                    logger.debug(f"Ticket not found for deletion: id={ticket_id}")
                return deleted
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting ticket {ticket_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در حذف تیکت: {str(e)}",
                    context={"ticket_id": ticket_id},
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(TicketModel)
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        if hasattr(TicketModel, key):
                            conditions.append(getattr(TicketModel, key) == value)
                    if conditions:
                        stmt = stmt.where(and_(*conditions))
                result = await session.execute(stmt)
                return result.scalar_one()
            except Exception as e:
                logger.error(f"Error counting tickets: {e}")
                raise QueryError(
                    query="COUNT tickets WITH filters",
                    reason=str(e),
                )

    # ----------------------------------------------
    # متدهای عملیاتی
    # ----------------------------------------------

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
        async with self._session_manager.session() as session:
            try:
                values = {
                    "status": new_status.value,
                    "updated_at": datetime.now(),
                }
                if new_status == TicketStatus.RESOLVED:
                    values["resolved_at"] = datetime.now()
                if new_status == TicketStatus.CLOSED:
                    values["closed_at"] = datetime.now()
                if reason:
                    values["metadata"] = func.jsonb_set(
                        TicketModel.metadata,
                        "{status_change_reason}",
                        f'"{reason}"',
                    )

                stmt = (
                    update(TicketModel)
                    .where(TicketModel.id == ticket_id)
                    .values(**values)
                    .returning(TicketModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.info(f"Ticket {ticket_id} status updated to {new_status.value}")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating status for ticket {ticket_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در به‌روزرسانی وضعیت تیکت: {str(e)}",
                    context={"ticket_id": ticket_id, "new_status": new_status.value},
                )

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
        async with self._session_manager.session() as session:
            try:
                # اگر assignee_id = 0 باشد، یعنی حذف تخصیص
                assignee_value = None if assignee_id == 0 else assignee_id

                stmt = (
                    update(TicketModel)
                    .where(TicketModel.id == ticket_id)
                    .values(
                        assigned_to=assignee_value,
                        updated_at=datetime.now(),
                    )
                    .returning(TicketModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.debug(f"Ticket {ticket_id} assigned to user {assignee_id}")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error assigning ticket {ticket_id} to user {assignee_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در تخصیص تیکت: {str(e)}",
                    context={"ticket_id": ticket_id, "assignee_id": assignee_id},
                )

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
        async with self._session_manager.session() as session:
            try:
                # ایجاد پیام جدید
                msg_model = TicketMessageModel(
                    ticket_id=ticket_id,
                    user_id=user_id,
                    message=message,
                    is_internal=is_internal,
                    created_at=datetime.now(),
                )
                session.add(msg_model)

                # به‌روزرسانی زمان تیکت
                stmt = (
                    update(TicketModel)
                    .where(TicketModel.id == ticket_id)
                    .values(updated_at=datetime.now())
                    .returning(TicketModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()

                if model:
                    logger.debug(f"Message added to ticket {ticket_id} by user {user_id}")
                    # بارگذاری مجدد با پیام‌ها
                    return await self.get_by_id(ticket_id)
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error adding message to ticket {ticket_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در افزودن پیام به تیکت: {str(e)}",
                    context={"ticket_id": ticket_id, "user_id": user_id},
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = select(TicketMessageModel).where(TicketMessageModel.ticket_id == ticket_id)
                if not include_internal:
                    stmt = stmt.where(TicketMessageModel.is_internal == False)
                stmt = (
                    stmt.order_by(asc(TicketMessageModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting messages for ticket {ticket_id}: {e}")
                raise QueryError(
                    query="SELECT ticket_messages WHERE ticket_id = :ticket_id",
                    reason=str(e),
                )

    # ----------------------------------------------
    # متدهای جستجو و فیلتر
    # ----------------------------------------------

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
        async with self._session_manager.session() as session:
            try:
                search_term = f"%{query}%"

                # جستجو در موضوع و توضیحات
                stmt = (
                    select(TicketModel)
                    .where(
                        or_(
                            TicketModel.subject.ilike(search_term),
                            TicketModel.description.ilike(search_term),
                            # جستجو در پیام‌ها (با استفاده از ساب‌کوئری)
                            TicketModel.id.in_(
                                select(TicketMessageModel.ticket_id)
                                .where(TicketMessageModel.message.ilike(search_term))
                            ),
                        )
                    )
                    .options(
                        selectinload(TicketModel.user),
                        selectinload(TicketModel.assignee),
                        selectinload(TicketModel.messages),
                    )
                    .order_by(desc(TicketModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error searching tickets with query '{query}': {e}")
                raise QueryError(
                    query="SEARCH tickets",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(TicketModel)
                    .where(
                        and_(
                            TicketModel.created_at >= start_date,
                            TicketModel.created_at <= end_date,
                        )
                    )
                    .options(
                        selectinload(TicketModel.user),
                        selectinload(TicketModel.assignee),
                        selectinload(TicketModel.messages),
                    )
                    .order_by(desc(TicketModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting tickets by date range: {e}")
                raise QueryError(
                    query="SELECT tickets by date range",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(TicketModel)
                    .where(
                        TicketModel.status.in_([
                            TicketStatus.OPEN.value,
                            TicketStatus.IN_PROGRESS.value,
                        ])
                    )
                    .options(
                        selectinload(TicketModel.user),
                        selectinload(TicketModel.assignee),
                        selectinload(TicketModel.messages),
                    )
                    .order_by(
                        # اولویت: URGENT, HIGH, MEDIUM, LOW
                        func.field(TicketModel.priority, "urgent", "high", "medium", "low"),
                        desc(TicketModel.created_at),
                    )
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting open tickets: {e}")
                raise QueryError(
                    query="SELECT open tickets",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                cutoff = datetime.now() - timedelta(hours=older_than_hours)

                # تیکت‌هایی که آخرین پیام آنها از طرف کاربر بوده و بیش از cutoff گذشته است
                # و وضعیت آنها OPEN یا IN_PROGRESS است
                subquery = (
                    select(
                        TicketMessageModel.ticket_id,
                        func.max(TicketMessageModel.created_at).label("last_msg_at"),
                        func.array_agg(TicketMessageModel.user_id).label("user_ids"),
                    )
                    .where(
                        TicketMessageModel.is_internal == False
                    )
                    .group_by(TicketMessageModel.ticket_id)
                    .subquery()
                )

                stmt = (
                    select(TicketModel)
                    .join(
                        subquery,
                        TicketModel.id == subquery.c.ticket_id,
                        isouter=True,
                    )
                    .where(
                        and_(
                            TicketModel.status.in_([
                                TicketStatus.OPEN.value,
                                TicketStatus.IN_PROGRESS.value,
                            ]),
                            or_(
                                # تیکت‌هایی که هیچ پیامی ندارند و قدیمی هستند
                                and_(
                                    subquery.c.last_msg_at.is_(None),
                                    TicketModel.created_at <= cutoff,
                                ),
                                # تیکت‌هایی که آخرین پیام آنها از طرف کاربر است و قدیمی است
                                and_(
                                    subquery.c.last_msg_at.is_not(None),
                                    subquery.c.last_msg_at <= cutoff,
                                    # آخرین پیام از طرف کاربر است (نه ادمین)
                                    # این شرط ساده‌سازی شده است
                                ),
                            )
                        )
                    )
                    .options(
                        selectinload(TicketModel.user),
                        selectinload(TicketModel.assignee),
                        selectinload(TicketModel.messages),
                    )
                    .order_by(TicketModel.created_at)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting tickets needing response: {e}")
                raise QueryError(
                    query="SELECT tickets needing response",
                    reason=str(e),
                )

    # ----------------------------------------------
    # متدهای آمار و تحلیل
    # ----------------------------------------------

    async def get_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی تیکت‌ها.

        Returns:
            دیکشنری شامل آمار.
        """
        async with self._session_manager.session() as session:
            try:
                # تعداد کل تیکت‌ها
                total = await session.execute(
                    select(func.count()).select_from(TicketModel)
                )
                total_tickets = total.scalar_one()

                # تیکت‌ها به‌تفکیک وضعیت
                status_counts = {}
                for status in TicketStatus:
                    count = await session.execute(
                        select(func.count()).select_from(TicketModel).where(
                            TicketModel.status == status.value
                        )
                    )
                    status_counts[status.value] = count.scalar_one()

                # تیکت‌ها به‌تفکیک دسته‌بندی
                category_counts = {}
                for category in TicketCategory:
                    count = await session.execute(
                        select(func.count()).select_from(TicketModel).where(
                            TicketModel.category == category.value
                        )
                    )
                    category_counts[category.value] = count.scalar_one()

                # تیکت‌ها به‌تفکیک اولویت
                priority_counts = {}
                for priority in TicketPriority:
                    count = await session.execute(
                        select(func.count()).select_from(TicketModel).where(
                            TicketModel.priority == priority.value
                        )
                    )
                    priority_counts[priority.value] = count.scalar_one()

                # میانگین زمان حل (ساعت)
                resolved_tickets = await session.execute(
                    select(TicketModel.resolved_at, TicketModel.created_at)
                    .where(
                        and_(
                            TicketModel.resolved_at.is_not(None),
                            TicketModel.created_at.is_not(None),
                        )
                    )
                )
                resolution_times = []
                for row in resolved_tickets.all():
                    if row.resolved_at and row.created_at:
                        diff_hours = (row.resolved_at - row.created_at).total_seconds() / 3600
                        resolution_times.append(diff_hours)

                avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0

                # تیکت‌های امروز
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                today = await session.execute(
                    select(func.count()).select_from(TicketModel).where(
                        TicketModel.created_at >= today_start
                    )
                )
                tickets_today = today.scalar_one()

                return {
                    "total_tickets": total_tickets,
                    "open_tickets": status_counts.get(TicketStatus.OPEN.value, 0) + status_counts.get(TicketStatus.IN_PROGRESS.value, 0),
                    "in_progress_tickets": status_counts.get(TicketStatus.IN_PROGRESS.value, 0),
                    "resolved_tickets": status_counts.get(TicketStatus.RESOLVED.value, 0),
                    "closed_tickets": status_counts.get(TicketStatus.CLOSED.value, 0),
                    "tickets_by_category": category_counts,
                    "tickets_by_priority": priority_counts,
                    "average_resolution_time_hours": avg_resolution_time,
                    "tickets_today": tickets_today,
                }
            except Exception as e:
                logger.error(f"Error getting ticket statistics: {e}")
                raise QueryError(
                    query="SELECT ticket statistics",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(TicketModel)
                    .where(TicketModel.priority == priority.value)
                    .options(
                        selectinload(TicketModel.user),
                        selectinload(TicketModel.assignee),
                        selectinload(TicketModel.messages),
                    )
                    .order_by(desc(TicketModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting tickets by priority {priority.value}: {e}")
                raise QueryError(
                    query="SELECT tickets WHERE priority = :priority",
                    reason=str(e),
                )

    # ----------------------------------------------
    # متدهای تغییر وضعیت سریع
    # ----------------------------------------------

    async def resolve_ticket(self, ticket_id: int, reason: Optional[str] = None) -> Optional[Ticket]:
        """
        حل کردن یک تیکت (تغییر وضعیت به RESOLVED).

        Args:
            ticket_id: شناسه تیکت.
            reason: دلیل حل (اختیاری).

        Returns:
            تیکت به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        return await self.update_status(ticket_id, TicketStatus.RESOLVED, reason)

    async def close_ticket(self, ticket_id: int, reason: Optional[str] = None) -> Optional[Ticket]:
        """
        بستن یک تیکت (تغییر وضعیت به CLOSED).

        Args:
            ticket_id: شناسه تیکت.
            reason: دلیل بستن (اختیاری).

        Returns:
            تیکت به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        return await self.update_status(ticket_id, TicketStatus.CLOSED, reason)

    async def reopen_ticket(self, ticket_id: int) -> Optional[Ticket]:
        """
        بازگشایی یک تیکت (تغییر وضعیت به OPEN).

        Args:
            ticket_id: شناسه تیکت.

        Returns:
            تیکت به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        return await self.update_status(ticket_id, TicketStatus.OPEN, "Reopened")