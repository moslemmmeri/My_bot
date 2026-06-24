# my_bot_project/src/my_bot/domain/interfaces/repositories/form_repository.py
"""
اینترفیس ریپازیتوری فرم (Form Repository Interface).

این اینترفیس قراردادهای لازم برای ذخیره‌سازی، بازیابی و جستجوی
فرم‌های پویا در سیستم را تعریف می‌کند. پیاده‌سازی این اینترفیس
در لایه زیرساخت (Infrastructure) انجام می‌شود.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from my_bot.core.constants.form_types import FormType
from my_bot.domain.entities.form import Form
from my_bot.domain.entities.form_response import FormResponse


class FormRepository(ABC):
    """
    اینترفیس ریپازیتوری فرم.

    این کلاس مسئولیت مدیریت ذخیره‌سازی، بازیابی و جستجوی فرم‌ها
    در سیستم را بر عهده دارد.
    """

    @abstractmethod
    async def get_by_id(self, form_id: int) -> Optional[Form]:
        """
        دریافت فرم با شناسه داخلی (Primary Key).

        Args:
            form_id: شناسه فرم در دیتابیس.

        Returns:
            فرم در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_title(self, title: str) -> Optional[Form]:
        """
        دریافت فرم با عنوان (در صورت یکتا بودن عنوان).

        Args:
            title: عنوان فرم.

        Returns:
            فرم در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def save(self, form: Form) -> Form:
        """
        ذخیره یا به‌روزرسانی یک فرم در دیتابیس.

        Args:
            form: موجودیت فرم برای ذخیره‌سازی.

        Returns:
            فرم ذخیره‌شده با شناسه و تاریخ‌های به‌روزرسانی‌شده.
        """
        pass

    @abstractmethod
    async def delete(self, form_id: int) -> bool:
        """
        حذف یک فرم از دیتابیس.

        Args:
            form_id: شناسه فرم برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود فرم.
        """
        pass

    @abstractmethod
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        شمارش تعداد فرم‌ها با اعمال فیلترهای اختیاری.

        Args:
            filters: دیکشنری فیلترها (اختیاری).

        Returns:
            تعداد فرم‌ها.
        """
        pass

    @abstractmethod
    async def exists_by_title(self, title: str, exclude_id: Optional[int] = None) -> bool:
        """
        بررسی وجود فرم با عنوان مشخص (به‌جز فرم با شناسه داده‌شده).

        Args:
            title: عنوان فرم.
            exclude_id: شناسه فرم برای حذف از بررسی (اختیاری).

        Returns:
            True اگر فرم وجود داشته باشد، در غیر این صورت False.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def update_status(self, form_id: int, is_active: bool) -> Optional[Form]:
        """
        به‌روزرسانی وضعیت فعال بودن یک فرم.

        Args:
            form_id: شناسه فرم.
            is_active: وضعیت جدید.

        Returns:
            فرم به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def increment_submission_count(self, form_id: int) -> Optional[Form]:
        """
        افزایش تعداد ارسال‌های فرم.

        Args:
            form_id: شناسه فرم.

        Returns:
            فرم به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی فرم‌ها.

        Returns:
            دیکشنری شامل آمار:
            - total_forms: تعداد کل فرم‌ها
            - active_forms: تعداد فرم‌های فعال
            - inactive_forms: تعداد فرم‌های غیرفعال
            - public_forms: تعداد فرم‌های عمومی
            - private_forms: تعداد فرم‌های خصوصی
            - forms_by_type: تعداد فرم‌ها به‌تفکیک نوع
            - total_submissions: تعداد کل ارسال‌ها
            - forms_created_today: تعداد فرم‌های ایجادشده امروز
            - forms_created_this_week: تعداد فرم‌های ایجادشده این هفته
            - forms_created_this_month: تعداد فرم‌های ایجادشده این ماه
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass