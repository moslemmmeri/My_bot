# my_bot_project/src/my_bot/infrastructure/repositories/payment_repo_impl.py
"""
پیاده‌سازی ریپازیتوری پرداخت (Payment Repository Implementation).

این کلاس پیاده‌سازی عینی از اینترفیس PaymentRepository است که با استفاده
از SQLAlchemy و DatabaseSessionManager، عملیات CRUD و جستجو روی
جدول payments را انجام می‌دهد.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import select, delete, update, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from my_bot.core.constants.payment_statuses import PaymentStatus
from my_bot.core.exceptions.db_errors import DatabaseError, QueryError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.payment import Payment
from my_bot.domain.interfaces.repositories.payment_repository import PaymentRepository
from my_bot.domain.value_objects.money import Money
from my_bot.infrastructure.database.models.payment_model import PaymentModel
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager

logger = get_logger(__name__)


class PaymentRepositoryImpl(PaymentRepository):
    """
    پیاده‌سازی ریپازیتوری پرداخت با استفاده از SQLAlchemy.

    این کلاس تمام متدهای اینترفیس PaymentRepository را پیاده‌سازی می‌کند
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
        logger.info("PaymentRepositoryImpl initialized.")

    async def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """
        دریافت تراکنش با شناسه داخلی.

        Args:
            payment_id: شناسه تراکنش در دیتابیس.

        Returns:
            تراکنش در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(PaymentModel).where(PaymentModel.id == payment_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting payment by id {payment_id}: {e}")
                raise QueryError(
                    query="SELECT payments WHERE id = :payment_id",
                    reason=str(e),
                )

    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """
        دریافت تراکنش با شناسه تراکنش در درگاه پرداخت.

        Args:
            transaction_id: شناسه تراکنش در درگاه.

        Returns:
            تراکنش در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(PaymentModel).where(PaymentModel.transaction_id == transaction_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting payment by transaction_id {transaction_id}: {e}")
                raise QueryError(
                    query="SELECT payments WHERE transaction_id = :transaction_id",
                    reason=str(e),
                )

    async def get_by_tracking_code(self, tracking_code: str) -> Optional[Payment]:
        """
        دریافت تراکنش با کد رهگیری پرداخت.

        Args:
            tracking_code: کد رهگیری پرداخت.

        Returns:
            تراکنش در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(PaymentModel).where(PaymentModel.tracking_code == tracking_code)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting payment by tracking_code {tracking_code}: {e}")
                raise QueryError(
                    query="SELECT payments WHERE tracking_code = :tracking_code",
                    reason=str(e),
                )

    async def get_by_order_id(self, order_id: str) -> Optional[Payment]:
        """
        دریافت تراکنش مرتبط با یک سفارش.

        Args:
            order_id: شناسه سفارش.

        Returns:
            تراکنش در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(PaymentModel).where(PaymentModel.order_id == order_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting payment by order_id {order_id}: {e}")
                raise QueryError(
                    query="SELECT payments WHERE order_id = :order_id",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = select(PaymentModel).where(PaymentModel.user_id == user_id)
                if status:
                    stmt = stmt.where(PaymentModel.status == status.value)
                stmt = (
                    stmt.order_by(desc(PaymentModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting payments for user {user_id}: {e}")
                raise QueryError(
                    query="SELECT payments WHERE user_id = :user_id",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(PaymentModel)
                    .where(PaymentModel.status == status.value)
                    .order_by(desc(PaymentModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting payments by status {status.value}: {e}")
                raise QueryError(
                    query="SELECT payments WHERE status = :status",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(PaymentModel)
                    .where(PaymentModel.gateway == gateway)
                    .order_by(desc(PaymentModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting payments by gateway {gateway}: {e}")
                raise QueryError(
                    query="SELECT payments WHERE gateway = :gateway",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                order_col = getattr(PaymentModel, order_by, PaymentModel.created_at)
                order_expr = order_col.desc() if order_desc else order_col.asc()

                stmt = (
                    select(PaymentModel)
                    .order_by(order_expr)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting all payments: {e}")
                raise QueryError(
                    query="SELECT payments WITH pagination",
                    reason=str(e),
                )

    async def save(self, payment: Payment) -> Payment:
        """
        ذخیره یا به‌روزرسانی یک تراکنش در دیتابیس.

        Args:
            payment: موجودیت پرداخت برای ذخیره‌سازی.

        Returns:
            تراکنش ذخیره‌شده با شناسه و تاریخ‌های به‌روزرسانی‌شده.
        """
        async with self._session_manager.session() as session:
            try:
                if payment.id:
                    # به‌روزرسانی
                    stmt = (
                        update(PaymentModel)
                        .where(PaymentModel.id == payment.id)
                        .values(
                            user_id=payment.user_id,
                            order_id=payment.order_id,
                            amount=float(payment.amount.amount),
                            currency=payment.amount.currency,
                            status=payment.status.value if payment.status else PaymentStatus.PENDING.value,
                            gateway=payment.gateway,
                            transaction_id=payment.transaction_id,
                            tracking_code=payment.tracking_code,
                            reference_id=payment.reference_id,
                            callback_url=payment.callback_url,
                            callback_data=payment.callback_data,
                            paid_at=payment.paid_at,
                            expired_at=payment.expired_at,
                            retry_count=payment.retry_count,
                            description=payment.description,
                            error_message=payment.error_message,
                            updated_at=datetime.now(),
                            metadata=payment.metadata,
                        )
                        .returning(PaymentModel)
                    )
                    result = await session.execute(stmt)
                    model = result.scalar_one_or_none()
                    await session.commit()
                    if model:
                        logger.debug(f"Payment updated: id={model.id}")
                        return model.to_domain()
                    raise DatabaseError(
                        message=f"Payment with id {payment.id} not found for update.",
                        context={"payment_id": payment.id},
                    )
                else:
                    # ایجاد جدید
                    model = PaymentModel.from_domain(payment)
                    session.add(model)
                    await session.commit()
                    await session.refresh(model)
                    logger.info(f"Payment created: id={model.id}, user_id={model.user_id}, amount={model.amount}")
                    return model.to_domain()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving payment: {e}")
                raise DatabaseError(
                    message=f"خطا در ذخیره‌سازی پرداخت: {str(e)}",
                    context={"payment_id": payment.id, "user_id": payment.user_id},
                )

    async def delete(self, payment_id: int) -> bool:
        """
        حذف یک تراکنش از دیتابیس.

        Args:
            payment_id: شناسه تراکنش برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود تراکنش.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = delete(PaymentModel).where(PaymentModel.id == payment_id)
                result = await session.execute(stmt)
                await session.commit()
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Payment deleted: id={payment_id}")
                else:
                    logger.debug(f"Payment not found for deletion: id={payment_id}")
                return deleted
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting payment {payment_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در حذف پرداخت: {str(e)}",
                    context={"payment_id": payment_id},
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(PaymentModel)
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        if hasattr(PaymentModel, key):
                            conditions.append(getattr(PaymentModel, key) == value)
                    if conditions:
                        stmt = stmt.where(and_(*conditions))
                result = await session.execute(stmt)
                return result.scalar_one()
            except Exception as e:
                logger.error(f"Error counting payments: {e}")
                raise QueryError(
                    query="COUNT payments WITH filters",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                values = {
                    "status": new_status.value,
                    "updated_at": datetime.now(),
                }
                if error_message:
                    values["error_message"] = error_message
                if new_status == PaymentStatus.SUCCESS:
                    values["paid_at"] = datetime.now()

                stmt = (
                    update(PaymentModel)
                    .where(PaymentModel.id == payment_id)
                    .values(**values)
                    .returning(PaymentModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.info(f"Payment {payment_id} status updated to {new_status.value}")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating status for payment {payment_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در به‌روزرسانی وضعیت پرداخت: {str(e)}",
                    context={"payment_id": payment_id, "new_status": new_status.value},
                )

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
        async with self._session_manager.session() as session:
            try:
                now = datetime.now()
                stmt = (
                    update(PaymentModel)
                    .where(PaymentModel.id == payment_id)
                    .values(
                        status=PaymentStatus.SUCCESS.value,
                        transaction_id=transaction_id,
                        reference_id=reference_id,
                        tracking_code=tracking_code,
                        paid_at=now,
                        updated_at=now,
                    )
                    .returning(PaymentModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.info(f"Payment {payment_id} marked as SUCCESS. Transaction: {transaction_id}")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error marking payment {payment_id} as success: {e}")
                raise DatabaseError(
                    message=f"خطا در علامت‌گذاری پرداخت موفق: {str(e)}",
                    context={"payment_id": payment_id, "transaction_id": transaction_id},
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    update(PaymentModel)
                    .where(PaymentModel.id == payment_id)
                    .values(
                        status=PaymentStatus.FAILED.value,
                        error_message=error_message,
                        updated_at=datetime.now(),
                    )
                    .returning(PaymentModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.warning(f"Payment {payment_id} marked as FAILED: {error_message}")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error marking payment {payment_id} as failed: {e}")
                raise DatabaseError(
                    message=f"خطا در علامت‌گذاری پرداخت ناموفق: {str(e)}",
                    context={"payment_id": payment_id, "error_message": error_message},
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(PaymentModel)
                    .where(
                        and_(
                            PaymentModel.created_at >= start_date,
                            PaymentModel.created_at <= end_date,
                        )
                    )
                    .order_by(PaymentModel.created_at)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting payments by date range: {e}")
                raise QueryError(
                    query="SELECT payments by date range",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(PaymentModel)
                    .where(PaymentModel.status == PaymentStatus.SUCCESS.value)
                    .order_by(desc(PaymentModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting successful payments: {e}")
                raise QueryError(
                    query="SELECT successful payments",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(PaymentModel)
                    .where(PaymentModel.status == PaymentStatus.FAILED.value)
                    .order_by(desc(PaymentModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting failed payments: {e}")
                raise QueryError(
                    query="SELECT failed payments",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = select(PaymentModel).where(
                    PaymentModel.status.in_([
                        PaymentStatus.PENDING.value,
                        PaymentStatus.PROCESSING.value,
                        PaymentStatus.WAITING_VERIFICATION.value,
                    ])
                )
                if older_than_minutes:
                    cutoff = datetime.now() - timedelta(minutes=older_than_minutes)
                    stmt = stmt.where(PaymentModel.created_at <= cutoff)

                stmt = stmt.order_by(PaymentModel.created_at)
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting pending payments: {e}")
                raise QueryError(
                    query="SELECT pending payments",
                    reason=str(e),
                )

    async def get_total_amount_by_user(self, user_id: int) -> Money:
        """
        دریافت مجموع مبلغ پرداختی یک کاربر (تراکنش‌های موفق).

        Args:
            user_id: شناسه کاربر.

        Returns:
            مجموع مبلغ پرداختی.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(func.sum(PaymentModel.amount))
                    .where(
                        and_(
                            PaymentModel.user_id == user_id,
                            PaymentModel.status == PaymentStatus.SUCCESS.value,
                        )
                    )
                )
                result = await session.execute(stmt)
                total = result.scalar_one() or 0
                return Money(Decimal(str(total)), "IRR")
            except Exception as e:
                logger.error(f"Error getting total amount for user {user_id}: {e}")
                raise QueryError(
                    query="SELECT total amount by user",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                conditions = [
                    PaymentModel.created_at >= start_date,
                    PaymentModel.created_at <= end_date,
                ]
                if status:
                    conditions.append(PaymentModel.status == status.value)

                stmt = select(func.sum(PaymentModel.amount)).where(and_(*conditions))
                result = await session.execute(stmt)
                total = result.scalar_one() or 0
                return Money(Decimal(str(total)), "IRR")
            except Exception as e:
                logger.error(f"Error getting total amount by date range: {e}")
                raise QueryError(
                    query="SELECT total amount by date range",
                    reason=str(e),
                )

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
            دیکشنری شامل آمار.
        """
        async with self._session_manager.session() as session:
            try:
                # شرط پایه
                conditions = []
                if start_date:
                    conditions.append(PaymentModel.created_at >= start_date)
                if end_date:
                    conditions.append(PaymentModel.created_at <= end_date)

                base_stmt = select(PaymentModel)
                if conditions:
                    base_stmt = base_stmt.where(and_(*conditions))

                # تعداد کل تراکنش‌ها
                total = await session.execute(
                    select(func.count()).select_from(base_stmt.subquery())
                )
                total_payments = total.scalar_one()

                # تراکنش‌ها به‌تفکیک وضعیت
                status_counts = {}
                for status in PaymentStatus:
                    count_stmt = base_stmt.where(PaymentModel.status == status.value)
                    count = await session.execute(
                        select(func.count()).select_from(count_stmt.subquery())
                    )
                    status_counts[status.value] = count.scalar_one()

                # مجموع درآمد (تراکنش‌های موفق)
                revenue_stmt = base_stmt.where(PaymentModel.status == PaymentStatus.SUCCESS.value)
                revenue = await session.execute(
                    select(func.sum(PaymentModel.amount)).select_from(revenue_stmt.subquery())
                )
                total_revenue = revenue.scalar_one() or 0

                # میانگین مبلغ
                avg = await session.execute(
                    select(func.avg(PaymentModel.amount)).select_from(base_stmt.subquery())
                )
                avg_amount = avg.scalar_one() or 0

                # تراکنش‌های امروز، این هفته، این ماه
                now = datetime.now()
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                week_start = today_start - timedelta(days=now.weekday())
                month_start = today_start.replace(day=1)

                today_count = await session.execute(
                    select(func.count()).select_from(PaymentModel).where(
                        PaymentModel.created_at >= today_start
                    )
                )
                payments_today = today_count.scalar_one()

                week_count = await session.execute(
                    select(func.count()).select_from(PaymentModel).where(
                        PaymentModel.created_at >= week_start
                    )
                )
                payments_this_week = week_count.scalar_one()

                month_count = await session.execute(
                    select(func.count()).select_from(PaymentModel).where(
                        PaymentModel.created_at >= month_start
                    )
                )
                payments_this_month = month_count.scalar_one()

                # تراکنش‌ها به‌تفکیک درگاه
                gateway_counts = {}
                gateways = await session.execute(
                    select(PaymentModel.gateway, func.count(PaymentModel.id))
                    .where(and_(*conditions) if conditions else True)
                    .group_by(PaymentModel.gateway)
                )
                for gateway, count in gateways.all():
                    gateway_counts[gateway] = count

                return {
                    "total_payments": total_payments,
                    "successful_payments": status_counts.get(PaymentStatus.SUCCESS.value, 0),
                    "failed_payments": status_counts.get(PaymentStatus.FAILED.value, 0),
                    "pending_payments": (
                        status_counts.get(PaymentStatus.PENDING.value, 0) +
                        status_counts.get(PaymentStatus.PROCESSING.value, 0) +
                        status_counts.get(PaymentStatus.WAITING_VERIFICATION.value, 0)
                    ),
                    "total_revenue": float(total_revenue),
                    "average_amount": float(avg_amount),
                    "payments_today": payments_today,
                    "payments_this_week": payments_this_week,
                    "payments_this_month": payments_this_month,
                    "payments_by_gateway": gateway_counts,
                }
            except Exception as e:
                logger.error(f"Error getting payment statistics: {e}")
                raise QueryError(
                    query="SELECT payment statistics",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(
                        PaymentModel.gateway,
                        func.sum(PaymentModel.amount).label("total"),
                    )
                    .where(
                        and_(
                            PaymentModel.created_at >= start_date,
                            PaymentModel.created_at <= end_date,
                            PaymentModel.status == PaymentStatus.SUCCESS.value,
                        )
                    )
                    .group_by(PaymentModel.gateway)
                )
                result = await session.execute(stmt)
                rows = result.all()
                return {
                    row.gateway: Money(Decimal(str(row.total)), "IRR")
                    for row in rows
                }
            except Exception as e:
                logger.error(f"Error getting revenue by gateway: {e}")
                raise QueryError(
                    query="SELECT revenue by gateway",
                    reason=str(e),
                )

    async def get_revenue_by_date(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: str = "day",
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
        async with self._session_manager.session() as session:
            try:
                # انتخاب ستون بر اساس group_by
                if group_by == "day":
                    date_col = func.date(PaymentModel.created_at)
                elif group_by == "week":
                    date_col = func.date_trunc("week", PaymentModel.created_at)
                elif group_by == "month":
                    date_col = func.date_trunc("month", PaymentModel.created_at)
                else:
                    raise ValueError(f"Invalid group_by: {group_by}")

                stmt = (
                    select(
                        date_col.label("date"),
                        func.sum(PaymentModel.amount).label("revenue"),
                        func.count(PaymentModel.id).label("payments_count"),
                    )
                    .where(
                        and_(
                            PaymentModel.created_at >= start_date,
                            PaymentModel.created_at <= end_date,
                            PaymentModel.status == PaymentStatus.SUCCESS.value,
                        )
                    )
                    .group_by("date")
                    .order_by("date")
                )
                result = await session.execute(stmt)
                rows = result.all()
                return [
                    {
                        "date": row.date.isoformat() if row.date else None,
                        "revenue": float(row.revenue) if row.revenue else 0,
                        "payments_count": row.payments_count or 0,
                    }
                    for row in rows
                ]
            except Exception as e:
                logger.error(f"Error getting revenue by date: {e}")
                raise QueryError(
                    query="SELECT revenue by date",
                    reason=str(e),
                )

    async def get_refunded_amount_by_user(self, user_id: int) -> Money:
        """
        دریافت مجموع مبلغ بازگشت‌وجه‌شده برای یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            مجموع مبلغ بازگشت‌وجه.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(func.sum(PaymentModel.amount))
                    .where(
                        and_(
                            PaymentModel.user_id == user_id,
                            PaymentModel.status == PaymentStatus.REFUNDED.value,
                        )
                    )
                )
                result = await session.execute(stmt)
                total = result.scalar_one() or 0
                return Money(Decimal(str(total)), "IRR")
            except Exception as e:
                logger.error(f"Error getting refunded amount for user {user_id}: {e}")
                raise QueryError(
                    query="SELECT refunded amount by user",
                    reason=str(e),
                )