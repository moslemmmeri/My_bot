# my_bot_project/src/my_bot/core/feature_flags/flag_manager.py
"""
مدیریت Feature Flags با پشتیبانی از کش و ذخیره‌سازی.

این ماژول شامل کلاس `FeatureFlagManager` است که به‌عنوان نقطه‌ی مرکزی
برای مدیریت ویژگی‌های فعال/غیرفعال در سیستم عمل می‌کند.
"""

from typing import Dict, List, Optional, Set

from my_bot.core.exceptions.feature_errors import (
    FeatureDisabledError,
    FeatureNotFoundError,
    FeatureToggleError,
    FeatureDependencyError,
    FeatureValidationError,
    FeatureLimitExceededError,
    FeatureExpiredError,
)
from my_bot.core.feature_flags.flag_cache import FlagCache
from my_bot.core.feature_flags.flag_repository import FlagRepository
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class FeatureFlagManager:
    """
    مدیریت مرکزی Feature Flags.

    این کلاس با استفاده از یک ریپازیتوری برای ذخیره‌سازی دائمی و یک کش
    برای افزایش سرعت، وضعیت ویژگی‌ها را مدیریت می‌کند.

    Attributes:
        repository: ریپازیتوری برای ذخیره‌سازی و بازیابی ویژگی‌ها.
        cache: کش اختیاری برای افزایش سرعت دسترسی.
        _dependency_graph: گراف وابستگی‌های بین ویژگی‌ها (اختیاری).
    """

    def __init__(
        self,
        repository: FlagRepository,
        cache: Optional[FlagCache] = None,
        dependencies: Optional[Dict[str, Set[str]]] = None,
    ) -> None:
        """
        مقداردهی اولیه مدیر ویژگی‌ها.

        Args:
            repository: ریپازیتوری برای ذخیره‌سازی دائمی.
            cache: کش اختیاری برای افزایش سرعت.
            dependencies: گراف وابستگی‌ها به صورت دیکشنری (نام ویژگی -> مجموعه‌ای از وابستگی‌ها).
        """
        self.repository = repository
        self.cache = cache
        self._dependency_graph = dependencies or {}
        self._initialized = False

    async def initialize(self) -> None:
        """بارگذاری اولیهٔ ویژگی‌ها از دیتابیس به کش."""
        if self._initialized:
            return

        try:
            # بارگذاری تمام ویژگی‌ها از ریپازیتوری
            all_flags = await self.repository.get_all()
            if self.cache:
                for name, flag in all_flags.items():
                    await self.cache.set(name, flag)
            logger.info(f"Feature flags initialized: {len(all_flags)} features loaded.")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize feature flags: {e}")
            raise

    async def is_enabled(self, feature_name: str, user_id: Optional[int] = None) -> bool:
        """
        بررسی فعال بودن یک ویژگی برای یک کاربر مشخص.

        Args:
            feature_name: نام ویژگی.
            user_id: شناسه کاربر (اختیاری، برای بررسی دسترسی‌های خاص).

        Returns:
            True اگر ویژگی فعال باشد و کاربر دسترسی داشته باشد.

        Raises:
            FeatureNotFoundError: اگر ویژگی وجود نداشته باشد.
        """
        flag = await self._get_flag(feature_name)
        if flag is None:
            raise FeatureNotFoundError(feature_name)

        # بررسی وضعیت پایه
        if not flag.get("enabled", False):
            return False

        # بررسی تاریخ انقضا
        if expiry := flag.get("expires_at"):
            from datetime import datetime
            if datetime.now() > expiry:
                # در صورت انقضا، ویژگی را غیرفعال می‌کنیم
                await self.disable(feature_name, reason="Expired")
                logger.warning(f"Feature '{feature_name}' expired at {expiry}, disabled.")
                return False

        # بررسی محدودیت تعداد استفاده
        if limit := flag.get("usage_limit"):
            current = flag.get("current_usage", 0)
            if current >= limit:
                # در صورت رسیدن به حد مجاز، غیرفعال می‌کنیم
                await self.disable(feature_name, reason="Usage limit reached")
                logger.warning(f"Feature '{feature_name}' usage limit ({limit}) reached, disabled.")
                return False

        # بررسی وابستگی‌ها
        if not await self._check_dependencies(feature_name):
            return False

        # بررسی دسترسی کاربر (در صورت وجود)
        if user_id is not None:
            if not await self._check_user_access(feature_name, user_id):
                return False

        return True

    async def enable(
        self,
        feature_name: str,
        enabled_by: Optional[int] = None,
        reason: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        فعال‌سازی یک ویژگی.

        Args:
            feature_name: نام ویژگی.
            enabled_by: شناسه کاربری که فعال‌سازی را انجام داده (اختیاری).
            reason: دلیل فعال‌سازی (اختیاری).
            **kwargs: پارامترهای اضافی مانند expires_at, usage_limit, etc.

        Raises:
            FeatureNotFoundError: اگر ویژگی وجود نداشته باشد.
            FeatureDependencyError: اگر وابستگی‌ها برآورده نشوند.
            FeatureToggleError: در صورت خطا در ذخیره‌سازی.
        """
        # بررسی وجود ویژگی
        flag = await self._get_flag(feature_name)
        if flag is None:
            raise FeatureNotFoundError(feature_name)

        # بررسی وابستگی‌ها
        if not await self._check_dependencies(feature_name):
            missing = await self._get_missing_dependencies(feature_name)
            raise FeatureDependencyError(feature_name, ", ".join(missing))

        # به‌روزرسانی وضعیت
        try:
            flag["enabled"] = True
            if reason:
                flag["enable_reason"] = reason
            if enabled_by:
                flag["enabled_by"] = enabled_by
            # پارامترهای اضافی
            for key, value in kwargs.items():
                if key in ("expires_at", "usage_limit", "description"):
                    flag[key] = value

            await self.repository.save(feature_name, flag)
            if self.cache:
                await self.cache.set(feature_name, flag)
            logger.info(f"Feature '{feature_name}' enabled by user {enabled_by or 'system'}.")
        except Exception as e:
            raise FeatureToggleError(feature_name, "enable", str(e))

    async def disable(
        self,
        feature_name: str,
        disabled_by: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> None:
        """
        غیرفعال‌سازی یک ویژگی.

        Args:
            feature_name: نام ویژگی.
            disabled_by: شناسه کاربری که غیرفعال‌سازی را انجام داده (اختیاری).
            reason: دلیل غیرفعال‌سازی (اختیاری).

        Raises:
            FeatureNotFoundError: اگر ویژگی وجود نداشته باشد.
            FeatureToggleError: در صورت خطا در ذخیره‌سازی.
        """
        flag = await self._get_flag(feature_name)
        if flag is None:
            raise FeatureNotFoundError(feature_name)

        try:
            flag["enabled"] = False
            if reason:
                flag["disable_reason"] = reason
            if disabled_by:
                flag["disabled_by"] = disabled_by

            await self.repository.save(feature_name, flag)
            if self.cache:
                await self.cache.set(feature_name, flag)
            logger.info(f"Feature '{feature_name}' disabled by user {disabled_by or 'system'}.")
        except Exception as e:
            raise FeatureToggleError(feature_name, "disable", str(e))

    async def toggle(self, feature_name: str, user_id: Optional[int] = None) -> bool:
        """
        تغییر وضعیت یک ویژگی (فعال/غیرفعال).

        Args:
            feature_name: نام ویژگی.
            user_id: شناسه کاربر (اختیاری).

        Returns:
            وضعیت جدید (True اگر فعال شده باشد).

        Raises:
            FeatureNotFoundError: اگر ویژگی وجود نداشته باشد.
        """
        flag = await self._get_flag(feature_name)
        if flag is None:
            raise FeatureNotFoundError(feature_name)

        current = flag.get("enabled", False)
        if current:
            await self.disable(feature_name, disabled_by=user_id)
            return False
        else:
            await self.enable(feature_name, enabled_by=user_id)
            return True

    async def list_all(self) -> Dict[str, Dict]:
        """
        دریافت لیست تمام ویژگی‌ها با وضعیت آنها.

        Returns:
            دیکشنری شامل نام ویژگی‌ها و اطلاعات آنها.
        """
        return await self.repository.get_all()

    async def get_feature(self, feature_name: str) -> Optional[Dict]:
        """
        دریافت اطلاعات یک ویژگی خاص.

        Args:
            feature_name: نام ویژگی.

        Returns:
            دیکشنری اطلاعات ویژگی یا None در صورت عدم وجود.
        """
        return await self._get_flag(feature_name)

    async def add_feature(
        self,
        feature_name: str,
        enabled: bool = False,
        description: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        افزودن یک ویژگی جدید به سیستم.

        Args:
            feature_name: نام ویژگی (باید یکتا باشد).
            enabled: وضعیت اولیه (پیش‌فرض False).
            description: توضیحات ویژگی (اختیاری).
            **kwargs: پارامترهای اضافی مانند expires_at, usage_limit.

        Raises:
            FeatureValidationError: اگر نام ویژگی نامعتبر باشد یا قبلاً وجود داشته باشد.
        """
        # اعتبارسنجی نام
        if not feature_name or not feature_name.strip():
            raise FeatureValidationError(feature_name, "name", "", "نام ویژگی نمی‌تواند خالی باشد.")

        # بررسی وجود قبلی
        existing = await self.repository.get(feature_name)
        if existing is not None:
            raise FeatureValidationError(
                feature_name,
                "name",
                feature_name,
                "ویژگی با این نام قبلاً وجود دارد."
            )

        # ساخت دیکشنری ویژگی
        flag = {
            "enabled": enabled,
            "description": description or "",
            "created_at": kwargs.get("created_at"),
        }
        # اضافه کردن پارامترهای اضافی
        for key in ("expires_at", "usage_limit", "current_usage", "dependencies"):
            if key in kwargs:
                flag[key] = kwargs[key]

        try:
            await self.repository.save(feature_name, flag)
            if self.cache:
                await self.cache.set(feature_name, flag)
            logger.info(f"Feature '{feature_name}' added with enabled={enabled}.")
        except Exception as e:
            raise FeatureToggleError(feature_name, "add", str(e))

    async def remove_feature(self, feature_name: str) -> None:
        """
        حذف یک ویژگی از سیستم.

        Args:
            feature_name: نام ویژگی.

        Raises:
            FeatureNotFoundError: اگر ویژگی وجود نداشته باشد.
        """
        flag = await self._get_flag(feature_name)
        if flag is None:
            raise FeatureNotFoundError(feature_name)

        try:
            await self.repository.delete(feature_name)
            if self.cache:
                await self.cache.delete(feature_name)
            logger.info(f"Feature '{feature_name}' removed.")
        except Exception as e:
            raise FeatureToggleError(feature_name, "delete", str(e))

    async def require_enabled(self, feature_name: str, user_id: Optional[int] = None) -> None:
        """
        بررسی فعال بودن ویژگی و پرتاب استثنا در صورت غیرفعال بودن.

        Args:
            feature_name: نام ویژگی.
            user_id: شناسه کاربر (اختیاری).

        Raises:
            FeatureDisabledError: اگر ویژگی غیرفعال باشد.
        """
        if not await self.is_enabled(feature_name, user_id):
            flag = await self._get_flag(feature_name)
            reason = flag.get("disable_reason") if flag else None
            raise FeatureDisabledError(feature_name, reason)

    async def check_dependency(self, feature_name: str) -> bool:
        """
        بررسی وابستگی‌های یک ویژگی.

        Args:
            feature_name: نام ویژگی.

        Returns:
            True اگر تمام وابستگی‌ها فعال باشند.

        Raises:
            FeatureNotFoundError: اگر ویژگی وجود نداشته باشد.
            FeatureDependencyError: اگر وابستگی‌ها برآورده نشوند.
        """
        flag = await self._get_flag(feature_name)
        if flag is None:
            raise FeatureNotFoundError(feature_name)

        dependencies = flag.get("dependencies", [])
        if not dependencies:
            return True

        missing = []
        for dep in dependencies:
            if not await self.is_enabled(dep):
                missing.append(dep)

        if missing:
            raise FeatureDependencyError(feature_name, ", ".join(missing))
        return True

    async def _get_flag(self, feature_name: str) -> Optional[Dict]:
        """دریافت اطلاعات یک ویژگی از کش یا ریپازیتوری."""
        # ابتدا از کش
        if self.cache:
            flag = await self.cache.get(feature_name)
            if flag is not None:
                return flag

        # از ریپازیتوری
        flag = await self.repository.get(feature_name)
        if flag is not None and self.cache:
            await self.cache.set(feature_name, flag)
        return flag

    async def _check_dependencies(self, feature_name: str) -> bool:
        """بررسی وابستگی‌های یک ویژگی (بدون پرتاب استثنا)."""
        flag = await self._get_flag(feature_name)
        if not flag:
            return False
        dependencies = flag.get("dependencies", [])
        if not dependencies:
            return True
        for dep in dependencies:
            if not await self.is_enabled(dep):
                return False
        return True

    async def _get_missing_dependencies(self, feature_name: str) -> List[str]:
        """دریافت لیست وابستگی‌های غیرفعال یک ویژگی."""
        flag = await self._get_flag(feature_name)
        if not flag:
            return []
        dependencies = flag.get("dependencies", [])
        missing = []
        for dep in dependencies:
            if not await self.is_enabled(dep):
                missing.append(dep)
        return missing

    async def _check_user_access(self, feature_name: str, user_id: int) -> bool:
        """
        بررسی دسترسی کاربر به ویژگی (می‌تواند در کلاس‌های فرزند بازنویسی شود).

        Args:
            feature_name: نام ویژگی.
            user_id: شناسه کاربر.

        Returns:
            True اگر کاربر دسترسی داشته باشد.
        """
        # پیاده‌سازی پیش‌فرض: همه کاربران دسترسی دارند
        # در صورت نیاز، می‌توان با بررسی نقش‌ها یا لیست‌های سفید این را سفارشی‌سازی کرد
        return True

    async def refresh_cache(self) -> None:
        """به‌روزرسانی کش با آخرین داده‌های ریپازیتوری."""
        if self.cache:
            all_flags = await self.repository.get_all()
            # پاک کردن کش فعلی
            await self.cache.clear()
            # بارگذاری مجدد
            for name, flag in all_flags.items():
                await self.cache.set(name, flag)
            logger.info("Feature flags cache refreshed.")

    async def clear_cache(self) -> None:
        """پاک کردن کش (بدون تأثیر بر ریپازیتوری)."""
        if self.cache:
            await self.cache.clear()
            logger.info("Feature flags cache cleared.")