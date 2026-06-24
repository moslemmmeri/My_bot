# my_bot_project/src/my_bot/shared/decorators/feature_flag.py
"""
دکوراتور فیچر فلاگ (Feature Flag Decorator).

این دکوراتور با استفاده از FeatureFlagManager، وضعیت فعال بودن یک فیچر را
قبل از اجرای تابع بررسی می‌کند و در صورت غیرفعال بودن، از ادامهٔ اجرا جلوگیری می‌کند.
از این دکوراتور برای کنترل دسترسی به ویژگی‌های جدید و آزمایشی استفاده می‌شود.
"""

import asyncio
import functools
from typing import (
    Callable, Optional, Any, Union, TypeVar, ParamSpec,
    Dict, Awaitable
)

from my_bot.core.exceptions.feature_errors import FeatureDisabledError
from my_bot.core.feature_flags.flag_manager import FeatureFlagManager
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")

# ==========================================
# نمونه سراسری FeatureFlagManager (اختیاری)
# ==========================================

_global_flag_manager: Optional[FeatureFlagManager] = None


def set_global_flag_manager(manager: FeatureFlagManager) -> None:
    """
    تنظیم نمونه سراسری FeatureFlagManager برای استفاده در دکوراتورها.

    Args:
        manager: نمونه FeatureFlagManager.
    """
    global _global_flag_manager
    _global_flag_manager = manager
    logger.info("Global FeatureFlagManager set.")


def get_global_flag_manager() -> Optional[FeatureFlagManager]:
    """
    دریافت نمونه سراسری FeatureFlagManager.

    Returns:
        Optional[FeatureFlagManager]: نمونه سراسری یا None در صورت عدم تنظیم.
    """
    return _global_flag_manager


# ==========================================
# دکوراتور اصلی
# ==========================================

def feature_flag(
    feature_name: Optional[str] = None,
    identifier_func: Optional[Callable[..., Optional[int]]] = None,
    raise_exception: bool = True,
    default_value: bool = False,
    flag_manager: Optional[FeatureFlagManager] = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    دکوراتور برای بررسی فعال بودن یک فیچر قبل از اجرای تابع.

    Args:
        feature_name: نام فیچر (در صورت None، باید از طریق تابع شناسه یا context استخراج شود).
        identifier_func: تابعی که شناسه کاربر (user_id) را از آرگومان‌های تابع استخراج می‌کند.
                         در صورت None، بررسی فیچر بدون شناسه کاربر انجام می‌شود.
        raise_exception: در صورت غیرفعال بودن فیچر، استثنا پرتاب شود (پیش‌فرض True).
        default_value: مقدار پیش‌فرض در صورت عدم وجود فیچر (پیش‌فرض False).
        flag_manager: نمونه FeatureFlagManager (در صورت None، از نمونه سراسری استفاده می‌شود).

    Returns:
        Callable: دکوراتور.

    Example:
        @feature_flag(feature_name="new_feature")
        async def new_feature_handler(message: Message) -> None:
            ...

        @feature_flag(
            feature_name="user_dashboard",
            identifier_func=lambda *args, **kwargs: args[0].id if args else None
        )
        async def user_dashboard(user: User) -> None:
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        is_async = asyncio.iscoroutinefunction(func)

        # تابع پیش‌فرض برای استخراج شناسه کاربر (در صورت نیاز)
        def default_identifier(*args: Any, **kwargs: Any) -> Optional[int]:
            # سعی می‌کنیم اولین آرگومان عددی را به‌عنوان شناسه کاربر بگیریم
            for arg in args:
                if isinstance(arg, int) and arg > 0:
                    return arg
                # اگر آرگومان دارای attribute 'id' باشد
                if hasattr(arg, "id") and isinstance(arg.id, int) and arg.id > 0:
                    return arg.id
            return None

        identifier = identifier_func or default_identifier
        manager = flag_manager or _global_flag_manager

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            """Wrapper برای توابع همزمان."""
            if manager is None:
                logger.warning("FeatureFlagManager not available. Allowing execution.")
                return func(*args, **kwargs)

            # استخراج نام فیچر (از پارامتر یا از context)
            feat_name = feature_name
            if feat_name is None:
                # تلاش برای استخراج از context (مثلاً از kwargs)
                feat_name = kwargs.get("feature_name")
                if feat_name is None:
                    raise ValueError(
                        "Feature name must be provided either as argument "
                        "to decorator or in kwargs as 'feature_name'"
                    )

            # استخراج شناسه کاربر (در صورت وجود تابع شناسه)
            user_id = None
            if identifier:
                try:
                    user_id = identifier(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Error extracting user_id: {e}")

            # بررسی فعال بودن فیچر
            try:
                # برای همزمان: اگر manager.is_enabled async است، باید از حلقه استفاده کنیم
                # اما بهتر است توابع همزمان با یک پیاده‌سازی دیگر پشتیبانی شوند
                # برای سادگی، فرض می‌کنیم توابع async هستند
                raise RuntimeError(
                    "feature_flag decorator on synchronous functions is not fully supported. "
                    "Please use async functions."
                )
            except FeatureDisabledError:
                if raise_exception:
                    raise
                else:
                    # اگر پرتاب استثنا غیرفعال باشد، مقدار پیش‌فرض را برمی‌گردانیم
                    if default_value is None:
                        # اما اگر هیچ مقداری تعیین نشده، بهتر است استثنا پرتاب شود
                        raise FeatureDisabledError(
                            feature_name=feat_name,
                            reason="Feature is disabled and default_value is None",
                        )
                    return default_value  # type: ignore

            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            """Wrapper برای توابع غیرهمزمان."""
            if manager is None:
                logger.warning("FeatureFlagManager not available. Allowing execution.")
                return await func(*args, **kwargs)

            # استخراج نام فیچر
            feat_name = feature_name
            if feat_name is None:
                feat_name = kwargs.get("feature_name")
                if feat_name is None:
                    # بررسی در args (اگر اولین آرگومان رشته باشد)
                    if args and isinstance(args[0], str):
                        feat_name = args[0]
                        # حذف آرگومان اول از args (زیرا نام فیچر است)
                        # اما این کار ممکن است باعث تغییر در امضای تابع شود
                        # بهتر است از kwargs استفاده کنیم
                    else:
                        raise ValueError(
                            "Feature name must be provided either as argument "
                            "to decorator or in kwargs as 'feature_name'"
                        )

            # استخراج شناسه کاربر
            user_id = None
            if identifier:
                try:
                    user_id = identifier(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Error extracting user_id for feature '{feat_name}': {e}")

            try:
                # بررسی فعال بودن فیچر
                is_enabled = await manager.is_enabled(feat_name, user_id)

                if not is_enabled:
                    logger.debug(
                        f"Feature '{feat_name}' is disabled for user {user_id or 'unknown'}"
                    )
                    raise FeatureDisabledError(
                        feature_name=feat_name,
                        reason="Feature is disabled",
                    )

            except FeatureDisabledError:
                if raise_exception:
                    raise
                else:
                    # اگر پرتاب استثنا غیرفعال باشد، مقدار پیش‌فرض را برمی‌گردانیم
                    logger.debug(
                        f"Feature '{feat_name}' is disabled, returning default value"
                    )
                    if default_value is None:
                        # اگر مقدار پیش‌فرض تعیین نشده، استثنا پرتاب می‌کنیم
                        raise FeatureDisabledError(
                            feature_name=feat_name,
                            reason="Feature is disabled and default_value is None",
                        )
                    return default_value  # type: ignore

            except Exception as e:
                logger.error(f"Error checking feature flag '{feat_name}': {e}")
                # در صورت بروز خطا در بررسی، اجازه اجرا داده می‌شود (یا مقدار پیش‌فرض برگردانده می‌شود)
                if default_value is not None:
                    return default_value  # type: ignore
                # در غیر این صورت، استثنا را propagate می‌کنیم
                raise

            # اجرای تابع اصلی
            return await func(*args, **kwargs)

        return async_wrapper if is_async else sync_wrapper

    return decorator


# ==========================================
# دکوراتورهای از پیش پیکربندی‌شده
# ==========================================

def feature_enabled(feature_name: str) -> Callable:
    """
    دکوراتور ساده برای بررسی فعال بودن یک فیچر.

    اگر فیچر غیرفعال باشد، استثنا FeatureDisabledError پرتاب می‌شود.

    Args:
        feature_name: نام فیچر.

    Returns:
        Callable: دکوراتور.
    """
    return feature_flag(
        feature_name=feature_name,
        raise_exception=True,
    )


def feature_with_fallback(
    feature_name: str,
    fallback_value: Any = None,
) -> Callable:
    """
    دکوراتور برای بررسی فیچر با مقدار بازگشتی پیش‌فرض.

    اگر فیچر غیرفعال باشد، تابع اصلی اجرا نمی‌شود و مقدار fallback_value برگردانده می‌شود.

    Args:
        feature_name: نام فیچر.
        fallback_value: مقدار بازگشتی در صورت غیرفعال بودن فیچر.

    Returns:
        Callable: دکوراتور.
    """
    return feature_flag(
        feature_name=feature_name,
        raise_exception=False,
        default_value=fallback_value,
    )


def feature_for_user(
    feature_name: str,
    identifier_func: Callable[..., Optional[int]],
) -> Callable:
    """
    دکوراتور برای بررسی فیچر به‌صورت اختصاصی برای یک کاربر.

    Args:
        feature_name: نام فیچر.
        identifier_func: تابع استخراج شناسه کاربر.

    Returns:
        Callable: دکوراتور.
    """
    return feature_flag(
        feature_name=feature_name,
        identifier_func=identifier_func,
        raise_exception=True,
    )


# ==========================================
# تابع کمکی برای بررسی مستقیم فیچر
# ==========================================

async def check_feature(
    feature_name: str,
    user_id: Optional[int] = None,
    flag_manager: Optional[FeatureFlagManager] = None,
    default_value: bool = False,
) -> bool:
    """
    تابع کمکی برای بررسی مستقیم فعال بودن یک فیچر.

    Args:
        feature_name: نام فیچر.
        user_id: شناسه کاربر (اختیاری).
        flag_manager: نمونه FeatureFlagManager (اختیاری).
        default_value: مقدار پیش‌فرض در صورت عدم وجود فیچر (پیش‌فرض False).

    Returns:
        bool: True اگر فیچر فعال باشد، در غیر این صورت False.
    """
    manager = flag_manager or _global_flag_manager

    if manager is None:
        logger.warning("FeatureFlagManager not available. Returning default value.")
        return default_value

    try:
        return await manager.is_enabled(feature_name, user_id)
    except Exception as e:
        logger.error(f"Error checking feature '{feature_name}': {e}")
        return default_value


async def require_feature(
    feature_name: str,
    user_id: Optional[int] = None,
    flag_manager: Optional[FeatureFlagManager] = None,
) -> None:
    """
    تابع کمکی برای بررسی فیچر و پرتاب استثنا در صورت غیرفعال بودن.

    Args:
        feature_name: نام فیچر.
        user_id: شناسه کاربر (اختیاری).
        flag_manager: نمونه FeatureFlagManager (اختیاری).

    Raises:
        FeatureDisabledError: در صورت غیرفعال بودن فیچر.
    """
    manager = flag_manager or _global_flag_manager

    if manager is None:
        logger.warning("FeatureFlagManager not available. Allowing execution.")
        return

    try:
        if not await manager.is_enabled(feature_name, user_id):
            raise FeatureDisabledError(
                feature_name=feature_name,
                reason="Feature is disabled",
            )
    except Exception as e:
        logger.error(f"Error checking feature '{feature_name}': {e}")
        raise FeatureDisabledError(
            feature_name=feature_name,
            reason=f"Error checking feature: {str(e)}",
        )