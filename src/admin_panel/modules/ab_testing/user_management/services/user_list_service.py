# my_bot_project/src/admin_panel/modules/user_management/services/user_list_service.py
"""
سرویس لیست کاربران (User List Service).

این سرویس مسئولیت دریافت لیست کاربران با صفحه‌بندی و فیلترهای مختلف
برای نمایش در پنل مدیریت را بر عهده دارد.
"""

from typing import Optional, Dict, Any, List, Tuple
from math import ceil

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.constants.user_roles import UserRole
from my_bot.domain.entities.user import User
from my_bot.domain.interfaces.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class UserListService:
    """
    سرویس لیست کاربران.

    این کلاس با استفاده از UserRepository، کاربران را با اعمال
    فیلترها و صفحه‌بندی دریافت می‌کند.

    Attributes:
        user_repository: ریپازیتوری کاربر.
        default_limit: تعداد کاربران در هر صفحه (پیش‌فرض ۱۰).
    """

    def __init__(self, user_repository: UserRepository, default_limit: int = 10) -> None:
        """
        مقداردهی اولیه سرویس.

        Args:
            user_repository: ریپازیتوری کاربر.
            default_limit: تعداد کاربران در هر صفحه (پیش‌فرض ۱۰).
        """
        self._user_repository = user_repository
        self._default_limit = default_limit

        logger.info(f"UserListService initialized: default_limit={default_limit}")

    async def get_users_page(
        self,
        page: int = 0,
        limit: Optional[int] = None,
        filter_name: str = "all",
        search_query: Optional[str] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Dict[str, Any]:
        """
        دریافت یک صفحه از کاربران با فیلترها و مرتب‌سازی.

        Args:
            page: شماره صفحه (از ۰ شروع می‌شود).
            limit: تعداد کاربران در هر صفحه (در صورت None از default_limit استفاده می‌شود).
            filter_name: نام فیلتر ('all', 'active', 'banned', 'admin', 'manager', 'operator', 'user').
            search_query: عبارت جستجو (اختیاری).
            sort_by: نام فیلد برای مرتب‌سازی (پیش‌فرض: 'created_at').
            sort_desc: مرتب‌سازی نزولی (پیش‌فرض True).

        Returns:
            Dict[str, Any]: شامل:
                - users: لیست کاربران
                - total: تعداد کل کاربران (با فیلترها)
                - total_pages: تعداد کل صفحات
                - current_page: شماره صفحه فعلی
                - filters: فیلترهای اعمال‌شده
        """
        # اعتبارسنجی صفحه
        page = max(0, page)
        limit = limit or self._default_limit
        skip = page * limit

        # اعمال فیلترها
        filters = await self._build_filters(filter_name)

        # دریافت کاربران با فیلترها
        if search_query:
            # اگر جستجو وجود دارد، از متد search استفاده می‌کنیم
            users = await self._user_repository.search(
                query=search_query,
                skip=skip,
                limit=limit,
            )
            # برای جستجو، تعداد کل را نمی‌توانیم به‌راحتی محاسبه کنیم، پس از count با فیلترها استفاده می‌کنیم
            total = await self._user_repository.count(filters=filters)
        else:
            # دریافت کاربران با صفحه‌بندی و مرتب‌سازی
            users = await self._user_repository.get_all(
                skip=skip,
                limit=limit,
                order_by=sort_by,
                order_desc=sort_desc,
            )

            # اگر فیلتر خاصی داریم، کاربران را فیلتر می‌کنیم (چون get_all همه را می‌گیرد)
            if filters:
                filtered_users = []
                for user in users:
                    match = True
                    for key, value in filters.items():
                        if key == "role" and user.role.value != value:
                            match = False
                            break
                        elif key == "is_active" and user.is_active != value:
                            match = False
                            break
                        elif key == "is_banned" and user.is_banned != value:
                            match = False
                            break
                    if match:
                        filtered_users.append(user)
                users = filtered_users
                # برای تعداد کل، باید با فیلترها شمارش کنیم
                total = await self._user_repository.count(filters=filters)
            else:
                # تعداد کل کاربران بدون فیلتر
                total = await self._user_repository.count()

        # اگر جستجو داشتیم، تعداد کل باید از قبل محاسبه شده باشد، اما برای دقت بیشتر،
        # از متد count با فیلترها استفاده می‌کنیم (اما search ممکن است فیلترهای اضافی داشته باشد)
        # برای سادگی، اگر جستجو داشتیم، total را از count بگیریم.
        if search_query:
            # برای جستجو، نمی‌توانیم دقیقاً تعداد کل را محاسبه کنیم،
            # اما می‌توانیم با فیلترهای نقش و وضعیت، تعداد را تخمین بزنیم
            total = await self._user_repository.count(filters=filters)

        # محاسبه تعداد صفحات
        total_pages = ceil(total / limit) if total > 0 else 1

        return {
            "users": users,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "filters": {
                "filter_name": filter_name,
                "search_query": search_query,
                "sort_by": sort_by,
                "sort_desc": sort_desc,
            },
            "limit": limit,
        }

    async def _build_filters(self, filter_name: str) -> Dict[str, Any]:
        """
        ساخت دیکشنری فیلترها بر اساس نام فیلتر.

        Args:
            filter_name: نام فیلتر.

        Returns:
            Dict[str, Any]: فیلترها.
        """
        filters = {}

        if filter_name == "active":
            filters["is_active"] = True
        elif filter_name == "banned":
            filters["is_banned"] = True
        elif filter_name == "admin":
            filters["role"] = UserRole.ADMIN.value
        elif filter_name == "manager":
            filters["role"] = UserRole.MANAGER.value
        elif filter_name == "operator":
            filters["role"] = UserRole.OPERATOR.value
        elif filter_name == "user":
            filters["role"] = UserRole.USER.value
        # 'all' هیچ فیلتری اضافه نمی‌کند

        return filters

    async def get_user_count(self, filter_name: str = "all") -> int:
        """
        دریافت تعداد کاربران با فیلتر مشخص.

        Args:
            filter_name: نام فیلتر.

        Returns:
            int: تعداد کاربران.
        """
        filters = await self._build_filters(filter_name)
        return await self._user_repository.count(filters=filters)

    async def get_all_users(
        self,
        limit: int = 1000,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[User]:
        """
        دریافت تمام کاربران (برای خروجی و موارد خاص).

        Args:
            limit: حداکثر تعداد (پیش‌فرض ۱۰۰۰).
            order_by: نام فیلد مرتب‌سازی.
            order_desc: مرتب‌سازی نزولی.

        Returns:
            List[User]: لیست کاربران.
        """
        return await self._user_repository.get_all(
            skip=0,
            limit=limit,
            order_by=order_by,
            order_desc=order_desc,
        )

    def get_supported_filters(self) -> List[str]:
        """
        دریافت لیست فیلترهای پشتیبانی‌شده.

        Returns:
            List[str]: لیست نام فیلترها.
        """
        return ["all", "active", "banned", "admin", "manager", "operator", "user"]