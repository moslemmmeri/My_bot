# my_bot_project/src/my_bot/presentation/middlewares/feature_flag_middleware.py
"""
میدلور فیچر فلاگ (Feature Flag Middleware).

این میدلور مسئولیت بررسی وضعیت فیچر فلاگ‌ها را قبل از پردازش درخواست‌ها
بر عهده دارد و در صورت غیرفعال بودن یک ویژگی، از ادامه پردازش جلوگیری می‌کند.
"""

from typing import Dict, Any, Optional, Callable, Awaitable, Union

from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery, User

from my_bot.core.feature_flags.flag_manager import FeatureFlagManager
from my_bot.core.exceptions.feature_errors import FeatureDisabledError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_to_main_button

logger = get_logger(__name__)


class FeatureFlagMiddleware(BaseMiddleware):
    """
    میدلور فیچر فلاگ برای بررسی فعال بودن ویژگی‌ها.

    این میدلور با استفاده از FeatureFlagManager، وضعیت فیچر فلاگ‌ها را
    قبل از پردازش درخواست بررسی می‌کند و در صورت غیرفعال بودن،
    پیام مناسب به کاربر نمایش می‌دهد.

    Attributes:
        flag_manager: مدیر فیچر فلاگ‌ها.
        default_feature: نام فیچر پیش‌فرض برای بررسی (در صورت عدم مشخص شدن).
    """

    def __init__(
        self,
        flag_manager: FeatureFlagManager,
        default_feature: Optional[str] = None,
    ) -> None:
        """
        مقداردهی اولیه میدلور.

        Args:
            flag_manager: مدیر فیچر فلاگ‌ها.
            default_feature: نام فیچر پیش‌فرض (اختیاری).
        """
        super().__init__()
        self._flag_manager = flag_manager
        self._default_feature = default_feature

        logger.info(
            f"FeatureFlagMiddleware initialized: default_feature={default_feature}"
        )

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        """
        پردازش ورودی و بررسی فیچر فلاگ.

        Args:
            handler: هندلر بعدی در زنجیره.
            event: رویداد دریافتی از تلگرام.
            data: داده‌های زمینه (Context Data).

        Returns:
            Any: نتیجه پردازش توسط هندلر بعدی.

        Raises:
            FeatureDisabledError: در صورت غیرفعال بودن فیچر.
        """
        # استخراج نام فیچر از context (در صورت وجود)
        feature_name = data.get("feature_name") or self._default_feature

        # اگر فیچر مشخص نشده باشد، ادامه پردازش
        if not feature_name:
            return await handler(event, data)

        try:
            # بررسی فعال بودن فیچر
            user = self._get_user_from_event(event)
            user_id = user.id if user else None

            if not await self._flag_manager.is_enabled(feature_name, user_id):
                # فیچر غیرفعال است
                await self._handle_disabled_feature(event, feature_name)
                raise FeatureDisabledError(
                    feature_name=feature_name,
                    reason="Feature is disabled",
                )

        except FeatureDisabledError:
            # propagate به بالا
            raise

        except Exception as e:
            logger.error(f"Error checking feature flag '{feature_name}': {e}")
            # در صورت بروز خطا در بررسی، اجازه پردازش داده می‌شود
            # (چون خطا ممکن است موقتی باشد)

        # ادامه پردازش
        return await handler(event, data)

    async def _handle_disabled_feature(
        self,
        event: Update,
        feature_name: str,
    ) -> None:
        """
        مدیریت زمانی که فیچر غیرفعال است.

        Args:
            event: رویداد دریافتی.
            feature_name: نام فیچر غیرفعال.
        """
        logger.info(f"Feature '{feature_name}' is disabled. Blocking request.")

        # ارسال پاسخ به کاربر (در صورت امکان)
        if event.message:
            await event.message.answer(
                f"⚠️ **ویژگی '{feature_name}' در حال حاضر غیرفعال است.**\n\n"
                "این ویژگی به‌زودی در دسترس قرار خواهد گرفت.",
                reply_markup=get_back_to_main_button(),
                parse_mode="Markdown",
            )
        elif event.callback_query:
            await event.callback_query.answer(
                f"⚠️ ویژگی '{feature_name}' غیرفعال است.",
                show_alert=True,
            )
            if event.callback_query.message:
                await event.callback_query.message.edit_text(
                    f"⚠️ **ویژگی '{feature_name}' در حال حاضر غیرفعال است.**\n\n"
                    "این ویژگی به‌زودی در دسترس قرار خواهد گرفت.",
                    reply_markup=get_back_to_main_button(),
                    parse_mode="Markdown",
                )

    def _get_user_from_event(self, event: Update) -> Optional[User]:
        """
        استخراج کاربر از رویداد.

        Args:
            event: رویداد دریافتی.

        Returns:
            Optional[User]: کاربر یا None در صورت عدم وجود.
        """
        if event.message and event.message.from_user:
            return event.message.from_user
        if event.callback_query and event.callback_query.from_user:
            return event.callback_query.from_user
        if event.inline_query and event.inline_query.from_user:
            return event.inline_query.from_user
        if event.chosen_inline_result and event.chosen_inline_result.from_user:
            return event.chosen_inline_result.from_user
        return None

    def set_default_feature(self, feature_name: str) -> None:
        """
        تنظیم فیچر پیش‌فرض.

        Args:
            feature_name: نام فیچر.
        """
        self._default_feature = feature_name
        logger.debug(f"Default feature set to: {feature_name}")

    async def check_feature_for_callback(
        self,
        callback: CallbackQuery,
        feature_name: str,
    ) -> bool:
        """
        بررسی فعال بودن فیچر برای یک کالبک خاص.

        Args:
            callback: کالبک دریافتی.
            feature_name: نام فیچر.

        Returns:
            bool: True اگر فیچر فعال باشد.

        Raises:
            FeatureDisabledError: در صورت غیرفعال بودن فیچر.
        """
        user_id = callback.from_user.id

        if await self._flag_manager.is_enabled(feature_name, user_id):
            return True

        # فیچر غیرفعال است
        await self._handle_disabled_feature(callback, feature_name)
        raise FeatureDisabledError(
            feature_name=feature_name,
            reason="Feature is disabled",
        )

    async def check_feature_for_message(
        self,
        message: Message,
        feature_name: str,
    ) -> bool:
        """
        بررسی فعال بودن فیچر برای یک پیام خاص.

        Args:
            message: پیام دریافتی.
            feature_name: نام فیچر.

        Returns:
            bool: True اگر فیچر فعال باشد.

        Raises:
            FeatureDisabledError: در صورت غیرفعال بودن فیچر.
        """
        user_id = message.from_user.id if message.from_user else None

        if await self._flag_manager.is_enabled(feature_name, user_id):
            return True

        # فیچر غیرفعال است
        await self._handle_disabled_feature(message, feature_name)
        raise FeatureDisabledError(
            feature_name=feature_name,
            reason="Feature is disabled",
        )

    async def get_feature_status(
        self,
        feature_name: str,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        دریافت وضعیت یک فیچر.

        Args:
            feature_name: نام فیچر.
            user_id: شناسه کاربر (اختیاری).

        Returns:
            Dict[str, Any]: وضعیت فیچر.
        """
        is_enabled = await self._flag_manager.is_enabled(feature_name, user_id)
        flag = await self._flag_manager.get_feature(feature_name)

        return {
            "feature_name": feature_name,
            "is_enabled": is_enabled,
            "details": flag,
        }

    async def get_all_features_status(
        self,
        user_id: Optional[int] = None,
    ) -> Dict[str, bool]:
        """
        دریافت وضعیت تمام فیچرها.

        Args:
            user_id: شناسه کاربر (اختیاری).

        Returns:
            Dict[str, bool]: دیکشنری نام فیچر به وضعیت.
        """
        all_flags = await self._flag_manager.list_all()
        result = {}

        for name in all_flags.keys():
            result[name] = await self._flag_manager.is_enabled(name, user_id)

        return result


# ----------------------------------------------
# دکوراتور برای بررسی فیچر در هندلرها
# ----------------------------------------------

def feature_required(feature_name: str):
    """
    دکوراتور برای مشخص کردن فیچر مورد نیاز یک هندلر.

    Args:
        feature_name: نام فیچر مورد نیاز.

    Returns:
        Callable: دکوراتور.
    """
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            # دریافت middleware از context
            # اینجا باید middleware را از طریق دی‌آی دریافت کرد
            # برای سادگی، فرض می‌کنیم که در دسترس است
            # در عمل، این دکوراتور باید با سیستم DI یا Aiogram FSM کار کند
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator