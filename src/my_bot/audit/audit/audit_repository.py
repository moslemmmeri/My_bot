# my_bot_project/src/my_bot/audit/audit_repository.py
"""
پیاده‌سازی ریپازیتوری لاگ حسابرسی (Audit Repository Implementation).

این کلاس پیاده‌سازی عینی از اینترفیس AuditRepository است که با استفاده
از SQLAlchemy و DatabaseSessionManager، عملیات CRUD و جستجو روی
جدول audit_logs را انجام می‌دهد.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, delete, update, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from my_bot.core.exceptions.db_errors import DatabaseError, QueryError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.audit_log import AuditLog, AuditAction, AuditStatus
from my_bot.domain.interfaces.repositories.audit_repository import AuditRepository
from my_bot.infrastructure.database.models.audit_log_model import AuditLogModel
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager

logger = get_logger(__name__)


class AuditRepositoryImpl(AuditRepository):
    """
    پیاده‌سازی ریپازیتوری لاگ حسابرسی با استفاده از SQLAlchemy.

    این کلاس تمام متدهای اینترفیس AuditRepository را پیاده‌سازی می‌کند
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
        logger.info("AuditRepositoryImpl initialized.")

    async def get_by_id(self, log_id: int) -> Optional[AuditLog]:
        """
        دریافت لاگ حسابرسی با شناسه داخلی.

        Args:
            log_id: شناسه لاگ در دیتابیس.

        Returns:
            لاگ در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(AuditLogModel).where(AuditLogModel.id == log_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting audit log by id {log_id}: {e}")
                raise QueryError(
                    query="SELECT audit_logs WHERE id = :log_id",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = select(AuditLogModel).where(AuditLogModel.user_id == user_id)
                if action:
                    stmt = stmt.where(AuditLogModel.action == action.value)
                stmt = (
                    stmt.order_by(desc(AuditLogModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting audit logs for user {user_id}: {e}")
                raise QueryError(
                    query="SELECT audit_logs WHERE user_id = :user_id",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = select(AuditLogModel).where(AuditLogModel.action == action.value)
                if status:
                    stmt = stmt.where(AuditLogModel.status == status.value)
                stmt = (
                    stmt.order_by(desc(AuditLogModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting audit logs by action {action.value}: {e}")
                raise QueryError(
                    query="SELECT audit_logs WHERE action = :action",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(AuditLogModel)
                    .where(
                        and_(
                            AuditLogModel.entity_type == entity_type,
                            AuditLogModel.entity_id == entity_id,
                        )
                    )
                    .order_by(desc(AuditLogModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting audit logs for entity {entity_type}:{entity_id}: {e}")
                raise QueryError(
                    query="SELECT audit_logs WHERE entity_type = :entity_type AND entity_id = :entity_id",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(AuditLogModel)
                    .where(
                        and_(
                            AuditLogModel.created_at >= start_date,
                            AuditLogModel.created_at <= end_date,
                        )
                    )
                    .order_by(desc(AuditLogModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting audit logs by date range: {e}")
                raise QueryError(
                    query="SELECT audit_logs by date range",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                order_col = getattr(AuditLogModel, order_by, AuditLogModel.created_at)
                order_expr = order_col.desc() if order_desc else order_col.asc()

                stmt = (
                    select(AuditLogModel)
                    .order_by(order_expr)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting all audit logs: {e}")
                raise QueryError(
                    query="SELECT audit_logs WITH pagination",
                    reason=str(e),
                )

    async def save(self, log: AuditLog) -> AuditLog:
        """
        ذخیره یک لاگ حسابرسی در دیتابیس.

        Args:
            log: موجودیت لاگ برای ذخیره‌سازی.

        Returns:
            لاگ ذخیره‌شده با شناسه و تاریخ ایجاد.

        Raises:
            DatabaseError: در صورت بروز خطا در ذخیره‌سازی.
        """
        async with self._session_manager.session() as session:
            try:
                if log.id:
                    # به‌روزرسانی (معمولاً لاگ‌ها به‌روزرسانی نمی‌شوند، اما برای کامل بودن)
                    stmt = (
                        update(AuditLogModel)
                        .where(AuditLogModel.id == log.id)
                        .values(
                            user_id=log.user_id,
                            username=log.username,
                            action=log.action.value,
                            entity_type=log.entity_type,
                            entity_id=log.entity_id,
                            status=log.status.value,
                            message=log.message,
                            changes=log.changes,
                            ip_address=log.ip_address,
                            user_agent=log.user_agent,
                            session_id=log.session_id,
                            request_id=log.request_id,
                            duration_ms=log.duration_ms,
                            metadata=log.metadata,
                        )
                        .returning(AuditLogModel)
                    )
                    result = await session.execute(stmt)
                    await session.commit()
                    model = result.scalar_one_or_none()
                    if model:
                        logger.debug(f"Audit log updated: id={model.id}")
                        return model.to_domain()
                    raise DatabaseError(
                        message=f"Audit log with id {log.id} not found for update.",
                        context={"log_id": log.id},
                    )
                else:
                    # ایجاد جدید
                    model = AuditLogModel.from_domain(log)
                    session.add(model)
                    await session.commit()
                    await session.refresh(model)
                    logger.debug(f"Audit log created: id={model.id}, action={model.action}")
                    return model.to_domain()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving audit log: {e}")
                raise DatabaseError(
                    message=f"خطا در ذخیره‌سازی لاگ حسابرسی: {str(e)}",
                    context={"action": log.action.value, "entity_type": log.entity_type},
                )

    async def delete_old_logs(self, older_than_days: int) -> int:
        """
        حذف لاگ‌های قدیمی‌تر از تعداد روز مشخص.

        Args:
            older_than_days: تعداد روزهای نگهداری لاگ.

        Returns:
            تعداد لاگ‌های حذف‌شده.

        Raises:
            DatabaseError: در صورت بروز خطا در حذف.
        """
        async with self._session_manager.session() as session:
            try:
                cutoff = datetime.now() - timedelta(days=older_than_days)
                stmt = delete(AuditLogModel).where(AuditLogModel.created_at < cutoff)
                result = await session.execute(stmt)
                await session.commit()
                deleted = result.rowcount
                if deleted:
                    logger.info(f"Deleted {deleted} audit logs older than {older_than_days} days")
                return deleted
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting old audit logs: {e}")
                raise DatabaseError(
                    message=f"خطا در حذف لاگ‌های قدیمی: {str(e)}",
                    context={"older_than_days": older_than_days},
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(AuditLogModel)
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        if hasattr(AuditLogModel, key):
                            conditions.append(getattr(AuditLogModel, key) == value)
                    if conditions:
                        stmt = stmt.where(and_(*conditions))
                result = await session.execute(stmt)
                return result.scalar_one()
            except Exception as e:
                logger.error(f"Error counting audit logs: {e}")
                raise QueryError(
                    query="COUNT audit_logs WITH filters",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                search_term = f"%{query}%"
                stmt = (
                    select(AuditLogModel)
                    .where(
                        or_(
                            AuditLogModel.message.ilike(search_term),
                            AuditLogModel.username.ilike(search_term),
                            AuditLogModel.entity_type.ilike(search_term),
                            AuditLogModel.entity_id.ilike(search_term),
                        )
                    )
                    .order_by(desc(AuditLogModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error searching audit logs with query '{query}': {e}")
                raise QueryError(
                    query="SEARCH audit_logs",
                    reason=str(e),
                )

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
            دیکشنری شامل آمار.
        """
        async with self._session_manager.session() as session:
            try:
                # شرط پایه
                conditions = []
                if start_date:
                    conditions.append(AuditLogModel.created_at >= start_date)
                if end_date:
                    conditions.append(AuditLogModel.created_at <= end_date)

                base_stmt = select(AuditLogModel)
                if conditions:
                    base_stmt = base_stmt.where(and_(*conditions))

                # تعداد کل لاگ‌ها
                total = await session.execute(
                    select(func.count()).select_from(base_stmt.subquery())
                )
                total_logs = total.scalar_one()

                # لاگ‌ها به‌تفکیک نوع عملیات
                action_counts = {}
                for action in AuditAction:
                    count_stmt = base_stmt.where(AuditLogModel.action == action.value)
                    count = await session.execute(
                        select(func.count()).select_from(count_stmt.subquery())
                    )
                    action_counts[action.value] = count.scalar_one()

                # لاگ‌ها به‌تفکیک وضعیت
                status_counts = {}
                for status in AuditStatus:
                    count_stmt = base_stmt.where(AuditLogModel.status == status.value)
                    count = await session.execute(
                        select(func.count()).select_from(count_stmt.subquery())
                    )
                    status_counts[status.value] = count.scalar_one()

                # لاگ‌های امروز، این هفته، این ماه
                now = datetime.now()
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                week_start = today_start - timedelta(days=now.weekday())
                month_start = today_start.replace(day=1)

                today_count = await session.execute(
                    select(func.count()).select_from(AuditLogModel).where(
                        AuditLogModel.created_at >= today_start
                    )
                )
                logs_today = today_count.scalar_one()

                week_count = await session.execute(
                    select(func.count()).select_from(AuditLogModel).where(
                        AuditLogModel.created_at >= week_start
                    )
                )
                logs_this_week = week_count.scalar_one()

                month_count = await session.execute(
                    select(func.count()).select_from(AuditLogModel).where(
                        AuditLogModel.created_at >= month_start
                    )
                )
                logs_this_month = month_count.scalar_one()

                # کاربران با بیشترین لاگ
                top_users_query = (
                    select(
                        AuditLogModel.user_id,
                        func.count(AuditLogModel.id).label("count")
                    )
                    .where(AuditLogModel.user_id.is_not(None))
                    .group_by(AuditLogModel.user_id)
                    .order_by(desc("count"))
                    .limit(5)
                )
                top_users = await session.execute(top_users_query)
                top_users_list = [
                    {"user_id": row.user_id, "count": row.count}
                    for row in top_users.all()
                ]

                # پرتکرارترین عملیات‌ها
                most_common_query = (
                    select(
                        AuditLogModel.action,
                        func.count(AuditLogModel.id).label("count")
                    )
                    .group_by(AuditLogModel.action)
                    .order_by(desc("count"))
                    .limit(5)
                )
                most_common = await session.execute(most_common_query)
                most_common_list = [
                    {"action": row.action, "count": row.count}
                    for row in most_common.all()
                ]

                return {
                    "total_logs": total_logs,
                    "logs_by_action": action_counts,
                    "logs_by_status": status_counts,
                    "logs_today": logs_today,
                    "logs_this_week": logs_this_week,
                    "logs_this_month": logs_this_month,
                    "most_active_users": top_users_list,
                    "most_common_actions": most_common_list,
                }
            except Exception as e:
                logger.error(f"Error getting audit log statistics: {e}")
                raise QueryError(
                    query="SELECT audit log statistics",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                conditions = []
                if action:
                    conditions.append(AuditLogModel.action == action.value)
                if start_date:
                    conditions.append(AuditLogModel.created_at >= start_date)
                if end_date:
                    conditions.append(AuditLogModel.created_at <= end_date)

                stmt = (
                    select(
                        AuditLogModel.user_id,
                        AuditLogModel.username,
                        AuditLogModel.entity_type,
                        AuditLogModel.entity_id,
                        func.count(AuditLogModel.id).label("count"),
                    )
                )
                if conditions:
                    stmt = stmt.where(and_(*conditions))

                stmt = (
                    stmt.group_by(
                        AuditLogModel.user_id,
                        AuditLogModel.username,
                        AuditLogModel.entity_type,
                        AuditLogModel.entity_id,
                    )
                    .order_by(desc("count"))
                    .limit(100)
                )

                result = await session.execute(stmt)
                rows = result.all()
                return [
                    {
                        "user_id": row.user_id,
                        "username": row.username,
                        "entity_type": row.entity_type,
                        "entity_id": row.entity_id,
                        "count": row.count,
                    }
                    for row in rows
                ]
            except Exception as e:
                logger.error(f"Error getting actions summary: {e}")
                raise QueryError(
                    query="SELECT actions summary",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = select(AuditLogModel)
                if action:
                    stmt = stmt.where(AuditLogModel.action == action.value)
                stmt = stmt.order_by(desc(AuditLogModel.created_at)).limit(limit)
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting latest audit logs: {e}")
                raise QueryError(
                    query="SELECT latest audit logs",
                    reason=str(e),
                )