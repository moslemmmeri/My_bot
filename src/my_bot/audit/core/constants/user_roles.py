# my_bot_project/src/my_bot/core/constants/user_roles.py
"""
ثابت‌های مربوط به نقش‌های کاربری (User Roles).

این ماژول شامل Enum نقش‌های کاربری در سیستم است که برای کنترل دسترسی
و تعیین سطح دسترسی کاربران به بخش‌های مختلف استفاده می‌شود.
"""

from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    """
    نقش‌های کاربری در سیستم.

    هر نقش دارای سطح دسترسی مشخصی است و برخی نقش‌ها دارای اولویت بیشتر
    نسبت به سایرین هستند.

    Attributes:
        ADMIN: ادمین اصلی سیستم (بالاترین سطح دسترسی)
        MANAGER: مدیر ارشد (دسترسی کامل به پنل مدیریت)
        OPERATOR: اپراتور (دسترسی محدود به پنل مدیریت)
        USER: کاربر عادی (دسترسی به منوی کاربری)
        GUEST: مهمان (دسترسی محدود به بخش‌های عمومی)
    """

    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    USER = "user"
    GUEST = "guest"

    @classmethod
    def from_string(cls, value: str) -> Optional["UserRole"]:
        """
        تبدیل یک رشته به نقش کاربری.

        Args:
            value: رشته‌ای که نمایانگر نقش کاربری است.

        Returns:
            نقش کاربری متناظر با رشته داده شده، یا None در صورت عدم تطابق.
        """
        try:
            return cls(value.lower())
        except ValueError:
            return None

    def is_admin_level(self) -> bool:
        """
        بررسی اینکه آیا نقش دارای سطح دسترسی ادمین است.

        نقش‌های ADMIN و MANAGER و OPERATOR به عنوان سطح ادمین محسوب می‌شوند.
        """
        return self in (UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR)

    def is_manager_level(self) -> bool:
        """
        بررسی اینکه آیا نقش دارای سطح دسترسی مدیریت ارشد است.

        نقش‌های ADMIN و MANAGER به عنوان سطح مدیریت ارشد محسوب می‌شوند.
        """
        return self in (UserRole.ADMIN, UserRole.MANAGER)

    def is_super_admin(self) -> bool:
        """
        بررسی اینکه آیا نقش ادمین اصلی است.
        """
        return self == UserRole.ADMIN

    def can_manage_users(self) -> bool:
        """
        بررسی اینکه آیا نقش مجاز به مدیریت کاربران است.
        """
        return self in (UserRole.ADMIN, UserRole.MANAGER)

    def can_manage_orders(self) -> bool:
        """
        بررسی اینکه آیا نقش مجاز به مدیریت سفارشات است.
        """
        return self in (UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR)

    def can_manage_content(self) -> bool:
        """
        بررسی اینکه آیا نقش مجاز به مدیریت محتوا است.
        """
        return self in (UserRole.ADMIN, UserRole.MANAGER)

    def can_view_analytics(self) -> bool:
        """
        بررسی اینکه آیا نقش مجاز به مشاهده آمار و تحلیلات است.
        """
        return self in (UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR)

    def can_send_broadcast(self) -> bool:
        """
        بررسی اینکه آیا نقش مجاز به ارسال پیام گروهی است.
        """
        return self in (UserRole.ADMIN, UserRole.MANAGER)

    def can_manage_settings(self) -> bool:
        """
        بررسی اینکه آیا نقش مجاز به مدیریت تنظیمات سیستم است.
        """
        return self == UserRole.ADMIN

    def get_display_name(self) -> str:
        """
        دریافت نام نمایشی نقش کاربری (به فارسی).

        Returns:
            نام نمایشی نقش کاربری.
        """
        display_names = {
            UserRole.ADMIN: "مدیر کل",
            UserRole.MANAGER: "مدیر ارشد",
            UserRole.OPERATOR: "اپراتور",
            UserRole.USER: "کاربر عادی",
            UserRole.GUEST: "مهمان",
        }
        return display_names.get(self, self.value)

    def get_permission_level(self) -> int:
        """
        دریافت سطح دسترسی عددی برای مقایسه آسان‌تر.

        سطوح دسترسی:
        - ADMIN: 100
        - MANAGER: 80
        - OPERATOR: 60
        - USER: 40
        - GUEST: 20

        Returns:
            عدد نشان‌دهنده سطح دسترسی.
        """
        levels = {
            UserRole.ADMIN: 100,
            UserRole.MANAGER: 80,
            UserRole.OPERATOR: 60,
            UserRole.USER: 40,
            UserRole.GUEST: 20,
        }
        return levels.get(self, 0)

    def has_higher_or_equal_permission(self, other: "UserRole") -> bool:
        """
        بررسی اینکه آیا نقش فعلی دارای سطح دسترسی بالاتر یا مساوی با نقش دیگر است.

        Args:
            other: نقش دیگر برای مقایسه.

        Returns:
            True اگر سطح دسترسی نقش فعلی >= سطح دسترسی نقش دیگر باشد.
        """
        return self.get_permission_level() >= other.get_permission_level()


# لیست نقش‌های قابل دسترسی در پنل مدیریت
ADMIN_ROLES = (UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR)

# لیست نقش‌های با دسترسی کامل
FULL_ACCESS_ROLES = (UserRole.ADMIN, UserRole.MANAGER)

# نقش پیش‌فرض برای کاربران جدید
DEFAULT_ROLE = UserRole.USER

__all__ = [
    "UserRole",
    "ADMIN_ROLES",
    "FULL_ACCESS_ROLES",
    "DEFAULT_ROLE",
]