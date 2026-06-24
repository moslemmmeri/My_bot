# my_bot_project/src/my_bot/infrastructure/repositories/user_repo_impl.py
"""
پیاده‌سازی ریپازیتوری کاربر (User Repository Implementation).

این کلاس پیاده‌سازی عینی از اینترفیس UserRepository است که با استفاده
از SQLAlchemy و DatabaseSessionManager، عملیات CRUD و جستجو روی
جدول users را انجام می‌دهد.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy import select, delete, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from my_bot.core.constants.user_roles import UserRole
from my_bot.core.exceptions.db_errors import DatabaseError, QueryError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.user import User
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.value_objects.user_level import UserLevel
from my_bot.infrastructure.database.models.user_model import UserModel
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager

logger = get_logger(__name__)


class UserRepositoryImpl(UserRepository):
    """
    پیاده‌سازی ریپازیتوری کاربر با استفاده از SQLAlchemy.

    این کلاس تمام متدهای اینترفیس UserRepository را پیاده‌سازی می‌کند
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
        logger.info("UserRepositoryImpl initialized.")

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        دریافت کاربر با شناسه داخلی.

        Args:
            user_id: شناسه کاربر در دیتابیس.

        Returns:
            کاربر در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(UserModel).where(UserModel.id == user_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting user by id {user_id}: {e}")
                raise QueryError(
                    query="SELECT users WHERE id = :user_id",
                    reason=str(e),
                )

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        دریافت کاربر با شناسه تلگرام.

        Args:
            telegram_id: شناسه تلگرام کاربر.

        Returns:
            کاربر در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(UserModel).where(UserModel.telegram_id == telegram_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting user by telegram_id {telegram_id}: {e}")
                raise QueryError(
                    query="SELECT users WHERE telegram_id = :telegram_id",
                    reason=str(e),
                )

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        دریافت کاربر با نام کاربری تلگرام.

        Args:
            username: نام کاربری.

        Returns:
            کاربر در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(UserModel).where(UserModel.username == username)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting user by username {username}: {e}")
                raise QueryError(
                    query="SELECT users WHERE username = :username",
                    reason=str(e),
                )

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        دریافت کاربر با آدرس ایمیل.

        Args:
            email: آدرس ایمیل.

        Returns:
            کاربر در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(UserModel).where(UserModel.email == email)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting user by email {email}: {e}")
                raise QueryError(
                    query="SELECT users WHERE email = :email",
                    reason=str(e),
                )

    async def get_by_phone(self, phone: str) -> Optional[User]:
        """
        دریافت کاربر با شماره تلفن.

        Args:
            phone: شماره تلفن.

        Returns:
            کاربر در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(UserModel).where(UserModel.phone_number == phone)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting user by phone {phone}: {e}")
                raise QueryError(
                    query="SELECT users WHERE phone_number = :phone",
                    reason=str(e),
                )

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "id",
        order_desc: bool = False,
    ) -> List[User]:
        """
        دریافت لیست کاربران با صفحه‌بندی.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی.

        Returns:
            لیست کاربران.
        """
        async with self._session_manager.session() as session:
            try:
                # ساخت عبارت ORDER BY
                order_col = getattr(UserModel, order_by, UserModel.id)
                order_expr = order_col.desc() if order_desc else order_col.asc()

                stmt = (
                    select(UserModel)
                    .order_by(order_expr)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting all users: {e}")
                raise QueryError(
                    query="SELECT users WITH pagination",
                    reason=str(e),
                )

    async def save(self, user: User) -> User:
        """
        ذخیره یا به‌روزرسانی یک کاربر در دیتابیس.

        Args:
            user: موجودیت کاربر برای ذخیره‌سازی.

        Returns:
            کاربر ذخیره‌شده با شناسه و تاریخ‌های به‌روزرسانی‌شده.
        """
        async with self._session_manager.session() as session:
            try:
                if user.id:
                    # به‌روزرسانی
                    stmt = (
                        update(UserModel)
                        .where(UserModel.id == user.id)
                        .values(
                            username=user.username,
                            first_name=user.first_name,
                            last_name=user.last_name,
                            phone_number=user.phone_number,
                            email=user.email,
                            role=user.role.value if user.role else UserRole.USER.value,
                            level=user.level.value if user.level else UserLevel.BRONZE.value,
                            points=user.points,
                            is_active=user.is_active,
                            is_banned=user.is_banned,
                            last_activity=user.last_activity,
                            updated_at=datetime.now(),
                            metadata=user.metadata,
                        )
                        .returning(UserModel)
                    )
                    result = await session.execute(stmt)
                    model = result.scalar_one_or_none()
                    await session.commit()
                    if model:
                        logger.debug(f"User updated: id={model.id}")
                        return model.to_domain()
                    raise DatabaseError(
                        message=f"User with id {user.id} not found for update.",
                        context={"user_id": user.id},
                    )
                else:
                    # ایجاد جدید
                    model = UserModel.from_domain(user)
                    session.add(model)
                    await session.commit()
                    await session.refresh(model)
                    logger.info(f"User created: id={model.id}, telegram_id={model.telegram_id}")
                    return model.to_domain()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving user: {e}")
                raise DatabaseError(
                    message=f"خطا در ذخیره‌سازی کاربر: {str(e)}",
                    context={"user_id": user.id, "telegram_id": user.telegram_id},
                )

    async def delete(self, user_id: int) -> bool:
        """
        حذف یک کاربر از دیتابیس.

        Args:
            user_id: شناسه کاربر برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود کاربر.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = delete(UserModel).where(UserModel.id == user_id)
                result = await session.execute(stmt)
                await session.commit()
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"User deleted: id={user_id}")
                else:
                    logger.debug(f"User not found for deletion: id={user_id}")
                return deleted
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting user {user_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در حذف کاربر: {str(e)}",
                    context={"user_id": user_id},
                )

    async def exists_by_telegram_id(self, telegram_id: int) -> bool:
        """
        بررسی وجود کاربر با شناسه تلگرام.

        Args:
            telegram_id: شناسه تلگرام.

        Returns:
            True اگر کاربر وجود داشته باشد، در غیر این صورت False.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(UserModel).where(
                    UserModel.telegram_id == telegram_id
                )
                result = await session.execute(stmt)
                count = result.scalar_one()
                return count > 0
            except Exception as e:
                logger.error(f"Error checking existence by telegram_id {telegram_id}: {e}")
                return False

    async def exists_by_email(self, email: str) -> bool:
        """
        بررسی وجود کاربر با آدرس ایمیل.

        Args:
            email: آدرس ایمیل.

        Returns:
            True اگر کاربر وجود داشته باشد، در غیر این صورت False.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(UserModel).where(
                    UserModel.email == email
                )
                result = await session.execute(stmt)
                count = result.scalar_one()
                return count > 0
            except Exception as e:
                logger.error(f"Error checking existence by email {email}: {e}")
                return False

    async def exists_by_phone(self, phone: str) -> bool:
        """
        بررسی وجود کاربر با شماره تلفن.

        Args:
            phone: شماره تلفن.

        Returns:
            True اگر کاربر وجود داشته باشد، در غیر این صورت False.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(UserModel).where(
                    UserModel.phone_number == phone
                )
                result = await session.execute(stmt)
                count = result.scalar_one()
                return count > 0
            except Exception as e:
                logger.error(f"Error checking existence by phone {phone}: {e}")
                return False

    async def exists_by_username(self, username: str) -> bool:
        """
        بررسی وجود کاربر با نام کاربری.

        Args:
            username: نام کاربری.

        Returns:
            True اگر کاربر وجود داشته باشد، در غیر این صورت False.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(UserModel).where(
                    UserModel.username == username
                )
                result = await session.execute(stmt)
                count = result.scalar_one()
                return count > 0
            except Exception as e:
                logger.error(f"Error checking existence by username {username}: {e}")
                return False

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        شمارش تعداد کاربران با اعمال فیلترهای اختیاری.

        Args:
            filters: دیکشنری فیلترها (اختیاری).

        Returns:
            تعداد کاربران.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(UserModel)
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        if hasattr(UserModel, key):
                            conditions.append(getattr(UserModel, key) == value)
                    if conditions:
                        stmt = stmt.where(and_(*conditions))
                result = await session.execute(stmt)
                return result.scalar_one()
            except Exception as e:
                logger.error(f"Error counting users: {e}")
                raise QueryError(
                    query="COUNT users WITH filters",
                    reason=str(e),
                )

    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[User]:
        """
        جستجوی کاربران با استفاده از متن.

        Args:
            query: عبارت جستجو.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کاربران مطابق با عبارت جستجو.
        """
        async with self._session_manager.session() as session:
            try:
                search_term = f"%{query}%"
                stmt = (
                    select(UserModel)
                    .where(
                        or_(
                            UserModel.username.ilike(search_term),
                            UserModel.first_name.ilike(search_term),
                            UserModel.last_name.ilike(search_term),
                            UserModel.email.ilike(search_term),
                            UserModel.phone_number.ilike(search_term),
                        )
                    )
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error searching users with query '{query}': {e}")
                raise QueryError(
                    query="SEARCH users",
                    reason=str(e),
                )

    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """
        دریافت کاربران فعال.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کاربران فعال.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(UserModel)
                    .where(
                        and_(
                            UserModel.is_active == True,
                            UserModel.is_banned == False,
                        )
                    )
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting active users: {e}")
                raise QueryError(
                    query="SELECT active users",
                    reason=str(e),
                )

    async def get_by_role(
        self,
        role: UserRole,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """
        دریافت کاربران با نقش مشخص.

        Args:
            role: نقش کاربری.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کاربران با نقش مشخص.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(UserModel)
                    .where(UserModel.role == role.value)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting users by role {role.value}: {e}")
                raise QueryError(
                    query="SELECT users WHERE role = :role",
                    reason=str(e),
                )

    async def get_by_level(
        self,
        level: UserLevel,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """
        دریافت کاربران با سطح مشخص.

        Args:
            level: سطح کاربری.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کاربران با سطح مشخص.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(UserModel)
                    .where(UserModel.level == level.value)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting users by level {level.value}: {e}")
                raise QueryError(
                    query="SELECT users WHERE level = :level",
                    reason=str(e),
                )

    async def get_top_by_points(
        self,
        limit: int = 10,
        min_points: Optional[int] = None,
    ) -> List[User]:
        """
        دریافت کاربران با بیشترین امتیاز.

        Args:
            limit: حداکثر تعداد کاربران.
            min_points: حداقل امتیاز (اختیاری).

        Returns:
            لیست کاربران برتر بر اساس امتیاز (نزولی).
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(UserModel).order_by(UserModel.points.desc()).limit(limit)
                if min_points is not None:
                    stmt = stmt.where(UserModel.points >= min_points)
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting top users by points: {e}")
                raise QueryError(
                    query="SELECT top users by points",
                    reason=str(e),
                )

    async def update_points(self, user_id: int, points_change: int) -> Optional[User]:
        """
        افزایش یا کاهش امتیاز کاربر.

        Args:
            user_id: شناسه کاربر.
            points_change: مقدار تغییر امتیاز.

        Returns:
            کاربر به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(
                        points=UserModel.points + points_change,
                        updated_at=datetime.now(),
                    )
                    .returning(UserModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.debug(f"User {user_id} points updated by {points_change}")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating points for user {user_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در به‌روزرسانی امتیاز کاربر: {str(e)}",
                    context={"user_id": user_id, "points_change": points_change},
                )

    async def update_last_activity(self, user_id: int) -> Optional[User]:
        """
        به‌روزرسانی زمان آخرین فعالیت کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            کاربر به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        async with self._session_manager.session() as session:
            try:
                now = datetime.now()
                stmt = (
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(
                        last_activity=now,
                        updated_at=now,
                    )
                    .returning(UserModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.debug(f"User {user_id} last_activity updated")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating last_activity for user {user_id}: {e}")
                return None

    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Tuple[User, bool]:
        """
        دریافت کاربر موجود یا ایجاد کاربر جدید.

        Args:
            telegram_id: شناسه تلگرام.
            username: نام کاربری (اختیاری).
            first_name: نام کوچک (اختیاری).
            last_name: نام خانوادگی (اختیاری).

        Returns:
            Tuple شامل کاربر و boolean (True اگر کاربر جدید ایجاد شده باشد).
        """
        # ابتدا بررسی وجود کاربر
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user, False

        # ایجاد کاربر جدید
        from my_bot.domain.entities.user import User
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        saved_user = await self.save(new_user)
        return saved_user, True

    async def get_users_created_between(
        self,
        start_date: str,
        end_date: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """
        دریافت کاربرانی که در بازه زمانی مشخص ایجاد شده‌اند.

        Args:
            start_date: تاریخ شروع (فرمت ISO).
            end_date: تاریخ پایان (فرمت ISO).
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کاربران ایجادشده در بازه زمانی.
        """
        async with self._session_manager.session() as session:
            try:
                start = datetime.fromisoformat(start_date)
                end = datetime.fromisoformat(end_date)
                stmt = (
                    select(UserModel)
                    .where(
                        and_(
                            UserModel.created_at >= start,
                            UserModel.created_at <= end,
                        )
                    )
                    .offset(skip)
                    .limit(limit)
                    .order_by(UserModel.created_at)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting users created between {start_date} and {end_date}: {e}")
                raise QueryError(
                    query="SELECT users by created_at range",
                    reason=str(e),
                )

    async def get_users_without_activity(
        self,
        days: int = 30,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """
        دریافت کاربرانی که در تعداد روز مشخص فعالیت نداشته‌اند.

        Args:
            days: تعداد روزهای عدم فعالیت.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کاربران غیرفعال.
        """
        async with self._session_manager.session() as session:
            try:
                cutoff = datetime.now() - timedelta(days=days)
                stmt = (
                    select(UserModel)
                    .where(
                        or_(
                            UserModel.last_activity.is_(None),
                            UserModel.last_activity < cutoff,
                        )
                    )
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting users without activity for {days} days: {e}")
                raise QueryError(
                    query="SELECT inactive users",
                    reason=str(e),
                )

    async def ban_user(self, user_id: int, reason: Optional[str] = None) -> Optional[User]:
        """
        مسدود کردن یک کاربر.

        Args:
            user_id: شناسه کاربر.
            reason: دلیل مسدودسازی (اختیاری).

        Returns:
            کاربر به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        async with self._session_manager.session() as session:
            try:
                now = datetime.now()
                stmt = (
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(
                        is_banned=True,
                        is_active=False,
                        updated_at=now,
                        metadata=func.jsonb_set(
                            UserModel.metadata,
                            "{ban_reason}",
                            f'"{reason}"' if reason else '"No reason provided"'
                        ) if reason else UserModel.metadata,
                    )
                    .returning(UserModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.info(f"User {user_id} banned. Reason: {reason}")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error banning user {user_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در مسدودسازی کاربر: {str(e)}",
                    context={"user_id": user_id},
                )

    async def unban_user(self, user_id: int) -> Optional[User]:
        """
        رفع مسدودیت یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            کاربر به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        async with self._session_manager.session() as session:
            try:
                now = datetime.now()
                stmt = (
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(
                        is_banned=False,
                        is_active=True,
                        updated_at=now,
                    )
                    .returning(UserModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.info(f"User {user_id} unbanned")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error unbanning user {user_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در رفع مسدودیت کاربر: {str(e)}",
                    context={"user_id": user_id},
                )

    async def get_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی کاربران.

        Returns:
            دیکشنری شامل آمار.
        """
        async with self._session_manager.session() as session:
            try:
                # تعداد کل کاربران
                total = await session.execute(select(func.count()).select_from(UserModel))
                total_users = total.scalar_one()

                # کاربران فعال
                active = await session.execute(
                    select(func.count()).select_from(UserModel).where(
                        and_(UserModel.is_active == True, UserModel.is_banned == False)
                    )
                )
                active_users = active.scalar_one()

                # کاربران مسدود
                banned = await session.execute(
                    select(func.count()).select_from(UserModel).where(UserModel.is_banned == True)
                )
                banned_users = banned.scalar_one()

                # کاربران به‌تفکیک نقش
                roles = {}
                for role in UserRole:
                    count = await session.execute(
                        select(func.count()).select_from(UserModel).where(UserModel.role == role.value)
                    )
                    roles[role.value] = count.scalar_one()

                # کاربران به‌تفکیک سطح
                levels = {}
                for level in UserLevel:
                    count = await session.execute(
                        select(func.count()).select_from(UserModel).where(UserModel.level == level.value)
                    )
                    levels[level.value] = count.scalar_one()

                # کاربران امروز
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                today = await session.execute(
                    select(func.count()).select_from(UserModel).where(
                        UserModel.created_at >= today_start
                    )
                )
                users_today = today.scalar_one()

                # کاربران این هفته
                week_start = today_start - timedelta(days=datetime.now().weekday())
                week = await session.execute(
                    select(func.count()).select_from(UserModel).where(
                        UserModel.created_at >= week_start
                    )
                )
                users_this_week = week.scalar_one()

                # کاربران این ماه
                month_start = today_start.replace(day=1)
                month = await session.execute(
                    select(func.count()).select_from(UserModel).where(
                        UserModel.created_at >= month_start
                    )
                )
                users_this_month = month.scalar_one()

                return {
                    "total_users": total_users,
                    "active_users": active_users,
                    "banned_users": banned_users,
                    "users_by_role": roles,
                    "users_by_level": levels,
                    "users_today": users_today,
                    "users_this_week": users_this_week,
                    "users_this_month": users_this_month,
                }
            except Exception as e:
                logger.error(f"Error getting user statistics: {e}")
                raise QueryError(
                    query="SELECT user statistics",
                    reason=str(e),
                )