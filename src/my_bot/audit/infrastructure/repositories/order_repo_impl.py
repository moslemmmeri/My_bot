# my_bot_project/src/my_bot/infrastructure/repositories/order_repo_impl.py
"""
پیاده‌سازی ریپازیتوری سفارش (Order Repository Implementation).

این کلاس پیاده‌سازی عینی از اینترفیس OrderRepository است که با استفاده
از SQLAlchemy و DatabaseSessionManager، عملیات CRUD و جستجو روی
جدول orders و order_items را انجام می‌دهد.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select, delete, update, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.core.exceptions.db_errors import DatabaseError, QueryError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.order import Order
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.value_objects.money import Money
from my_bot.infrastructure.database.models.order_model import OrderModel
from my_bot.infrastructure.database.models.order_item_model import OrderItemModel
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager

logger = get_logger(__name__)


class OrderRepositoryImpl(OrderRepository):
    """
    پیاده‌سازی ریپازیتوری سفارش با استفاده از SQLAlchemy.

    این کلاس تمام متدهای اینترفیس OrderRepository را پیاده‌سازی می‌کند
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
        logger.info("OrderRepositoryImpl initialized.")

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        """
        دریافت سفارش با شناسه داخلی.

        Args:
            order_id: شناسه سفارش در دیتابیس.

        Returns:
            سفارش در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(OrderModel)
                    .where(OrderModel.id == order_id)
                    .options(selectinload(OrderModel.items))
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting order by id {order_id}: {e}")
                raise QueryError(
                    query="SELECT orders WHERE id = :order_id",
                    reason=str(e),
                )

    async def get_by_order_number(self, order_number: str) -> Optional[Order]:
        """
        دریافت سفارش با شماره سفارش.

        Args:
            order_number: شماره سفارش.

        Returns:
            سفارش در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(OrderModel)
                    .where(OrderModel.order_number == order_number)
                    .options(selectinload(OrderModel.items))
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting order by order_number {order_number}: {e}")
                raise QueryError(
                    query="SELECT orders WHERE order_number = :order_number",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(OrderModel)
                    .where(OrderModel.user_id == user_id)
                    .options(selectinload(OrderModel.items))
                    .order_by(desc(OrderModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                if status:
                    stmt = stmt.where(OrderModel.status == status.value)
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting orders for user {user_id}: {e}")
                raise QueryError(
                    query="SELECT orders WHERE user_id = :user_id",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(OrderModel)
                    .where(OrderModel.status == status.value)
                    .options(selectinload(OrderModel.items))
                    .order_by(desc(OrderModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting orders by status {status.value}: {e}")
                raise QueryError(
                    query="SELECT orders WHERE status = :status",
                    reason=str(e),
                )

    async def get_by_payment_id(self, payment_id: str) -> Optional[Order]:
        """
        دریافت سفارش با شناسه پرداخت.

        Args:
            payment_id: شناسه تراکنش پرداخت.

        Returns:
            سفارش در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(OrderModel)
                    .where(OrderModel.payment_id == payment_id)
                    .options(selectinload(OrderModel.items))
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting order by payment_id {payment_id}: {e}")
                raise QueryError(
                    query="SELECT orders WHERE payment_id = :payment_id",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                order_col = getattr(OrderModel, order_by, OrderModel.created_at)
                order_expr = order_col.desc() if order_desc else order_col.asc()

                stmt = (
                    select(OrderModel)
                    .options(selectinload(OrderModel.items))
                    .order_by(order_expr)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting all orders: {e}")
                raise QueryError(
                    query="SELECT orders WITH pagination",
                    reason=str(e),
                )

    async def save(self, order: Order) -> Order:
        """
        ذخیره یا به‌روزرسانی یک سفارش در دیتابیس.

        Args:
            order: موجودیت سفارش برای ذخیره‌سازی.

        Returns:
            سفارش ذخیره‌شده با شناسه و تاریخ‌های به‌روزرسانی‌شده.
        """
        async with self._session_manager.session() as session:
            try:
                if order.id:
                    # به‌روزرسانی
                    # ابتدا آیتم‌های موجود را حذف می‌کنیم
                    await session.execute(
                        delete(OrderItemModel).where(OrderItemModel.order_id == order.id)
                    )

                    # به‌روزرسانی سفارش
                    stmt = (
                        update(OrderModel)
                        .where(OrderModel.id == order.id)
                        .values(
                            user_id=order.user_id,
                            order_number=order.order_number,
                            subtotal=float(order.subtotal.amount),
                            discount_amount=float(order.discount_amount.amount) if order.discount_amount else 0.0,
                            total_amount=float(order.total_amount.amount),
                            currency=order.total_amount.currency,
                            coupon_code=order.coupon_code,
                            status=order.status.value if order.status else OrderStatus.PENDING.value,
                            payment_id=order.payment_id,
                            shipping_address=order.shipping_address,
                            tracking_code=order.tracking_code,
                            notes=order.notes,
                            updated_at=datetime.now(),
                            metadata=order.metadata,
                        )
                        .returning(OrderModel)
                    )
                    result = await session.execute(stmt)
                    model = result.scalar_one_or_none()

                    if not model:
                        raise DatabaseError(
                            message=f"Order with id {order.id} not found for update.",
                            context={"order_id": order.id},
                        )

                    # افزودن آیتم‌های جدید
                    for item in order.items:
                        item_model = OrderItemModel.from_domain(item)
                        item_model.order_id = model.id
                        session.add(item_model)

                    await session.commit()
                    await session.refresh(model)

                    # بارگذاری آیتم‌ها
                    stmt = (
                        select(OrderModel)
                        .where(OrderModel.id == model.id)
                        .options(selectinload(OrderModel.items))
                    )
                    result = await session.execute(stmt)
                    model = result.scalar_one()

                    logger.debug(f"Order updated: id={model.id}")
                    return model.to_domain()
                else:
                    # ایجاد جدید
                    model = OrderModel.from_domain(order)
                    session.add(model)
                    await session.commit()
                    await session.refresh(model)

                    # بارگذاری آیتم‌ها
                    stmt = (
                        select(OrderModel)
                        .where(OrderModel.id == model.id)
                        .options(selectinload(OrderModel.items))
                    )
                    result = await session.execute(stmt)
                    model = result.scalar_one()

                    logger.info(f"Order created: id={model.id}, order_number={model.order_number}")
                    return model.to_domain()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving order: {e}")
                raise DatabaseError(
                    message=f"خطا در ذخیره‌سازی سفارش: {str(e)}",
                    context={"order_id": order.id, "order_number": order.order_number},
                )

    async def delete(self, order_id: int) -> bool:
        """
        حذف یک سفارش از دیتابیس.

        Args:
            order_id: شناسه سفارش برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود سفارش.
        """
        async with self._session_manager.session() as session:
            try:
                # حذف آیتم‌ها (به‌صورت خودکار با CASCADE)
                stmt = delete(OrderModel).where(OrderModel.id == order_id)
                result = await session.execute(stmt)
                await session.commit()
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Order deleted: id={order_id}")
                else:
                    logger.debug(f"Order not found for deletion: id={order_id}")
                return deleted
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting order {order_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در حذف سفارش: {str(e)}",
                    context={"order_id": order_id},
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(OrderModel)
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        if hasattr(OrderModel, key):
                            conditions.append(getattr(OrderModel, key) == value)
                    if conditions:
                        stmt = stmt.where(and_(*conditions))
                result = await session.execute(stmt)
                return result.scalar_one()
            except Exception as e:
                logger.error(f"Error counting orders: {e}")
                raise QueryError(
                    query="COUNT orders WITH filters",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                metadata_update = {}
                if reason:
                    metadata_update["status_change_reason"] = reason
                    metadata_update["status_change_from"] = func.jsonb_extract_path(
                        OrderModel.metadata, "status"
                    )

                stmt = (
                    update(OrderModel)
                    .where(OrderModel.id == order_id)
                    .values(
                        status=new_status.value,
                        updated_at=datetime.now(),
                        metadata=func.jsonb_set(
                            OrderModel.metadata,
                            "{status_change_reason}",
                            f'"{reason}"' if reason else 'null',
                        ) if reason else OrderModel.metadata,
                    )
                    .returning(OrderModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.info(f"Order {order_id} status updated to {new_status.value}")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating status for order {order_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در به‌روزرسانی وضعیت سفارش: {str(e)}",
                    context={"order_id": order_id, "new_status": new_status.value},
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    update(OrderModel)
                    .where(OrderModel.id == order_id)
                    .values(
                        payment_id=payment_id,
                        updated_at=datetime.now(),
                    )
                    .returning(OrderModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.debug(f"Payment id {payment_id} added to order {order_id}")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error adding payment id to order {order_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در افزودن شناسه پرداخت به سفارش: {str(e)}",
                    context={"order_id": order_id, "payment_id": payment_id},
                )

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
        async with self._session_manager.session() as session:
            try:
                # ابتدا سفارش را دریافت می‌کنیم تا subtotal را داشته باشیم
                order = await self.get_by_id(order_id)
                if not order:
                    return None

                new_total = order.total_amount.amount - discount_amount.amount
                if new_total < 0:
                    new_total = Decimal("0")

                stmt = (
                    update(OrderModel)
                    .where(OrderModel.id == order_id)
                    .values(
                        coupon_code=coupon_code,
                        discount_amount=float(order.discount_amount.amount + discount_amount.amount),
                        total_amount=float(new_total),
                        updated_at=datetime.now(),
                    )
                    .returning(OrderModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.info(f"Coupon {coupon_code} applied to order {order_id}")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error applying coupon to order {order_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در اعمال کد تخفیف به سفارش: {str(e)}",
                    context={"order_id": order_id, "coupon_code": coupon_code},
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    update(OrderModel)
                    .where(OrderModel.id == order_id)
                    .values(
                        tracking_code=tracking_code,
                        updated_at=datetime.now(),
                    )
                    .returning(OrderModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.debug(f"Tracking code {tracking_code} added to order {order_id}")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error adding tracking code to order {order_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در افزودن کد رهگیری به سفارش: {str(e)}",
                    context={"order_id": order_id, "tracking_code": tracking_code},
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(OrderModel)
                    .where(
                        and_(
                            OrderModel.created_at >= start_date,
                            OrderModel.created_at <= end_date,
                        )
                    )
                    .options(selectinload(OrderModel.items))
                    .order_by(OrderModel.created_at)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting orders by date range: {e}")
                raise QueryError(
                    query="SELECT orders by date range",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = select(OrderModel).where(OrderModel.status == OrderStatus.PENDING.value)
                if older_than_minutes:
                    cutoff = datetime.now() - timedelta(minutes=older_than_minutes)
                    stmt = stmt.where(OrderModel.created_at <= cutoff)
                stmt = (
                    stmt.options(selectinload(OrderModel.items))
                    .order_by(OrderModel.created_at)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting pending orders: {e}")
                raise QueryError(
                    query="SELECT pending orders",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(OrderModel)
                    .where(
                        or_(
                            OrderModel.status == OrderStatus.PENDING.value,
                            OrderModel.status == OrderStatus.ON_HOLD.value,
                        )
                    )
                    .options(selectinload(OrderModel.items))
                    .order_by(OrderModel.created_at)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting orders needing action: {e}")
                raise QueryError(
                    query="SELECT orders needing action",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                # ابتدا شناسه سفارش‌های حاوی محصول را پیدا می‌کنیم
                subquery = (
                    select(OrderItemModel.order_id)
                    .where(OrderItemModel.product_id == product_id)
                    .distinct()
                )
                stmt = (
                    select(OrderModel)
                    .where(OrderModel.id.in_(subquery))
                    .options(selectinload(OrderModel.items))
                    .order_by(desc(OrderModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting orders by product {product_id}: {e}")
                raise QueryError(
                    query="SELECT orders by product",
                    reason=str(e),
                )

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
            دیکشنری شامل آمار.
        """
        async with self._session_manager.session() as session:
            try:
                # شرط پایه
                conditions = []
                if start_date:
                    conditions.append(OrderModel.created_at >= start_date)
                if end_date:
                    conditions.append(OrderModel.created_at <= end_date)

                base_stmt = select(OrderModel)
                if conditions:
                    base_stmt = base_stmt.where(and_(*conditions))

                # تعداد کل سفارشات
                total = await session.execute(
                    select(func.count()).select_from(base_stmt.subquery())
                )
                total_orders = total.scalar_one()

                # سفارشات به‌تفکیک وضعیت
                status_counts = {}
                for status in OrderStatus:
                    count_stmt = base_stmt.where(OrderModel.status == status.value)
                    count = await session.execute(
                        select(func.count()).select_from(count_stmt.subquery())
                    )
                    status_counts[status.value] = count.scalar_one()

                # مجموع درآمد (فقط سفارشات پرداخت‌شده)
                revenue_stmt = base_stmt.where(
                    OrderModel.status.in_([s.value for s in [
                        OrderStatus.PAID,
                        OrderStatus.PROCESSING,
                        OrderStatus.SHIPPED,
                        OrderStatus.DELIVERED,
                    ]])
                )
                revenue = await session.execute(
                    select(func.sum(OrderModel.total_amount)).select_from(revenue_stmt.subquery())
                )
                total_revenue = revenue.scalar_one() or 0

                # میانگین مبلغ سفارش
                avg = await session.execute(
                    select(func.avg(OrderModel.total_amount)).select_from(base_stmt.subquery())
                )
                avg_order_value = avg.scalar_one() or 0

                # سفارشات امروز، این هفته، این ماه
                now = datetime.now()
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                week_start = today_start - timedelta(days=now.weekday())
                month_start = today_start.replace(day=1)

                today_count = await session.execute(
                    select(func.count()).select_from(OrderModel).where(
                        OrderModel.created_at >= today_start
                    )
                )
                orders_today = today_count.scalar_one()

                week_count = await session.execute(
                    select(func.count()).select_from(OrderModel).where(
                        OrderModel.created_at >= week_start
                    )
                )
                orders_this_week = week_count.scalar_one()

                month_count = await session.execute(
                    select(func.count()).select_from(OrderModel).where(
                        OrderModel.created_at >= month_start
                    )
                )
                orders_this_month = month_count.scalar_one()

                return {
                    "total_orders": total_orders,
                    "orders_by_status": status_counts,
                    "total_revenue": float(total_revenue),
                    "average_order_value": float(avg_order_value),
                    "orders_today": orders_today,
                    "orders_this_week": orders_this_week,
                    "orders_this_month": orders_this_month,
                }
            except Exception as e:
                logger.error(f"Error getting order statistics: {e}")
                raise QueryError(
                    query="SELECT order statistics",
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
                    date_col = func.date(OrderModel.created_at)
                elif group_by == "week":
                    date_col = func.date_trunc("week", OrderModel.created_at)
                elif group_by == "month":
                    date_col = func.date_trunc("month", OrderModel.created_at)
                else:
                    raise ValueError(f"Invalid group_by: {group_by}")

                stmt = (
                    select(
                        date_col.label("date"),
                        func.sum(OrderModel.total_amount).label("revenue"),
                        func.count(OrderModel.id).label("orders_count"),
                    )
                    .where(
                        and_(
                            OrderModel.created_at >= start_date,
                            OrderModel.created_at <= end_date,
                            OrderModel.status.in_([
                                OrderStatus.PAID.value,
                                OrderStatus.PROCESSING.value,
                                OrderStatus.SHIPPED.value,
                                OrderStatus.DELIVERED.value,
                            ])
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
                        "orders_count": row.orders_count or 0,
                    }
                    for row in rows
                ]
            except Exception as e:
                logger.error(f"Error getting revenue by date: {e}")
                raise QueryError(
                    query="SELECT revenue by date",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                # شرط پایه
                conditions = []
                if start_date:
                    conditions.append(OrderModel.created_at >= start_date)
                if end_date:
                    conditions.append(OrderModel.created_at <= end_date)

                # فقط سفارشات پرداخت‌شده
                conditions.append(
                    OrderModel.status.in_([
                        OrderStatus.PAID.value,
                        OrderStatus.PROCESSING.value,
                        OrderStatus.SHIPPED.value,
                        OrderStatus.DELIVERED.value,
                    ])
                )

                # ساب‌کوئری برای دریافت آیتم‌های سفارشات معتبر
                order_subquery = select(OrderModel.id).where(and_(*conditions)).subquery()

                stmt = (
                    select(
                        OrderItemModel.product_id,
                        OrderItemModel.product_name,
                        func.sum(OrderItemModel.quantity).label("total_quantity"),
                        func.sum(OrderItemModel.total_price).label("total_revenue"),
                        func.count(OrderItemModel.order_id).label("order_count"),
                    )
                    .where(OrderItemModel.order_id.in_(select(order_subquery.c.id)))
                    .group_by(OrderItemModel.product_id, OrderItemModel.product_name)
                    .order_by(desc("total_revenue"))
                    .limit(limit)
                )
                result = await session.execute(stmt)
                rows = result.all()
                return [
                    {
                        "product_id": row.product_id,
                        "product_name": row.product_name,
                        "total_quantity": row.total_quantity or 0,
                        "total_revenue": float(row.total_revenue) if row.total_revenue else 0,
                        "order_count": row.order_count or 0,
                    }
                    for row in rows
                ]
            except Exception as e:
                logger.error(f"Error getting top products: {e}")
                raise QueryError(
                    query="SELECT top products",
                    reason=str(e),
                )

    async def get_total_spent_by_user(self, user_id: int) -> Money:
        """
        دریافت مجموع مبلغ پرداختی یک کاربر (سفارشات موفق).

        Args:
            user_id: شناسه کاربر.

        Returns:
            مجموع مبلغ پرداختی.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(func.sum(OrderModel.total_amount))
                    .where(
                        and_(
                            OrderModel.user_id == user_id,
                            OrderModel.status.in_([
                                OrderStatus.PAID.value,
                                OrderStatus.PROCESSING.value,
                                OrderStatus.SHIPPED.value,
                                OrderStatus.DELIVERED.value,
                            ])
                        )
                    )
                )
                result = await session.execute(stmt)
                total = result.scalar_one() or 0
                return Money(Decimal(str(total)), "IRR")
            except Exception as e:
                logger.error(f"Error getting total spent by user {user_id}: {e}")
                raise QueryError(
                    query="SELECT total spent by user",
                    reason=str(e),
                )

    async def get_order_count_by_user(self, user_id: int) -> int:
        """
        دریافت تعداد سفارشات یک کاربر (همه وضعیت‌ها).

        Args:
            user_id: شناسه کاربر.

        Returns:
            تعداد سفارشات کاربر.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(OrderModel).where(
                    OrderModel.user_id == user_id
                )
                result = await session.execute(stmt)
                return result.scalar_one()
            except Exception as e:
                logger.error(f"Error getting order count for user {user_id}: {e}")
                raise QueryError(
                    query="SELECT order count by user",
                    reason=str(e),
                )

    async def get_last_order_by_user(self, user_id: int) -> Optional[Order]:
        """
        دریافت آخرین سفارش یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            آخرین سفارش کاربر یا None در صورت عدم وجود.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(OrderModel)
                    .where(OrderModel.user_id == user_id)
                    .options(selectinload(OrderModel.items))
                    .order_by(desc(OrderModel.created_at))
                    .limit(1)
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting last order for user {user_id}: {e}")
                raise QueryError(
                    query="SELECT last order by user",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(OrderModel)
                    .where(
                        and_(
                            OrderModel.status == OrderStatus.CANCELED.value,
                            OrderModel.created_at >= start_date,
                            OrderModel.created_at <= end_date,
                        )
                    )
                    .options(selectinload(OrderModel.items))
                    .order_by(desc(OrderModel.created_at))
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting canceled orders by date: {e}")
                raise QueryError(
                    query="SELECT canceled orders by date",
                    reason=str(e),
                )

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
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(OrderModel)
                    .where(
                        and_(
                            OrderModel.status == OrderStatus.REFUNDED.value,
                            OrderModel.created_at >= start_date,
                            OrderModel.created_at <= end_date,
                        )
                    )
                    .options(selectinload(OrderModel.items))
                    .order_by(desc(OrderModel.created_at))
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting refunded orders by date: {e}")
                raise QueryError(
                    query="SELECT refunded orders by date",
                    reason=str(e),
                )