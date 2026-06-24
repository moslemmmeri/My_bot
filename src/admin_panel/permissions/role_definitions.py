# my_bot_project/src/admin_panel/core/permissions/role_definitions.py
"""
تعاریف نقش‌ها و مجوزهای پنل مدیریت (Role Definitions).

این ماژول شامل کلاس‌های `AdminRole` و `RoleDefinitions` است که
نقش‌های قابل استفاده در پنل مدیریت و مجوزهای هر نقش را تعریف می‌کنند.
"""

from enum import Enum
from typing import Set, Dict, List, Optional

from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class AdminRole(str, Enum):
    """
    نقش‌های قابل استفاده در پنل مدیریت.

    هر نقش دارای مجموعه‌ای از مجوزها (Permissions) است که دسترسی
    کاربر را به بخش‌های مختلف پنل مدیریت تعیین می‌کند.

    سطوح دسترسی:
    - SUPER_ADMIN: دسترسی کامل به تمام بخش‌ها
    - MANAGER: دسترسی به مدیریت محتوا، سفارشات و کاربران (به جز تنظیمات حساس)
    - OPERATOR: دسترسی به مدیریت سفارشات، تیکت‌ها و ارسال گروهی
    """

    SUPER_ADMIN = "super_admin"
    MANAGER = "manager"
    OPERATOR = "operator"

    @classmethod
    def from_string(cls, value: str) -> Optional["AdminRole"]:
        """
        تبدیل یک رشته به نقش ادمین.

        Args:
            value: رشته نمایانگر نقش.

        Returns:
            نقش متناظر یا None در صورت عدم تطابق.
        """
        try:
            return cls(value.lower())
        except ValueError:
            return None

    def get_display_name(self) -> str:
        """دریافت نام نمایشی نقش (به فارسی)."""
        names = {
            AdminRole.SUPER_ADMIN: "مدیر کل",
            AdminRole.MANAGER: "مدیر ارشد",
            AdminRole.OPERATOR: "اپراتور",
        }
        return names.get(self, self.value)


class RoleDefinitions:
    """
    تعاریف نقش‌ها و مجوزهای پنل مدیریت.

    این کلاس با استفاده از دیکشنری داخلی، مجوزهای هر نقش را نگهداری کرده
    و امکان دریافت مجوزهای یک نقش را فراهم می‌کند.

    Attributes:
        _permissions: دیکشنری نگاشت نقش به مجموعه مجوزها.
    """

    def __init__(self) -> None:
        """
        مقداردهی اولیه تعاریف نقش‌ها.
        """
        self._permissions: Dict[AdminRole, Set[str]] = {}
        self._load_default_permissions()
        logger.info("RoleDefinitions initialized with default permissions.")

    def _load_default_permissions(self) -> None:
        """
        بارگذاری مجوزهای پیش‌فرض برای هر نقش.

        مجوزها با فرمت `{module}.{action}` تعریف می‌شوند.
        """
        # مجوزهای عمومی (برای همه نقش‌های مدیریتی)
        base_permissions = {
            "dashboard.view",
            "profile.view",
            "profile.edit",
        }

        # مجوزهای مدیریت کاربران
        user_permissions = {
            "users.view",
            "users.manage",
            "users.create",
            "users.edit",
            "users.delete",
            "users.ban",
            "users.unban",
            "users.export",
        }

        # مجوزهای مدیریت سفارشات
        order_permissions = {
            "orders.view",
            "orders.manage",
            "orders.edit",
            "orders.delete",
            "orders.export",
            "orders.status.update",
        }

        # مجوزهای مدیریت محتوا
        content_permissions = {
            "content.view",
            "content.manage",
            "content.create",
            "content.edit",
            "content.delete",
        }

        # مجوزهای مدیریت فرم‌ها
        form_permissions = {
            "forms.view",
            "forms.manage",
            "forms.create",
            "forms.edit",
            "forms.delete",
            "forms.export",
        }

        # مجوزهای ارسال گروهی
        broadcast_permissions = {
            "broadcast.view",
            "broadcast.send",
            "broadcast.schedule",
            "broadcast.cancel",
            "broadcast.export",
        }

        # مجوزهای تحلیل و آمار
        analytics_permissions = {
            "analytics.view",
            "analytics.export",
            "analytics.dashboard",
        }

        # مجوزهای تنظیمات
        settings_permissions = {
            "settings.view",
            "settings.manage",
            "settings.edit",
        }

        # مجوزهای تیکت‌ها
        ticket_permissions = {
            "tickets.view",
            "tickets.manage",
            "tickets.reply",
            "tickets.close",
            "tickets.assign",
            "tickets.export",
        }

        # مجوزهای کوپن‌ها
        coupon_permissions = {
            "coupons.view",
            "coupons.manage",
            "coupons.create",
            "coupons.edit",
            "coupons.delete",
            "coupons.export",
        }

        # مجوزهای فیچر فلاگ
        feature_permissions = {
            "features.view",
            "features.manage",
            "features.toggle",
            "features.create",
            "features.delete",
        }

        # مجوزهای تست A/B
        ab_test_permissions = {
            "ab_tests.view",
            "ab_tests.manage",
            "ab_tests.create",
            "ab_tests.edit",
            "ab_tests.delete",
            "ab_tests.export",
        }

        # مجوزهای پشتیبان
        backup_permissions = {
            "backup.view",
            "backup.create",
            "backup.restore",
            "backup.delete",
            "backup.export",
        }

        # مجوزهای سلامت سیستم
        health_permissions = {
            "health.view",
            "health.check",
        }

        # مجوزهای لاگ‌ها
        log_permissions = {
            "logs.view",
            "logs.export",
            "logs.clear",
        }

        # تعریف مجوزهای هر نقش
        self._permissions[AdminRole.SUPER_ADMIN] = (
            base_permissions |
            user_permissions |
            order_permissions |
            content_permissions |
            form_permissions |
            broadcast_permissions |
            analytics_permissions |
            settings_permissions |
            ticket_permissions |
            coupon_permissions |
            feature_permissions |
            ab_test_permissions |
            backup_permissions |
            health_permissions |
            log_permissions
        )

        self._permissions[AdminRole.MANAGER] = (
            base_permissions |
            user_permissions |
            order_permissions |
            content_permissions |
            form_permissions |
            broadcast_permissions |
            analytics_permissions |
            ticket_permissions |
            coupon_permissions |
            health_permissions |
            log_permissions
        )

        self._permissions[AdminRole.OPERATOR] = (
            base_permissions |
            order_permissions |
            broadcast_permissions |
            ticket_permissions |
            health_permissions |
            log_permissions
        )

        logger.debug(
            f"Permissions loaded: SUPER_ADMIN={len(self._permissions[AdminRole.SUPER_ADMIN])}, "
            f"MANAGER={len(self._permissions[AdminRole.MANAGER])}, "
            f"OPERATOR={len(self._permissions[AdminRole.OPERATOR])}"
        )

    def get_permissions(self, role: AdminRole) -> Set[str]:
        """
        دریافت مجوزهای یک نقش.

        Args:
            role: نقش ادمین.

        Returns:
            Set[str]: مجموعه مجوزهای نقش.

        Raises:
            ValueError: اگر نقش وجود نداشته باشد.
        """
        if role not in self._permissions:
            raise ValueError(f"نقش '{role.value}' تعریف نشده است.")
        return self._permissions[role].copy()

    def has_permission(self, role: AdminRole, permission: str) -> bool:
        """
        بررسی اینکه آیا یک نقش دارای یک مجوز خاص است.

        Args:
            role: نقش ادمین.
            permission: نام مجوز.

        Returns:
            bool: True اگر نقش مجوز را داشته باشد.
        """
        return permission in self.get_permissions(role)

    def add_permission(self, role: AdminRole, permission: str) -> None:
        """
        افزودن یک مجوز به یک نقش.

        Args:
            role: نقش ادمین.
            permission: نام مجوز.
        """
        if role not in self._permissions:
            self._permissions[role] = set()
        self._permissions[role].add(permission)
        logger.debug(f"Permission '{permission}' added to role '{role.value}'.")

    def remove_permission(self, role: AdminRole, permission: str) -> bool:
        """
        حذف یک مجوز از یک نقش.

        Args:
            role: نقش ادمین.
            permission: نام مجوز.

        Returns:
            bool: True اگر مجوز حذف شده باشد، False اگر وجود نداشته باشد.
        """
        if role in self._permissions and permission in self._permissions[role]:
            self._permissions[role].remove(permission)
            logger.debug(f"Permission '{permission}' removed from role '{role.value}'.")
            return True
        return False

    def get_all_permissions(self) -> Set[str]:
        """
        دریافت تمام مجوزهای موجود در سیستم.

        Returns:
            Set[str]: مجموعه تمام مجوزها.
        """
        all_perms = set()
        for perms in self._permissions.values():
            all_perms.update(perms)
        return all_perms

    def get_roles_with_permission(self, permission: str) -> List[AdminRole]:
        """
        دریافت لیست نقش‌هایی که یک مجوز خاص را دارند.

        Args:
            permission: نام مجوز.

        Returns:
            List[AdminRole]: لیست نقش‌ها.
        """
        roles = []
        for role, perms in self._permissions.items():
            if permission in perms:
                roles.append(role)
        return roles

    def clear_custom_permissions(self) -> None:
        """
        بازنشانی مجوزها به حالت پیش‌فرض.

        این متد مجوزهای سفارشی را حذف کرده و مجوزهای پیش‌فرض را بارگذاری می‌کند.
        """
        self._permissions.clear()
        self._load_default_permissions()
        logger.info("Permissions reset to default.")

    def get_permission_descriptions(self) -> Dict[str, str]:
        """
        دریافت توضیحات مجوزها (برای نمایش در UI).

        Returns:
            Dict[str, str]: دیکشنری نگاشت نام مجوز به توضیحات.
        """
        return {
            "dashboard.view": "مشاهده داشبورد",
            "profile.view": "مشاهده پروفایل",
            "profile.edit": "ویرایش پروفایل",
            "users.view": "مشاهده کاربران",
            "users.manage": "مدیریت کاربران",
            "users.create": "ایجاد کاربر",
            "users.edit": "ویرایش کاربر",
            "users.delete": "حذف کاربر",
            "users.ban": "مسدود کردن کاربر",
            "users.unban": "رفع مسدودیت کاربر",
            "users.export": "خروجی کاربران",
            "orders.view": "مشاهده سفارشات",
            "orders.manage": "مدیریت سفارشات",
            "orders.edit": "ویرایش سفارش",
            "orders.delete": "حذف سفارش",
            "orders.export": "خروجی سفارشات",
            "orders.status.update": "به‌روزرسانی وضعیت سفارش",
            "content.view": "مشاهده محتوا",
            "content.manage": "مدیریت محتوا",
            "content.create": "ایجاد محتوا",
            "content.edit": "ویرایش محتوا",
            "content.delete": "حذف محتوا",
            "forms.view": "مشاهده فرم‌ها",
            "forms.manage": "مدیریت فرم‌ها",
            "forms.create": "ایجاد فرم",
            "forms.edit": "ویرایش فرم",
            "forms.delete": "حذف فرم",
            "forms.export": "خروجی فرم‌ها",
            "broadcast.view": "مشاهده ارسال‌های گروهی",
            "broadcast.send": "ارسال گروهی",
            "broadcast.schedule": "زمان‌بندی ارسال گروهی",
            "broadcast.cancel": "لغو ارسال گروهی",
            "broadcast.export": "خروجی ارسال‌های گروهی",
            "analytics.view": "مشاهده آمار",
            "analytics.export": "خروجی آمار",
            "analytics.dashboard": "داشبورد تحلیلی",
            "settings.view": "مشاهده تنظیمات",
            "settings.manage": "مدیریت تنظیمات",
            "settings.edit": "ویرایش تنظیمات",
            "tickets.view": "مشاهده تیکت‌ها",
            "tickets.manage": "مدیریت تیکت‌ها",
            "tickets.reply": "پاسخ به تیکت",
            "tickets.close": "بستن تیکت",
            "tickets.assign": "تخصیص تیکت",
            "tickets.export": "خروجی تیکت‌ها",
            "coupons.view": "مشاهده کوپن‌ها",
            "coupons.manage": "مدیریت کوپن‌ها",
            "coupons.create": "ایجاد کوپن",
            "coupons.edit": "ویرایش کوپن",
            "coupons.delete": "حذف کوپن",
            "coupons.export": "خروجی کوپن‌ها",
            "features.view": "مشاهده فیچرها",
            "features.manage": "مدیریت فیچرها",
            "features.toggle": "تغییر وضعیت فیچر",
            "features.create": "ایجاد فیچر",
            "features.delete": "حذف فیچر",
            "ab_tests.view": "مشاهده تست‌های A/B",
            "ab_tests.manage": "مدیریت تست‌های A/B",
            "ab_tests.create": "ایجاد تست A/B",
            "ab_tests.edit": "ویرایش تست A/B",
            "ab_tests.delete": "حذف تست A/B",
            "ab_tests.export": "خروجی تست‌های A/B",
            "backup.view": "مشاهده پشتیبان‌ها",
            "backup.create": "ایجاد پشتیبان",
            "backup.restore": "بازیابی پشتیبان",
            "backup.delete": "حذف پشتیبان",
            "backup.export": "خروجی پشتیبان",
            "health.view": "مشاهده سلامت سیستم",
            "health.check": "بررسی سلامت سیستم",
            "logs.view": "مشاهده لاگ‌ها",
            "logs.export": "خروجی لاگ‌ها",
            "logs.clear": "پاک کردن لاگ‌ها",
        }