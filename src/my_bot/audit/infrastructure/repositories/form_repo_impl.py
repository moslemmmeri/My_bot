# my_bot_project/src/my_bot/infrastructure/repositories/form_repo_impl.py
"""
پیاده‌سازی ریپازیتوری فرم (Form Repository Implementation).

این کلاس پیاده‌سازی عینی از اینترفیس FormRepository است که با استفاده
از SQLAlchemy و DatabaseSessionManager، عملیات CRUD و جستجو روی
جداول forms، form_fields، form_responses و form_analytics را انجام می‌دهد.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select, delete, update, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from my_bot.core.constants.form_types import FormType
from my_bot.core.exceptions.db_errors import DatabaseError, QueryError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.form import Form
from my_bot.domain.entities.form_response import FormResponse
from my_bot.domain.interfaces.repositories.form_repository import FormRepository
from my_bot.infrastructure.database.models.form_model import FormModel
from my_bot.infrastructure.database.models.form_field_model import FormFieldModel
from my_bot.infrastructure.database.models.form_response_model import FormResponseModel
from my_bot.infrastructure.database.models.form_analytics_model import FormAnalyticsModel
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager

logger = get_logger(__name__)


class FormRepositoryImpl(FormRepository):
    """
    پیاده‌سازی ریپازیتوری فرم با استفاده از SQLAlchemy.

    این کلاس تمام متدهای اینترفیس FormRepository را پیاده‌سازی می‌کند
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
        logger.info("FormRepositoryImpl initialized.")

    # ----------------------------------------------
    # متدهای مربوط به Form
    # ----------------------------------------------

    async def get_by_id(self, form_id: int) -> Optional[Form]:
        """
        دریافت فرم با شناسه داخلی.

        Args:
            form_id: شناسه فرم در دیتابیس.

        Returns:
            فرم در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(FormModel)
                    .where(FormModel.id == form_id)
                    .options(
                        selectinload(FormModel.fields_models),
                        selectinload(FormModel.creator),
                    )
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting form by id {form_id}: {e}")
                raise QueryError(
                    query="SELECT forms WHERE id = :form_id",
                    reason=str(e),
                )

    async def get_by_title(self, title: str) -> Optional[Form]:
        """
        دریافت فرم با عنوان.

        Args:
            title: عنوان فرم.

        Returns:
            فرم در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(FormModel)
                    .where(FormModel.title == title)
                    .options(
                        selectinload(FormModel.fields_models),
                        selectinload(FormModel.creator),
                    )
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting form by title {title}: {e}")
                raise QueryError(
                    query="SELECT forms WHERE title = :title",
                    reason=str(e),
                )

    async def get_by_type(
        self,
        form_type: FormType,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> List[Form]:
        """
        دریافت فرم‌ها با نوع مشخص.

        Args:
            form_type: نوع فرم.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            is_active: فیلتر بر اساس فعال بودن (اختیاری).

        Returns:
            لیست فرم‌ها با نوع مشخص.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(FormModel).where(FormModel.form_type == form_type.value)
                if is_active is not None:
                    stmt = stmt.where(FormModel.is_active == is_active)
                stmt = (
                    stmt.options(
                        selectinload(FormModel.fields_models),
                        selectinload(FormModel.creator),
                    )
                    .order_by(desc(FormModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting forms by type {form_type.value}: {e}")
                raise QueryError(
                    query="SELECT forms WHERE form_type = :form_type",
                    reason=str(e),
                )

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_public: Optional[bool] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[Form]:
        """
        دریافت لیست فرم‌ها با صفحه‌بندی و فیلترهای اختیاری.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            is_active: فیلتر بر اساس فعال بودن (اختیاری).
            is_public: فیلتر بر اساس عمومی بودن (اختیاری).
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی، False برای صعودی.

        Returns:
            لیست فرم‌ها.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(FormModel)
                if is_active is not None:
                    stmt = stmt.where(FormModel.is_active == is_active)
                if is_public is not None:
                    stmt = stmt.where(FormModel.is_public == is_public)

                order_col = getattr(FormModel, order_by, FormModel.created_at)
                order_expr = order_col.desc() if order_desc else order_col.asc()

                stmt = (
                    stmt.options(
                        selectinload(FormModel.fields_models),
                        selectinload(FormModel.creator),
                    )
                    .order_by(order_expr)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting all forms: {e}")
                raise QueryError(
                    query="SELECT forms WITH pagination",
                    reason=str(e),
                )

    async def save(self, form: Form) -> Form:
        """
        ذخیره یا به‌روزرسانی یک فرم در دیتابیس.

        Args:
            form: موجودیت فرم برای ذخیره‌سازی.

        Returns:
            فرم ذخیره‌شده با شناسه و تاریخ‌های به‌روزرسانی‌شده.
        """
        async with self._session_manager.session() as session:
            try:
                if form.id:
                    # به‌روزرسانی
                    # ابتدا فیلدهای قدیمی را حذف می‌کنیم
                    await session.execute(
                        delete(FormFieldModel).where(FormFieldModel.form_id == form.id)
                    )

                    # به‌روزرسانی فرم
                    stmt = (
                        update(FormModel)
                        .where(FormModel.id == form.id)
                        .values(
                            title=form.title,
                            description=form.description,
                            form_type=form.form_type.value if form.form_type else FormType.CUSTOM.value,
                            fields=[field.to_dict() for field in form.fields],
                            is_active=form.is_active,
                            is_public=form.is_public,
                            requires_login=form.requires_login,
                            is_multistep=form.is_multistep,
                            steps=form.steps,
                            submit_button_text=form.submit_button_text,
                            success_message=form.success_message,
                            redirect_url=form.redirect_url,
                            published_at=form.published_at,
                            expires_at=form.expires_at,
                            max_submissions=form.max_submissions,
                            submission_count=form.submission_count,
                            updated_at=datetime.now(),
                            metadata=form.metadata,
                            submission_message=form.success_message,
                        )
                        .returning(FormModel)
                    )
                    result = await session.execute(stmt)
                    model = result.scalar_one_or_none()

                    if not model:
                        raise DatabaseError(
                            message=f"Form with id {form.id} not found for update.",
                            context={"form_id": form.id},
                        )

                    # افزودن فیلدهای جدید
                    for field in form.fields:
                        field_model = FormFieldModel.from_domain(field)
                        field_model.form_id = model.id
                        session.add(field_model)

                    await session.commit()
                    await session.refresh(model)

                    # بارگذاری مجدد با روابط
                    stmt = (
                        select(FormModel)
                        .where(FormModel.id == model.id)
                        .options(
                            selectinload(FormModel.fields_models),
                            selectinload(FormModel.creator),
                        )
                    )
                    result = await session.execute(stmt)
                    model = result.scalar_one()

                    logger.debug(f"Form updated: id={model.id}")
                    return model.to_domain()
                else:
                    # ایجاد جدید
                    model = FormModel.from_domain(form)
                    session.add(model)
                    await session.commit()
                    await session.refresh(model)

                    # بارگذاری مجدد با روابط
                    stmt = (
                        select(FormModel)
                        .where(FormModel.id == model.id)
                        .options(
                            selectinload(FormModel.fields_models),
                            selectinload(FormModel.creator),
                        )
                    )
                    result = await session.execute(stmt)
                    model = result.scalar_one()

                    logger.info(f"Form created: id={model.id}, title={model.title}")
                    return model.to_domain()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving form: {e}")
                raise DatabaseError(
                    message=f"خطا در ذخیره‌سازی فرم: {str(e)}",
                    context={"form_id": form.id, "title": form.title},
                )

    async def delete(self, form_id: int) -> bool:
        """
        حذف یک فرم از دیتابیس.

        Args:
            form_id: شناسه فرم برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود فرم.
        """
        async with self._session_manager.session() as session:
            try:
                # فیلدها و پاسخ‌ها به‌صورت خودکار با CASCADE حذف می‌شوند
                stmt = delete(FormModel).where(FormModel.id == form_id)
                result = await session.execute(stmt)
                await session.commit()
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Form deleted: id={form_id}")
                else:
                    logger.debug(f"Form not found for deletion: id={form_id}")
                return deleted
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting form {form_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در حذف فرم: {str(e)}",
                    context={"form_id": form_id},
                )

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        شمارش تعداد فرم‌ها با اعمال فیلترهای اختیاری.

        Args:
            filters: دیکشنری فیلترها (اختیاری).

        Returns:
            تعداد فرم‌ها.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(FormModel)
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        if hasattr(FormModel, key):
                            conditions.append(getattr(FormModel, key) == value)
                    if conditions:
                        stmt = stmt.where(and_(*conditions))
                result = await session.execute(stmt)
                return result.scalar_one()
            except Exception as e:
                logger.error(f"Error counting forms: {e}")
                raise QueryError(
                    query="COUNT forms WITH filters",
                    reason=str(e),
                )

    async def exists_by_title(self, title: str, exclude_id: Optional[int] = None) -> bool:
        """
        بررسی وجود فرم با عنوان مشخص.

        Args:
            title: عنوان فرم.
            exclude_id: شناسه فرم برای حذف از بررسی (اختیاری).

        Returns:
            True اگر فرم وجود داشته باشد، در غیر این صورت False.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(FormModel).where(FormModel.title == title)
                if exclude_id:
                    stmt = stmt.where(FormModel.id != exclude_id)
                result = await session.execute(stmt)
                count = result.scalar_one()
                return count > 0
            except Exception as e:
                logger.error(f"Error checking existence by title {title}: {e}")
                return False

    async def get_active_forms(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Form]:
        """
        دریافت فرم‌های فعال (قابل ارسال).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست فرم‌های فعال.
        """
        async with self._session_manager.session() as session:
            try:
                now = datetime.now()
                stmt = (
                    select(FormModel)
                    .where(
                        and_(
                            FormModel.is_active == True,
                            or_(
                                FormModel.expires_at.is_(None),
                                FormModel.expires_at >= now,
                            ),
                            or_(
                                FormModel.published_at.is_(None),
                                FormModel.published_at <= now,
                            ),
                            or_(
                                FormModel.max_submissions.is_(None),
                                FormModel.submission_count < FormModel.max_submissions,
                            ),
                        )
                    )
                    .options(
                        selectinload(FormModel.fields_models),
                        selectinload(FormModel.creator),
                    )
                    .order_by(FormModel.created_at)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting active forms: {e}")
                raise QueryError(
                    query="SELECT active forms",
                    reason=str(e),
                )

    async def get_public_forms(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Form]:
        """
        دریافت فرم‌های عمومی (قابل مشاهده برای همه کاربران).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست فرم‌های عمومی.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(FormModel)
                    .where(
                        and_(
                            FormModel.is_public == True,
                            FormModel.is_active == True,
                        )
                    )
                    .options(
                        selectinload(FormModel.fields_models),
                        selectinload(FormModel.creator),
                    )
                    .order_by(FormModel.created_at)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting public forms: {e}")
                raise QueryError(
                    query="SELECT public forms",
                    reason=str(e),
                )

    async def get_forms_by_creator(
        self,
        created_by: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Form]:
        """
        دریافت فرم‌های ساخته‌شده توسط یک ادمین خاص.

        Args:
            created_by: شناسه کاربر سازنده.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست فرم‌های ساخته‌شده.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(FormModel)
                    .where(FormModel.created_by == created_by)
                    .options(
                        selectinload(FormModel.fields_models),
                        selectinload(FormModel.creator),
                    )
                    .order_by(desc(FormModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting forms by creator {created_by}: {e}")
                raise QueryError(
                    query="SELECT forms WHERE created_by = :created_by",
                    reason=str(e),
                )

    async def get_forms_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Form]:
        """
        دریافت فرم‌های ایجادشده در بازه زمانی مشخص.

        Args:
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست فرم‌ها در بازه زمانی.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(FormModel)
                    .where(
                        and_(
                            FormModel.created_at >= start_date,
                            FormModel.created_at <= end_date,
                        )
                    )
                    .options(
                        selectinload(FormModel.fields_models),
                        selectinload(FormModel.creator),
                    )
                    .order_by(FormModel.created_at)
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting forms by date range: {e}")
                raise QueryError(
                    query="SELECT forms by date range",
                    reason=str(e),
                )

    async def update_status(self, form_id: int, is_active: bool) -> Optional[Form]:
        """
        به‌روزرسانی وضعیت فعال بودن یک فرم.

        Args:
            form_id: شناسه فرم.
            is_active: وضعیت جدید.

        Returns:
            فرم به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    update(FormModel)
                    .where(FormModel.id == form_id)
                    .values(
                        is_active=is_active,
                        updated_at=datetime.now(),
                    )
                    .returning(FormModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.info(f"Form {form_id} status updated to is_active={is_active}")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating form status {form_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در به‌روزرسانی وضعیت فرم: {str(e)}",
                    context={"form_id": form_id, "is_active": is_active},
                )

    async def increment_submission_count(self, form_id: int) -> Optional[Form]:
        """
        افزایش تعداد ارسال‌های فرم.

        Args:
            form_id: شناسه فرم.

        Returns:
            فرم به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    update(FormModel)
                    .where(FormModel.id == form_id)
                    .values(
                        submission_count=FormModel.submission_count + 1,
                        updated_at=datetime.now(),
                    )
                    .returning(FormModel)
                )
                result = await session.execute(stmt)
                await session.commit()
                model = result.scalar_one_or_none()
                if model:
                    logger.debug(f"Form {form_id} submission count incremented to {model.submission_count}")
                    return model.to_domain()
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error incrementing form submission count {form_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در افزایش تعداد ارسال فرم: {str(e)}",
                    context={"form_id": form_id},
                )

    async def get_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی فرم‌ها.

        Returns:
            دیکشنری شامل آمار.
        """
        async with self._session_manager.session() as session:
            try:
                # تعداد کل فرم‌ها
                total = await session.execute(
                    select(func.count()).select_from(FormModel)
                )
                total_forms = total.scalar_one()

                # فرم‌های فعال
                active = await session.execute(
                    select(func.count()).select_from(FormModel).where(
                        FormModel.is_active == True
                    )
                )
                active_forms = active.scalar_one()

                # فرم‌های غیرفعال
                inactive = total_forms - active_forms

                # فرم‌های عمومی
                public = await session.execute(
                    select(func.count()).select_from(FormModel).where(
                        FormModel.is_public == True
                    )
                )
                public_forms = public.scalar_one()

                # فرم‌های خصوصی
                private = total_forms - public_forms

                # فرم‌ها به‌تفکیک نوع
                types = {}
                for form_type in FormType:
                    count = await session.execute(
                        select(func.count()).select_from(FormModel).where(
                            FormModel.form_type == form_type.value
                        )
                    )
                    types[form_type.value] = count.scalar_one()

                # مجموع ارسال‌ها
                total_submissions = await session.execute(
                    select(func.sum(FormModel.submission_count)).select_from(FormModel)
                )
                total_submissions_count = total_submissions.scalar_one() or 0

                # فرم‌های امروز، این هفته، این ماه
                now = datetime.now()
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                week_start = today_start - timedelta(days=now.weekday())
                month_start = today_start.replace(day=1)

                created_today = await session.execute(
                    select(func.count()).select_from(FormModel).where(
                        FormModel.created_at >= today_start
                    )
                )
                forms_created_today = created_today.scalar_one()

                created_week = await session.execute(
                    select(func.count()).select_from(FormModel).where(
                        FormModel.created_at >= week_start
                    )
                )
                forms_created_this_week = created_week.scalar_one()

                created_month = await session.execute(
                    select(func.count()).select_from(FormModel).where(
                        FormModel.created_at >= month_start
                    )
                )
                forms_created_this_month = created_month.scalar_one()

                return {
                    "total_forms": total_forms,
                    "active_forms": active_forms,
                    "inactive_forms": inactive,
                    "public_forms": public_forms,
                    "private_forms": private,
                    "forms_by_type": types,
                    "total_submissions": total_submissions_count,
                    "forms_created_today": forms_created_today,
                    "forms_created_this_week": forms_created_this_week,
                    "forms_created_this_month": forms_created_this_month,
                }
            except Exception as e:
                logger.error(f"Error getting form statistics: {e}")
                raise QueryError(
                    query="SELECT form statistics",
                    reason=str(e),
                )

    async def search_forms(
        self,
        query: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Form]:
        """
        جستجوی فرم‌ها با استفاده از متن (عنوان، توضیحات).

        Args:
            query: عبارت جستجو.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست فرم‌های مطابق با عبارت جستجو.
        """
        async with self._session_manager.session() as session:
            try:
                search_term = f"%{query}%"
                stmt = (
                    select(FormModel)
                    .where(
                        or_(
                            FormModel.title.ilike(search_term),
                            FormModel.description.ilike(search_term),
                        )
                    )
                    .options(
                        selectinload(FormModel.fields_models),
                        selectinload(FormModel.creator),
                    )
                    .order_by(desc(FormModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error searching forms with query '{query}': {e}")
                raise QueryError(
                    query="SEARCH forms",
                    reason=str(e),
                )

    async def get_forms_with_submissions(
        self,
        min_submissions: int = 1,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Form]:
        """
        دریافت فرم‌هایی که حداقل تعداد ارسال مشخص را دارند.

        Args:
            min_submissions: حداقل تعداد ارسال.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست فرم‌های با ارسال‌های کافی.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(FormModel)
                    .where(FormModel.submission_count >= min_submissions)
                    .options(
                        selectinload(FormModel.fields_models),
                        selectinload(FormModel.creator),
                    )
                    .order_by(desc(FormModel.submission_count))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting forms with submissions: {e}")
                raise QueryError(
                    query="SELECT forms with submissions",
                    reason=str(e),
                )

    async def get_most_popular_forms(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        دریافت محبوب‌ترین فرم‌ها بر اساس تعداد ارسال.

        Args:
            limit: حداکثر تعداد فرم‌ها.
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            لیست دیکشنری‌های شامل شناسه فرم، عنوان، تعداد ارسال.
        """
        async with self._session_manager.session() as session:
            try:
                conditions = []
                if start_date:
                    conditions.append(FormModel.created_at >= start_date)
                if end_date:
                    conditions.append(FormModel.created_at <= end_date)

                stmt = select(
                    FormModel.id,
                    FormModel.title,
                    FormModel.submission_count,
                )
                if conditions:
                    stmt = stmt.where(and_(*conditions))
                stmt = stmt.order_by(desc(FormModel.submission_count)).limit(limit)

                result = await session.execute(stmt)
                rows = result.all()
                return [
                    {
                        "form_id": row.id,
                        "title": row.title,
                        "submission_count": row.submission_count,
                    }
                    for row in rows
                ]
            except Exception as e:
                logger.error(f"Error getting most popular forms: {e}")
                raise QueryError(
                    query="SELECT most popular forms",
                    reason=str(e),
                )

    async def get_forms_needing_review(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Form]:
        """
        دریافت فرم‌هایی که نیاز به بررسی دارند (وضعیت ON_HOLD یا مشابه).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست فرم‌های نیازمند بررسی.
        """
        async with self._session_manager.session() as session:
            try:
                # فرم‌هایی که نیاز به بررسی دارند: فرم‌های با submission_count بالا
                # و فرم‌هایی که اخیراً ایجاد شده‌اند اما هنوز منتشر نشده‌اند
                stmt = (
                    select(FormModel)
                    .where(
                        or_(
                            # فرم‌هایی که منتشر نشده‌اند و به‌تازگی ایجاد شده‌اند (کمتر از 7 روز)
                            and_(
                                FormModel.published_at.is_(None),
                                FormModel.created_at >= datetime.now() - timedelta(days=7),
                            ),
                            # فرم‌هایی که بیش از ۵۰ ارسال دارند (نیاز به بررسی کیفیت)
                            FormModel.submission_count > 50,
                        )
                    )
                    .options(
                        selectinload(FormModel.fields_models),
                        selectinload(FormModel.creator),
                    )
                    .order_by(desc(FormModel.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting forms needing review: {e}")
                raise QueryError(
                    query="SELECT forms needing review",
                    reason=str(e),
                )

    async def get_forms_by_step_count(
        self,
        min_steps: int = 2,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Form]:
        """
        دریافت فرم‌های چند مرحله‌ای با حداقل تعداد مراحل مشخص.

        Args:
            min_steps: حداقل تعداد مراحل.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست فرم‌های چند مرحله‌ای.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = (
                    select(FormModel)
                    .where(
                        and_(
                            FormModel.is_multistep == True,
                            FormModel.steps >= min_steps,
                        )
                    )
                    .options(
                        selectinload(FormModel.fields_models),
                        selectinload(FormModel.creator),
                    )
                    .order_by(desc(FormModel.steps))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting forms by step count: {e}")
                raise QueryError(
                    query="SELECT forms by step count",
                    reason=str(e),
                )

    async def get_expired_forms(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Form]:
        """
        دریافت فرم‌های منقضی‌شده (expires_at گذشته).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست فرم‌های منقضی‌شده.
        """
        async with self._session_manager.session() as session:
            try:
                now = datetime.now()
                stmt = (
                    select(FormModel)
                    .where(
                        and_(
                            FormModel.expires_at.is_not(None),
                            FormModel.expires_at < now,
                        )
                    )
                    .options(
                        selectinload(FormModel.fields_models),
                        selectinload(FormModel.creator),
                    )
                    .order_by(desc(FormModel.expires_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting expired forms: {e}")
                raise QueryError(
                    query="SELECT expired forms",
                    reason=str(e),
                )

    # ----------------------------------------------
    # متدهای مربوط به FormResponse
    # ----------------------------------------------

    async def save_response(self, response: FormResponse) -> FormResponse:
        """
        ذخیره یک پاسخ فرم در دیتابیس.

        Args:
            response: موجودیت پاسخ فرم برای ذخیره‌سازی.

        Returns:
            پاسخ فرم ذخیره‌شده با شناسه.
        """
        async with self._session_manager.session() as session:
            try:
                model = FormResponseModel.from_domain(response)
                session.add(model)
                await session.commit()
                await session.refresh(model)
                logger.debug(f"Form response created: id={model.id}, form_id={model.form_id}")
                return model.to_domain()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving form response: {e}")
                raise DatabaseError(
                    message=f"خطا در ذخیره‌سازی پاسخ فرم: {str(e)}",
                    context={"form_id": response.form_id, "user_id": response.user_id},
                )

    async def get_response_by_id(self, response_id: int) -> Optional[FormResponse]:
        """
        دریافت یک پاسخ فرم با شناسه.

        Args:
            response_id: شناسه پاسخ.

        Returns:
            پاسخ فرم در صورت وجود، در غیر این صورت None.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(FormResponseModel).where(FormResponseModel.id == response_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    return model.to_domain()
                return None
            except Exception as e:
                logger.error(f"Error getting form response by id {response_id}: {e}")
                raise QueryError(
                    query="SELECT form_responses WHERE id = :response_id",
                    reason=str(e),
                )

    async def get_responses_by_user(
        self,
        user_id: int,
        form_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FormResponse]:
        """
        دریافت پاسخ‌های یک کاربر.

        Args:
            user_id: شناسه کاربر.
            form_id: فیلتر بر اساس فرم (اختیاری).
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست پاسخ‌های کاربر.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(FormResponseModel).where(FormResponseModel.user_id == user_id)
                if form_id:
                    stmt = stmt.where(FormResponseModel.form_id == form_id)
                stmt = (
                    stmt.order_by(desc(FormResponseModel.submitted_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting form responses for user {user_id}: {e}")
                raise QueryError(
                    query="SELECT form_responses WHERE user_id = :user_id",
                    reason=str(e),
                )

    async def get_responses_by_form(
        self,
        form_id: int,
        skip: int = 0,
        limit: int = 100,
        include_invalid: bool = False,
    ) -> List[FormResponse]:
        """
        دریافت تمام پاسخ‌های یک فرم.

        Args:
            form_id: شناسه فرم.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            include_invalid: شامل پاسخ‌های نامعتبر (پیش‌فرض False).

        Returns:
            لیست پاسخ‌های فرم.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(FormResponseModel).where(FormResponseModel.form_id == form_id)
                if not include_invalid:
                    stmt = stmt.where(FormResponseModel.is_valid == True)
                stmt = (
                    stmt.order_by(desc(FormResponseModel.submitted_at))
                    .offset(skip)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [model.to_domain() for model in models]
            except Exception as e:
                logger.error(f"Error getting form responses for form {form_id}: {e}")
                raise QueryError(
                    query="SELECT form_responses WHERE form_id = :form_id",
                    reason=str(e),
                )

    async def get_response_statistics(self, form_id: int) -> Dict[str, Any]:
        """
        دریافت آمار پاسخ‌های یک فرم.

        Args:
            form_id: شناسه فرم.

        Returns:
            دیکشنری شامل آمار پاسخ‌ها.
        """
        async with self._session_manager.session() as session:
            try:
                # تعداد کل پاسخ‌ها
                total = await session.execute(
                    select(func.count()).select_from(FormResponseModel).where(
                        FormResponseModel.form_id == form_id
                    )
                )
                total_responses = total.scalar_one()

                # پاسخ‌های معتبر
                valid = await session.execute(
                    select(func.count()).select_from(FormResponseModel).where(
                        and_(
                            FormResponseModel.form_id == form_id,
                            FormResponseModel.is_valid == True,
                        )
                    )
                )
                valid_responses = valid.scalar_one()

                # پاسخ‌های نامعتبر
                invalid = total_responses - valid_responses

                # کاربران یکتا
                unique_users = await session.execute(
                    select(func.count(func.distinct(FormResponseModel.user_id))).where(
                        FormResponseModel.form_id == form_id
                    )
                )
                unique_users_count = unique_users.scalar_one()

                # پاسخ‌های امروز، این هفته، این ماه
                now = datetime.now()
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                week_start = today_start - timedelta(days=now.weekday())
                month_start = today_start.replace(day=1)

                responses_today = await session.execute(
                    select(func.count()).select_from(FormResponseModel).where(
                        and_(
                            FormResponseModel.form_id == form_id,
                            FormResponseModel.submitted_at >= today_start,
                        )
                    )
                )
                responses_today_count = responses_today.scalar_one()

                responses_week = await session.execute(
                    select(func.count()).select_from(FormResponseModel).where(
                        and_(
                            FormResponseModel.form_id == form_id,
                            FormResponseModel.submitted_at >= week_start,
                        )
                    )
                )
                responses_week_count = responses_week.scalar_one()

                responses_month = await session.execute(
                    select(func.count()).select_from(FormResponseModel).where(
                        and_(
                            FormResponseModel.form_id == form_id,
                            FormResponseModel.submitted_at >= month_start,
                        )
                    )
                )
                responses_month_count = responses_month.scalar_one()

                # آخرین پاسخ
                last_response = await session.execute(
                    select(FormResponseModel.submitted_at)
                    .where(FormResponseModel.form_id == form_id)
                    .order_by(desc(FormResponseModel.submitted_at))
                    .limit(1)
                )
                last_response_at = last_response.scalar_one_or_none()

                return {
                    "total_responses": total_responses,
                    "valid_responses": valid_responses,
                    "invalid_responses": invalid,
                    "unique_users": unique_users_count,
                    "submission_rate": (valid_responses / total_responses * 100) if total_responses > 0 else 0,
                    "responses_today": responses_today_count,
                    "responses_this_week": responses_week_count,
                    "responses_this_month": responses_month_count,
                    "last_response_at": last_response_at,
                }
            except Exception as e:
                logger.error(f"Error getting form response statistics for form {form_id}: {e}")
                raise QueryError(
                    query="SELECT form response statistics",
                    reason=str(e),
                )

    async def has_user_submitted(self, form_id: int, user_id: int) -> bool:
        """
        بررسی اینکه آیا کاربر قبلاً این فرم را ارسال کرده است.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر.

        Returns:
            True اگر کاربر قبلاً ارسال کرده باشد.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = select(func.count()).select_from(FormResponseModel).where(
                    and_(
                        FormResponseModel.form_id == form_id,
                        FormResponseModel.user_id == user_id,
                    )
                )
                result = await session.execute(stmt)
                count = result.scalar_one()
                return count > 0
            except Exception as e:
                logger.error(f"Error checking if user {user_id} submitted form {form_id}: {e}")
                return False

    async def delete_response(self, response_id: int) -> bool:
        """
        حذف یک پاسخ فرم.

        Args:
            response_id: شناسه پاسخ.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود.
        """
        async with self._session_manager.session() as session:
            try:
                stmt = delete(FormResponseModel).where(FormResponseModel.id == response_id)
                result = await session.execute(stmt)
                await session.commit()
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Form response deleted: id={response_id}")
                else:
                    logger.debug(f"Form response not found for deletion: id={response_id}")
                return deleted
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting form response {response_id}: {e}")
                raise DatabaseError(
                    message=f"خطا در حذف پاسخ فرم: {str(e)}",
                    context={"response_id": response_id},
                )

    # ----------------------------------------------
    # متدهای مربوط به Form Analytics
    # ----------------------------------------------

    async def get_form_analytics(
        self,
        form_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        دریافت تحلیل فرم (آمار روزانه).

        Args:
            form_id: شناسه فرم.
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            دیکشنری شامل تحلیل فرم.
        """
        async with self._session_manager.session() as session:
            try:
                from my_bot.infrastructure.database.models.form_analytics_model import FormAnalyticsModel

                conditions = [FormAnalyticsModel.form_id == form_id]
                if start_date:
                    conditions.append(FormAnalyticsModel.date >= start_date.date())
                if end_date:
                    conditions.append(FormAnalyticsModel.date <= end_date.date())

                stmt = (
                    select(FormAnalyticsModel)
                    .where(and_(*conditions))
                    .order_by(FormAnalyticsModel.date)
                )
                result = await session.execute(stmt)
                models = result.scalars().all()

                analytics_data = []
                for model in models:
                    analytics_data.append({
                        "date": model.date.isoformat(),
                        "views": model.views,
                        "starts": model.starts,
                        "submissions": model.submissions,
                        "abandoned": model.abandoned,
                        "completion_rate": (model.submissions / model.starts * 100) if model.starts > 0 else 0,
                    })

                # محاسبه مجموع
                total_views = sum(a["views"] for a in analytics_data)
                total_starts = sum(a["starts"] for a in analytics_data)
                total_submissions = sum(a["submissions"] for a in analytics_data)
                total_abandoned = sum(a["abandoned"] for a in analytics_data)

                overall_completion_rate = (total_submissions / total_starts * 100) if total_starts > 0 else 0

                return {
                    "form_id": form_id,
                    "period": {
                        "start": start_date.isoformat() if start_date else None,
                        "end": end_date.isoformat() if end_date else None,
                    },
                    "summary": {
                        "total_views": total_views,
                        "total_starts": total_starts,
                        "total_submissions": total_submissions,
                        "total_abandoned": total_abandoned,
                        "overall_completion_rate": overall_completion_rate,
                    },
                    "daily_data": analytics_data,
                }
            except Exception as e:
                logger.error(f"Error getting form analytics for form {form_id}: {e}")
                raise QueryError(
                    query="SELECT form analytics",
                    reason=str(e),
                )