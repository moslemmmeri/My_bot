# my_bot_project/src/my_bot/infrastructure/repositories/coupon_repo_impl.py
"""
پیاده‌سازی ریپازیتوری کوپن (Coupon Repository Implementation).

این کلاس پیاده‌سازی عینی از اینترفیس CouponRepository است که با استفاده
از SQLAlchemy و DatabaseSessionManager، عملیات CRUD و جستجو روی
جدول coupons را انجام می‌دهد.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import select, delete, update, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from my_bot.core.exceptions.db_errors import DatabaseError, QueryError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.coupon import Coupon
from my_bot.domain.interfaces.repositories.coupon_repository import CouponRepository
from my_bot.domain.value_objects.money import Money
from my_bot.infrastructure.database.models.coupon_model import CouponModel
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager

logger = get_logger(__name__)


class CouponRepositoryImpl(CouponRepository):
    """
    پیاده‌سازی ریپازیتوری کوپن با استفاده از SQLAlchemy.

    این کلاس تمام متدهای اینترفیس CouponRepository را پیاده‌سازی می‌کند
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
        logger.info("CouponRepositoryImpl initialized.")

    async def get_by_id(self, coupon_id: int) -> Optional[Coupon]:
        """
        دریافت کوپن با شناسه داخلی.

        Args:
            coupon_id: شناسه کوپن در دیتابیس.

        Returns:
            کوپن در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(CouponModel).where(CouponModel.id == coupon_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting coupon by id {coupon_id}: {e}")
                raise QueryError(
                    query="SELECT coupons WHERE id = :coupon_id",
                    reason=str(e),
                )

    async def get_by_code(self, code: str) -> Optional[Coupon]:
        """
        دریافت کوپن با کد تخفیف.

        Args:
            code: کد تخفیف.

        Returns:
            کوپن در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(CouponModel).where(CouponModel.code == code)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting coupon by code {code}: {e}")
                raise QueryError(
                    query="SELECT coupons WHERE code = :code",
                    reason=str(e),
                )

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[Coupon]:
        """
        دریافت لیست کوپن‌ها با صفحه‌بندی و فیلتر اختیاری.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            is_active: فیلتر بر اساس فعال بودن (اختیاری).
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی، False برای صعودی.

        Returns:
            لیست کوپن‌ها.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(CouponModel)
                if is_active is not None:
                    stmt = stmt.where(CouponModel.is_active == is_active)

                order_col = getattr(CouponModel, order_by, CouponModel.created_at)
                order_expr = order_col.desc() if order_desc else order_col.asc()

                stmt = stmt.order_by(order_expr).offset(skip).limit(limit)
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting all coupons: {e}")
                raise QueryError(
                    query="SELECT coupons WITH pagination",
                    reason=str(e),
                )

    async def save(self, coupon: Coupon) -> Coupon:
        """
        ذخیره یا به‌روزرسانی یک کوپن در دیتابیس.

        Args:
            coupon: موجودیت کوپن برای ذخیره‌سازی.

        Returns:
            کوپن ذخیره‌شده با شناسه و تاریخ‌های به‌روزرسانی‌شده.
        """
        async with self._session_manager.session() as session:
            try:
                if coupon.id:
                    # به‌روزرسانی
                    stmt = (
                        update(CouponModel)
                        .where(CouponModel.id == coupon.id)
                        .values(
                            code=coupon.code,
                            description=coupon.description,
                            discount_type=coupon.discount_type.value if coupon.discount_type else "fixed",
                            discount_value=coupon.discount_value,
                            currency=coupon.currency,
                            min_order_amount=float(coupon.min_order_amount.amount) if coupon.min_order_amount else None,
                            max_discount_amount=float(coupon.max_discount_amount.amount) if coupon.max_discount_amount else None,
                            usage_limit=coupon.usage_limit,
                            usage_count=coupon.usage_count,
                            user_usage_limit=coupon.user_usage_limit,
                            user_usage_count=coupon.user_usage_count,
                            valid_from=coupon.valid_from,
                            valid_until=coupon.valid_until,
                            is_active=coupon.is_active,
                            applicable_products=coupon.applicable_products,
                            applicable_users=coupon.applicable_users,
                            updated_at=datetime.now(),
                            metadata=coupon.metadata,
                        )
                        .returning(CouponModel)
                    )
                    result = await session.execute(stmt)
                    model = result.scalar_one_or_none()
                    await session.commit()
                    if model:
                        logger.debug(f"Coupon updated: id={model.id}")
                        return model.to_domain()
                    raise DatabaseError(
                        message=f"Coupon with id {coupon.id} not found for update.",
                        context={"coupon_id": coupon.id},
                    )
                else:
                    # ایجاد جدید
                    model = CouponModel.from_domain(coupon)
                    session.add(model)
                    await session.commit()
                    await session.refresh(model)
                    logger.info(f"Coupon created: id={model.id}, code={model.code}")
                    return model.to_domain()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving coupon: {e}")
                raise DatabaseError(
                    message=f"خطا در ذخیره‌سازی کوپن: {str(e)}",
                    context={"coupon_id": coupon.id, "code": coupon.code},
                )

    async def delete(self, coupon_id: int) -> bool:
        """
        حذف یک کوپن از دیتابیس.

        Args:
            coupon_id: شناسه کوپن برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود کوپن.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = delete(CouponModel).where(CouponModel.id == coupon_id)
                result = await session.execute(stmt)
                await session.commit()
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Coupon deleted: id={coupon_id}")
                else:
                    logger.debug(f"Coupon not found for deletion: id={coupon_id}")
                return deleted
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting coupon {coupon_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در حذف کوپن: {str(e)}",
                    context={"coupon_id": coupon_id},
                )

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        شمارش تعداد کوپن‌ها با اعمال فیلترهای اختیاری.

        Args:
            filters: دیکشنری فیلترها (اختیاری).

        Returns:
            تعداد کوپن‌ها.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(CouponModel)
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        if hasattr(CouponModel, key):
                            conditions.append(getattr(CouponModel, key) == value)
                    if conditions:
                        stmt = stmt.where(and_(*conditions))
                result = await session.execute(stmt)
                return result.scalar_one()
            except Exception as e:
                logger.error(f"Error counting coupons: {e}")
                raise QueryError(
                    query="COUNT coupons WITH filters",
                    reason=str(e),
                )

    async def exists_by_code(self, code: str) -> bool:
        """
        بررسی وجود کوپن با کد مشخص.

        Args:
            code: کد تخفیف.

        Returns:
            True اگر کوپن وجود داشته باشد، در غیر این صورت False.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(CouponModel).where(CouponModel.code == code)
                result = await session.execute(stmt)
                count = result.scalar_one()
                return count > 0
            except Exception as e:
                logger.error(f"Error checking existence by code {code}: {e}")
                return False

    async def get_valid_coupons(
        self,
        user_id: Optional[int] = None,
        order_amount: Optional[Money] = None,
        product_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Coupon]:
        """
        دریافت کوپن‌های معتبر برای یک کاربر، مبلغ سفارش و محصول خاص.

        Args:
            user_id: شناسه کاربر (اختیاری).
            order_amount: مبلغ سفارش (اختیاری).
            product_id: شناسه محصول (اختیاری).
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کوپن‌های معتبر.
        """
        async with self._session_manager.session() as session:
            try:
                now = datetime.now()
                conditions = [
                    CouponModel.is_active == True,
                    CouponModel.valid_from <= now,
                    or_(
                        CouponModel.valid_until.is_(None),
                        CouponModel.valid_until >= now,
                    ),
                ]

                # بررسی محدودیت استفاده کلی
                conditions.append(
                    or_(
                        CouponModel.usage_limit.is_(None),
                        CouponModel.usage_count < CouponModel.usage_limit,
                    )
                )

                # اگر کاربر مشخص شده، محدودیت‌های کاربری را اعمال می‌کنیم
                if user_id is not None:
                    # کاربر باید در لیست مجاز باشد (اگر لیست خالی باشد یعنی همه مجازند)
                    conditions.append(
                        or_(
                            CouponModel.applicable_users.is_(None),
                            CouponModel.applicable_users == [],
                            func.jsonb_array_length(CouponModel.applicable_users) == 0,
                            func.jsonb_array_contains(CouponModel.applicable_users, str(user_id)),
                        )
                    )
                    # بررسی محدودیت استفاده کاربر
                    # این شرط در کوئری SQL سخت است، پس بعداً در حافظه فیلتر می‌کنیم
                    # فعلاً فقط شرط کلی را اعمال می‌کنیم

                # اگر مبلغ سفارش مشخص شده، حداقل مبلغ را بررسی می‌کنیم
                if order_amount is not None:
                    conditions.append(
                        or_(
                            CouponModel.min_order_amount.is_(None),
                            CouponModel.min_order_amount <= float(order_amount.amount),
                        )
                    )

                # اگر محصول مشخص شده، فقط کوپن‌هایی که برای این محصول قابل اعمال هستند
                if product_id is not None:
                    conditions.append(
                        or_(
                            CouponModel.applicable_products.is_(None),
                            CouponModel.applicable_products == [],
                            func.jsonb_array_length(CouponModel.applicable_products) == 0,
                            func.jsonb_array_contains(CouponModel.applicable_products, product_id),
                        )
                    )

                stmt = (
                    select(CouponModel)
                    .where(and_(*conditions))
                    .order_by(desc(CouponModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()

                # فیلتر نهایی در حافظه برای محدودیت استفاده کاربر
                coupons = []
                for model in models:
                    coupon = model.to_domain()
                    # بررسی محدودیت استفاده کاربر
                    if user_id is not None:
                        user_used = coupon.user_usage_count.get(user_id, 0)
                        if user_used >= coupon.user_usage_limit:
                            continue
                    coupons.append(coupon)

                return coupons
            except Exception as e:
                logger.error(f"Error getting valid coupons: {e}")
                raise QueryError(
                    query="SELECT valid coupons",
                    reason=str(e),
                )

    async def get_active_coupons(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Coupon]:
        """
        دریافت کوپن‌های فعال (is_active=True و تاریخ اعتبار).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کوپن‌های فعال.
        """
        async with self._session_manager.session() as session:
            try:
                now = datetime.now()
                stmt = (
                    select(CouponModel)
                    .where(
                        and_(
                            CouponModel.is_active == True,
                            CouponModel.valid_from <= now,
                            or_(
                                CouponModel.valid_until.is_(None),
                                CouponModel.valid_until >= now,
                            )
                        )
                    )
                    .order_by(desc(CouponModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting active coupons: {e}")
                raise QueryError(
                    query="SELECT active coupons",
                    reason=str(e),
                )

    async def get_expired_coupons(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Coupon]:
        """
        دریافت کوپن‌های منقضی‌شده.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کوپن‌های منقضی‌شده.
        """
        async with self._session_manager.session() as session:
            try:
                now = datetime.now()
                stmt = (
                    select(CouponModel)
                    .where(
                        or_(
                            CouponModel.valid_until.is_not(None),
                            CouponModel.valid_until < now,
                        )
                    )
                    .order_by(desc(CouponModel.valid_until))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting expired coupons: {e}")
                raise QueryError(
                    query="SELECT expired coupons",
                    reason=str(e),
                )

    async def use_coupon(self, coupon_id: int, user_id: int) -> Optional[Coupon]:
        """
        ثبت استفاده از کوپن توسط یک کاربر (افزایش شمارش استفاده).

        Args:
            coupon_id: شناسه کوپن.
            user_id: شناسه کاربر.

        Returns:
            کوپن به‌روزرسانی‌شده یا None در صورت عدم وجود یا نامعتبر بودن.
        """
        async with self._session_manager.session() as session:
            try:
                # ابتدا کوپن را دریافت می‌کنیم
                coupon = await self.get_by_id(coupon_id)
                if not coupon:
                    return None

                # بررسی اعتبار (با استفاده از متد is_valid موجودیت)
                # برای سادگی، از متد use خود کوپن استفاده می‌کنیم
                try:
                    coupon.use(user_id)
                except Exception as e:
                    logger.warning(f"Coupon {coupon_id} cannot be used by user {user_id}: {e}")
                    return None

                # ذخیره تغییرات
                return await self.save(coupon)
            except Exception as e:
                logger.error(f"Error using coupon {coupon_id} for user {user_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در ثبت استفاده از کوپن: {str(e)}",
                    context={"coupon_id": coupon_id, "user_id": user_id},
                )

    async def reset_usage(self, coupon_id: int) -> Optional[Coupon]:
        """
        بازنشانی آمار استفاده از کوپن.

        Args:
            coupon_id: شناسه کوپن.

        Returns:
            کوپن به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        async with self._session_manager.session() as session:
            try:
                coupon = await self.get_by_id(coupon_id)
                if not coupon:
                    return None

                coupon.reset_usage()
                return await self.save(coupon)
            except Exception as e:
                logger.error(f"Error resetting usage for coupon {coupon_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در بازنشانی آمار استفاده کوپن: {str(e)}",
                    context={"coupon_id": coupon_id},
                )

    async def activate(self, coupon_id: int) -> Optional[Coupon]:
        """
        فعال‌سازی یک کوپن.

        Args:
            coupon_id: شناسه کوپن.

        Returns:
            کوپن به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        async with self._session_manager.session() as session:
            try:
                coupon = await self.get_by_id(coupon_id)
                if not coupon:
                    return None

                coupon.activate()
                return await self.save(coupon)
            except Exception as e:
                logger.error(f"Error activating coupon {coupon_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در فعال‌سازی کوپن: {str(e)}",
                    context={"coupon_id": coupon_id},
                )

    async def deactivate(self, coupon_id: int, reason: Optional[str] = None) -> Optional[Coupon]:
        """
        غیرفعال‌سازی یک کوپن.

        Args:
            coupon_id: شناسه کوپن.
            reason: دلیل غیرفعال‌سازی (اختیاری).

        Returns:
            کوپن به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        async with self._session_manager.session() as session:
            try:
                coupon = await self.get_by_id(coupon_id)
                if not coupon:
                    return None

                coupon.deactivate(reason)
                return await self.save(coupon)
            except Exception as e:
                logger.error(f"Error deactivating coupon {coupon_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در غیرفعال‌سازی کوپن: {str(e)}",
                    context={"coupon_id": coupon_id},
                )

    async def get_user_coupon_usage(self, user_id: int, coupon_id: int) -> int:
        """
        دریافت تعداد دفعات استفاده یک کاربر از یک کوپن.

        Args:
            user_id: شناسه کاربر.
            coupon_id: شناسه کوپن.

        Returns:
            تعداد دفعات استفاده.
        """
        try:
            coupon = await self.get_by_id(coupon_id)
            if not coupon:
                return 0
            return coupon.user_usage_count.get(user_id, 0)
        except Exception as e:
            logger.error(f"Error getting user coupon usage: {e}")
            return 0

    async def get_most_used_coupons(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        دریافت پراستفاده‌ترین کوپن‌ها.

        Args:
            limit: حداکثر تعداد کوپن‌ها.
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            لیست دیکشنری‌های شامل شناسه کوپن، کد، تعداد استفاده.
        """
        async with self._session_manager.session() as session:
            try:
                conditions = []
                if start_date:
                    conditions.append(CouponModel.created_at >= start_date)
                if end_date:
                    conditions.append(CouponModel.created_at <= end_date)

                stmt = select(
                    CouponModel.id,
                    CouponModel.code,
                    CouponModel.usage_count,
                )
                if conditions:
                    stmt = stmt.where(and_(*conditions))
                stmt = stmt.order_by(desc(CouponModel.usage_count)).limit(limit)

                result = await session.execute(stmt)
                rows = result.all()
                return [
                    {
                        "coupon_id": row.id,
                        "code": row.code,
                        "usage_count": row.usage_count,
                    }
                    for row in rows
                ]
            except Exception as e:
                logger.error(f"Error getting most used coupons: {e}")
                raise QueryError(
                    query="SELECT most used coupons",
                    reason=str(e),
                )

    async def get_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی کوپن‌ها.

        Returns:
            دیکشنری شامل آمار.
        """
        async with self._session_manager.session() as session:
            try:
                # تعداد کل کوپن‌ها
                total = await session.execute(
                    select(func.count()).select_from(CouponModel)
                )
                total_coupons = total.scalar_one()

                # کوپن‌های فعال
                active = await session.execute(
                    select(func.count()).select_from(CouponModel).where(
                        CouponModel.is_active == True
                    )
                )
                active_coupons = active.scalar_one()

                # کوپن‌های منقضی
                now = datetime.now()
                expired = await session.execute(
                    select(func.count()).select_from(CouponModel).where(
                        and_(
                            CouponModel.valid_until.is_not(None),
                            CouponModel.valid_until < now,
                        )
                    )
                )
                expired_coupons = expired.scalar_one()

                # تعداد کل استفاده‌ها
                total_usage = await session.execute(
                    select(func.sum(CouponModel.usage_count)).select_from(CouponModel)
                )
                total_usage_count = total_usage.scalar_one() or 0

                # کوپن‌ها به‌تفکیک نوع تخفیف
                types = {}
                for disc_type in ["percentage", "fixed"]:
                    count = await session.execute(
                        select(func.count()).select_from(CouponModel).where(
                            CouponModel.discount_type == disc_type
                        )
                    )
                    types[disc_type] = count.scalar_one()

                return {
                    "total_coupons": total_coupons,
                    "active_coupons": active_coupons,
                    "expired_coupons": expired_coupons,
                    "total_usage": total_usage_count,
                    "coupons_by_type": types,
                }
            except Exception as e:
                logger.error(f"Error getting coupon statistics: {e}")
                raise QueryError(
                    query="SELECT coupon statistics",
                    reason=str(e),
                )