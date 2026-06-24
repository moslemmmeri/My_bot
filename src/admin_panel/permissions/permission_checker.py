# my_bot_project/src/admin_panel/core/permissions/permission_checker.py
"""
بررسی‌کننده دسترسی‌ها (Permission Checker).

این ماژول شامل کلاس `PermissionChecker` است که مسئولیت بررسی دسترسی
کاربران به بخش‌های مختلف پنل مدیریت را بر عهده دارد. با استفاده از نقش‌های
تعریف‌شده و مجوزهای هر نقش، دسترسی کاربران را اعتبارسنجی می‌کند.
"""

from typing import Optional, List, Set, Union

from my_bot.core.constants.user_roles import UserRole
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.user import User
from admin_panel.core.permissions.role_definitions import AdminRole, RoleDefinitions

logger = get_logger(__name__)


class PermissionChecker:
    """
    بررسی‌کننده دسترسی‌های پنل مدیریت.

    این کلاس با استفاده از نقش‌های تعریف‌شده و مجوزهای هر نقش،
    دسترسی کاربران به بخش‌های مختلف پنل مدیریت را بررسی می‌کند.

    Attributes:
        role_definitions: تعاریف نقش‌ها و مجوزهای آنها.
        _permission_cache: کش مجوزهای کاربران برای افزایش سرعت.
    """

    def __init__(self, role_definitions: Optional[RoleDefinitions] = None) -> None:
        """
        مقداردهی اولیه PermissionChecker.

        Args:
            role_definitions: تعاریف نقش‌ها (در صورت None، از پیش‌فرض استفاده می‌شود).
        """
        self.role_definitions = role_definitions or RoleDefinitions()
        self._permission_cache: dict[int, Set[str]] = {}

        logger.info("PermissionChecker initialized.")

    def check_permission(
        self,
        user: User,
        permission: str,
        raise_exception: bool = True,
    ) -> bool:
        """
        بررسی دسترسی یک کاربر به یک مجوز خاص.

        Args:
            user: کاربر برای بررسی.
            permission: نام مجوز (مانند 'users.view', 'orders.edit').
            raise_exception: آیا در صورت عدم دسترسی استثنا پرتاب شود (پیش‌فرض True).

        Returns:
            bool: True اگر کاربر دسترسی داشته باشد.

        Raises:
            PermissionDeniedError: در صورت عدم دسترسی و raise_exception=True.
        """
        # اگر کاربر ادمین اصلی است، همه دسترسی‌ها را دارد
        if user.role == UserRole.ADMIN:
            return True

        # دریافت مجوزهای نقش کاربر
        user_permissions = self.get_user_permissions(user)

        # بررسی وجود مجوز
        has_permission = permission in user_permissions

        if not has_permission and raise_exception:
            raise PermissionDeniedError(
                message=f"شما دسترسی به '{permission}' را ندارید.",
                context={"user_id": user.id, "user_role": user.role.value, "permission": permission},
            )

        return has_permission

    def check_any_permission(
        self,
        user: User,
        permissions: List[str],
        raise_exception: bool = True,
    ) -> bool:
        """
        بررسی اینکه کاربر حداقل یکی از مجوزهای لیست را داشته باشد.

        Args:
            user: کاربر برای بررسی.
            permissions: لیست مجوزها.
            raise_exception: آیا در صورت عدم دسترسی استثنا پرتاب شود.

        Returns:
            bool: True اگر کاربر حداقل یکی از مجوزها را داشته باشد.

        Raises:
            PermissionDeniedError: در صورت عدم دسترسی و raise_exception=True.
        """
        # اگر کاربر ادمین اصلی است، همه دسترسی‌ها را دارد
        if user.role == UserRole.ADMIN:
            return True

        user_permissions = self.get_user_permissions(user)

        for permission in permissions:
            if permission in user_permissions:
                return True

        if raise_exception:
            raise PermissionDeniedError(
                message=f"شما به هیچ‌یک از مجوزهای مورد نیاز دسترسی ندارید.",
                context={"user_id": user.id, "user_role": user.role.value, "permissions": permissions},
            )

        return False

    def check_all_permissions(
        self,
        user: User,
        permissions: List[str],
        raise_exception: bool = True,
    ) -> bool:
        """
        بررسی اینکه کاربر تمام مجوزهای لیست را داشته باشد.

        Args:
            user: کاربر برای بررسی.
            permissions: لیست مجوزها.
            raise_exception: آیا در صورت عدم دسترسی استثنا پرتاب شود.

        Returns:
            bool: True اگر کاربر تمام مجوزها را داشته باشد.

        Raises:
            PermissionDeniedError: در صورت عدم دسترسی و raise_exception=True.
        """
        # اگر کاربر ادمین اصلی است، همه دسترسی‌ها را دارد
        if user.role == UserRole.ADMIN:
            return True

        user_permissions = self.get_user_permissions(user)

        missing = []
        for permission in permissions:
            if permission not in user_permissions:
                missing.append(permission)

        if missing:
            if raise_exception:
                raise PermissionDeniedError(
                    message=f"شما دسترسی به مجوزهای زیر را ندارید: {', '.join(missing)}",
                    context={"user_id": user.id, "user_role": user.role.value, "missing": missing},
                )
            return False

        return True

    def check_role(
        self,
        user: User,
        required_roles: Union[UserRole, List[UserRole]],
        raise_exception: bool = True,
    ) -> bool:
        """
        بررسی اینکه کاربر یکی از نقش‌های مورد نیاز را داشته باشد.

        Args:
            user: کاربر برای بررسی.
            required_roles: نقش مورد نیاز یا لیستی از نقش‌ها.
            raise_exception: آیا در صورت عدم دسترسی استثنا پرتاب شود.

        Returns:
            bool: True اگر کاربر نقش مورد نیاز را داشته باشد.

        Raises:
            PermissionDeniedError: در صورت عدم دسترسی و raise_exception=True.
        """
        if isinstance(required_roles, UserRole):
            required_roles = [required_roles]

        # اگر کاربر ادمین اصلی است و در لیست نباشد، دسترسی دارد
        if user.role == UserRole.ADMIN:
            # ادمین اصلی به همه چیز دسترسی دارد
            return True

        user_role = user.role

        # بررسی اینکه نقش کاربر در لیست باشد
        if user_role in required_roles:
            return True

        # اگر کاربر نقش بالاتری دارد (مثلاً MANAGER می‌تواند به بخش‌های OPERATOR دسترسی داشته باشد)
        # اما اینجا فقط تطابق دقیق را بررسی می‌کنیم
        # برای دسترسی سلسله‌مراتبی از متد check_permission استفاده می‌شود

        if raise_exception:
            role_names = [r.value for r in required_roles]
            raise PermissionDeniedError(
                message=f"شما به نقش‌های مورد نیاز دسترسی ندارید. نقش‌های مورد نیاز: {', '.join(role_names)}",
                context={"user_id": user.id, "user_role": user.role.value, "required_roles": role_names},
            )

        return False

    def get_user_permissions(self, user: User) -> Set[str]:
        """
        دریافت تمام مجوزهای یک کاربر.

        Args:
            user: کاربر برای دریافت مجوزها.

        Returns:
            Set[str]: مجموعه مجوزهای کاربر.

        Raises:
            ValueError: اگر نقش کاربر نامعتبر باشد.
        """
        # اگر کاربر ادمین اصلی است، همه مجوزها را دارد
        if user.role == UserRole.ADMIN:
            # دریافت همه مجوزهای موجود از تعاریف نقش‌ها
            all_permissions = set()
            for role in AdminRole:
                all_permissions.update(self.role_definitions.get_permissions(role))
            return all_permissions

        # بررسی کش
        if user.id in self._permission_cache:
            return self._permission_cache[user.id]

        # تبدیل نقش کاربر به AdminRole
        admin_role = self._user_role_to_admin_role(user.role)
        if admin_role is None:
            # اگر نقش کاربر در AdminRole تعریف نشده باشد، کاربر دسترسی ندارد
            return set()

        # دریافت مجوزها
        permissions = self.role_definitions.get_permissions(admin_role)

        # ذخیره در کش
        if user.id is not None:
            self._permission_cache[user.id] = permissions

        return permissions

    def _user_role_to_admin_role(self, user_role: UserRole) -> Optional[AdminRole]:
        """
        تبدیل نقش کاربری به نقش ادمین.

        Args:
            user_role: نقش کاربری.

        Returns:
            Optional[AdminRole]: نقش ادمین متناظر یا None.
        """
        mapping = {
            UserRole.ADMIN: AdminRole.SUPER_ADMIN,
            UserRole.MANAGER: AdminRole.MANAGER,
            UserRole.OPERATOR: AdminRole.OPERATOR,
        }
        return mapping.get(user_role)

    def clear_cache(self) -> None:
        """پاک کردن کش مجوزها."""
        self._permission_cache.clear()
        logger.debug("Permission cache cleared.")

    def get_user_role_in_admin(self, user: User) -> Optional[AdminRole]:
        """
        دریافت نقش کاربر در پنل مدیریت.

        Args:
            user: کاربر.

        Returns:
            Optional[AdminRole]: نقش کاربر در پنل مدیریت یا None.
        """
        return self._user_role_to_admin_role(user.role)

    def is_admin_user(self, user: User) -> bool:
        """
        بررسی اینکه آیا کاربر یکی از نقش‌های مدیریتی دارد.

        Args:
            user: کاربر.

        Returns:
            bool: True اگر کاربر نقش مدیریتی داشته باشد.
        """
        return self._user_role_to_admin_role(user.role) is not None

    def get_user_admin_level(self, user: User) -> int:
        """
        دریافت سطح دسترسی کاربر در پنل مدیریت (عدد بالاتر = دسترسی بیشتر).

        Args:
            user: کاربر.

        Returns:
            int: سطح دسترسی کاربر (۰ برای کاربران عادی).
        """
        admin_role = self._user_role_to_admin_role(user.role)
        if admin_role is None:
            return 0

        levels = {
            AdminRole.SUPER_ADMIN: 100,
            AdminRole.MANAGER: 80,
            AdminRole.OPERATOR: 60,
        }
        return levels.get(admin_role, 0)

    def can_manage_users(self, user: User) -> bool:
        """
        بررسی اینکه آیا کاربر مجاز به مدیریت کاربران است.

        Args:
            user: کاربر.

        Returns:
            bool: True اگر کاربر مجاز باشد.
        """
        return self.check_permission(user, "users.manage", raise_exception=False)

    def can_manage_orders(self, user: User) -> bool:
        """
        بررسی اینکه آیا کاربر مجاز به مدیریت سفارشات است.

        Args:
            user: کاربر.

        Returns:
            bool: True اگر کاربر مجاز باشد.
        """
        return self.check_permission(user, "orders.manage", raise_exception=False)

    def can_manage_content(self, user: User) -> bool:
        """
        بررسی اینکه آیا کاربر مجاز به مدیریت محتوا است.

        Args:
            user: کاربر.

        Returns:
            bool: True اگر کاربر مجاز باشد.
        """
        return self.check_permission(user, "content.manage", raise_exception=False)

    def can_manage_settings(self, user: User) -> bool:
        """
        بررسی اینکه آیا کاربر مجاز به مدیریت تنظیمات است.

        Args:
            user: کاربر.

        Returns:
            bool: True اگر کاربر مجاز باشد.
        """
        return self.check_permission(user, "settings.manage", raise_exception=False)

    def can_send_broadcast(self, user: User) -> bool:
        """
        بررسی اینکه آیا کاربر مجاز به ارسال گروهی است.

        Args:
            user: کاربر.

        Returns:
            bool: True اگر کاربر مجاز باشد.
        """
        return self.check_permission(user, "broadcast.send", raise_exception=False)

    def can_view_analytics(self, user: User) -> bool:
        """
        بررسی اینکه آیا کاربر مجاز به مشاهده آمار است.

        Args:
            user: کاربر.

        Returns:
            bool: True اگر کاربر مجاز باشد.
        """
        return self.check_permission(user, "analytics.view", raise_exception=False)

    def can_manage_tickets(self, user: User) -> bool:
        """
        بررسی اینکه آیا کاربر مجاز به مدیریت تیکت‌ها است.

        Args:
            user: کاربر.

        Returns:
            bool: True اگر کاربر مجاز باشد.
        """
        return self.check_permission(user, "tickets.manage", raise_exception=False)

    def can_manage_coupons(self, user: User) -> bool:
        """
        بررسی اینکه آیا کاربر مجاز به مدیریت کوپن‌ها است.

        Args:
            user: کاربر.

        Returns:
            bool: True اگر کاربر مجاز باشد.
        """
        return self.check_permission(user, "coupons.manage", raise_exception=False)

    def can_manage_features(self, user: User) -> bool:
        """
        بررسی اینکه آیا کاربر مجاز به مدیریت فیچر فلاگ‌ها است.

        Args:
            user: کاربر.

        Returns:
            bool: True اگر کاربر مجاز باشد.
        """
        return self.check_permission(user, "features.manage", raise_exception=False)

    def can_manage_ab_tests(self, user: User) -> bool:
        """
        بررسی اینکه آیا کاربر مجاز به مدیریت تست‌های A/B است.

        Args:
            user: کاربر.

        Returns:
            bool: True اگر کاربر مجاز باشد.
        """
        return self.check_permission(user, "ab_tests.manage", raise_exception=False)