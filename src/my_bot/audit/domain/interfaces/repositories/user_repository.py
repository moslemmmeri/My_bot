# my_bot_project/src/my_bot/domain/interfaces/repositories/user_repository.py
"""
اینترفیس ریپازیتوری کاربر (User Repository Interface).

این اینترفیس قراردادهای لازم برای ذخیره‌سازی، بازیابی و جستجوی
کاربران در سیستم را تعریف می‌کند. پیاده‌سازی این اینترفیس در لایه
زیرساخت (Infrastructure) انجام می‌شود و می‌تواند از دیتابیس‌های
مختلف (PostgreSQL, SQLite) پشتیبانی کند.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple

from my_bot.core.constants.user_roles import UserRole
from my_bot.domain.entities.user import User
from my_bot.domain.value_objects.user_level import UserLevel


class UserRepository(ABC):
    """
    اینترفیس ریپازیتوری کاربر.

    این کلاس مسئولیت مدیریت ذخیره‌سازی، بازیابی و جستجوی کاربران
    در سیستم را بر عهده دارد. تمام متدها به‌صورت async تعریف شده‌اند
    تا با معماری غیرهمگام (asynchronous) پروژه سازگار باشند.
    """

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        دریافت کاربر با شناسه داخلی (Primary Key).

        Args:
            user_id: شناسه کاربر در دیتابیس.

        Returns:
            کاربر در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        دریافت کاربر با شناسه تلگرام.

        Args:
            telegram_id: شناسه تلگرام کاربر (Unique).

        Returns:
            کاربر در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        دریافت کاربر با نام کاربری تلگرام.

        Args:
            username: نام کاربری (بدون @).

        Returns:
            کاربر در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        دریافت کاربر با آدرس ایمیل.

        Args:
            email: آدرس ایمیل.

        Returns:
            کاربر در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
    async def get_by_phone(self, phone: str) -> Optional[User]:
        """
        دریافت کاربر با شماره تلفن.

        Args:
            phone: شماره تلفن.

        Returns:
            کاربر در صورت وجود، در غیر این صورت None.
        """
        pass

    @abstractmethod
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
            skip: تعداد رکوردهای نادیده گرفته شده (offset).
            limit: حداکثر تعداد رکوردهای برگشتی.
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی، False برای صعودی.

        Returns:
            لیست کاربران.
        """
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        """
        ذخیره یا به‌روزرسانی یک کاربر در دیتابیس.

        اگر کاربر شناسه (id) نداشته باشد، ایجاد می‌شود و
        در غیر این صورت به‌روزرسانی می‌گردد.

        Args:
            user: موجودیت کاربر برای ذخیره‌سازی.

        Returns:
            کاربر ذخیره‌شده با شناسه و تاریخ‌های به‌روزرسانی‌شده.
        """
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """
        حذف یک کاربر از دیتابیس.

        Args:
            user_id: شناسه کاربر برای حذف.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود کاربر.
        """
        pass

    @abstractmethod
    async def exists_by_telegram_id(self, telegram_id: int) -> bool:
        """
        بررسی وجود کاربر با شناسه تلگرام.

        Args:
            telegram_id: شناسه تلگرام.

        Returns:
            True اگر کاربر وجود داشته باشد، در غیر این صورت False.
        """
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """
        بررسی وجود کاربر با آدرس ایمیل.

        Args:
            email: آدرس ایمیل.

        Returns:
            True اگر کاربر وجود داشته باشد، در غیر این صورت False.
        """
        pass

    @abstractmethod
    async def exists_by_phone(self, phone: str) -> bool:
        """
        بررسی وجود کاربر با شماره تلفن.

        Args:
            phone: شماره تلفن.

        Returns:
            True اگر کاربر وجود داشته باشد، در غیر این صورت False.
        """
        pass

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """
        بررسی وجود کاربر با نام کاربری.

        Args:
            username: نام کاربری.

        Returns:
            True اگر کاربر وجود داشته باشد، در غیر این صورت False.
        """
        pass

    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        شمارش تعداد کاربران با اعمال فیلترهای اختیاری.

        Args:
            filters: دیکشنری فیلترها (اختیاری).

        Returns:
            تعداد کاربران.
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[User]:
        """
        جستجوی کاربران با استفاده از متن (نام، نام کاربری، ایمیل، تلفن).

        Args:
            query: عبارت جستجو.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کاربران مطابق با عبارت جستجو.
        """
        pass

    @abstractmethod
    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """
        دریافت کاربران فعال (حساب فعال و مسدود نشده).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            لیست کاربران فعال.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def update_points(self, user_id: int, points_change: int) -> Optional[User]:
        """
        افزایش یا کاهش امتیاز کاربر.

        Args:
            user_id: شناسه کاربر.
            points_change: مقدار تغییر امتیاز (مثبت برای افزایش، منفی برای کاهش).

        Returns:
            کاربر به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def update_last_activity(self, user_id: int) -> Optional[User]:
        """
        به‌روزرسانی زمان آخرین فعالیت کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            کاربر به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Tuple[User, bool]:
        """
        دریافت کاربر موجود یا ایجاد کاربر جدید با اطلاعات تلگرام.

        Args:
            telegram_id: شناسه تلگرام.
            username: نام کاربری (اختیاری).
            first_name: نام کوچک (اختیاری).
            last_name: نام خانوادگی (اختیاری).

        Returns:
            Tuple شامل کاربر و boolean (True اگر کاربر جدید ایجاد شده باشد).
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def ban_user(self, user_id: int, reason: Optional[str] = None) -> Optional[User]:
        """
        مسدود کردن یک کاربر.

        Args:
            user_id: شناسه کاربر.
            reason: دلیل مسدودسازی (اختیاری).

        Returns:
            کاربر به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def unban_user(self, user_id: int) -> Optional[User]:
        """
        رفع مسدودیت یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            کاربر به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی کاربران.

        Returns:
            دیکشنری شامل آمار:
            - total_users: تعداد کل کاربران
            - active_users: تعداد کاربران فعال
            - banned_users: تعداد کاربران مسدود
            - users_by_role: تعداد کاربران به‌تفکیک نقش
            - users_by_level: تعداد کاربران به‌تفکیک سطح
            - users_today: تعداد کاربران ثبت‌نام‌شده امروز
            - users_this_week: تعداد کاربران ثبت‌نام‌شده این هفته
            - users_this_month: تعداد کاربران ثبت‌نام‌شده این ماه
        """
        pass