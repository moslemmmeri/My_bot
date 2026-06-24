# my_bot_project/src/my_bot/audit/audit_middleware.py
"""
میدلور حسابرسی (Audit Middleware).

این ماژول شامل کلاس `AuditMiddleware` است که به‌عنوان میدلور در
پردازش درخواست‌ها عمل کرده و رویدادهای مربوط به ورود کاربران،
دسترسی به منابع و تغییرات داده‌ها را به‌صورت خودکار ثبت می‌کند.
"""

import time
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime

from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery, User

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.domain.entities.audit_log import AuditAction, AuditStatus
from my_bot.audit.audit_logger import AuditLogger

logger = get_logger(__name__)


class AuditMiddleware(BaseMiddleware):
    """
    میدلور حسابرسی برای ثبت خودکار رویدادها.

    این میدلور با استفاده از AuditLogger، رویدادهای مربوط به ورود کاربران،
    دسترسی به منابع و تغییرات داده‌ها را به‌صورت خودکار ثبت می‌کند.

    Attributes:
        audit_logger: ثبت‌کننده لاگ‌های حسابرسی.
        log_requests: ثبت درخواست‌ها (پیش‌فرض True).
        log_errors: ثبت خطاها (پیش‌فرض True).
        enabled: فعال بودن میدلور (پیش‌فرض True).
        _excluded_actions: لیست عملیات‌های مستثنی از ثبت (اختیاری).
    """

    def __init__(
        self,
        audit_logger: AuditLogger,
        log_requests: bool = True,
        log_errors: bool = True,
        enabled: bool = True,
        excluded_actions: Optional[list[str]] = None,
    ) -> None:
        """
        مقداردهی اولیه میدلور حسابرسی.

        Args:
            audit_logger: ثبت‌کننده لاگ‌های حسابرسی.
            log_requests: ثبت درخواست‌ها (پیش‌فرض True).
            log_errors: ثبت خطاها (پیش‌فرض True).
            enabled: فعال بودن میدلور (پیش‌فرض True).
            excluded_actions: لیست عملیات‌های مستثنی از ثبت (اختیاری).
        """
        super().__init__()
        self._audit_logger = audit_logger
        self._log_requests = log_requests
        self._log_errors = log_errors
        self._enabled = enabled
        self._excluded_actions = excluded_actions or []

        logger.info(
            f"AuditMiddleware initialized: log_requests={log_requests}, "
            f"log_errors={log_errors}, enabled={enabled}"
        )

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        """
        پردازش ورودی و ثبت رویداد حسابرسی.

        Args:
            handler: هندلر بعدی در زنجیره.
            event: رویداد دریافتی از تلگرام.
            data: داده‌های زمینه (Context Data).

        Returns:
            Any: نتیجه پردازش توسط هندلر بعدی.
        """
        if not self._enabled:
            return await handler(event, data)

        # استخراج اطلاعات رویداد
        user = self._get_user_from_event(event)
        event_type = self._get_event_type(event)
        callback_data = self._get_callback_data(event)

        # بررسی مستثنی بودن عملیات
        if callback_data and any(cb in callback_data for cb in self._excluded_actions):
            return await handler(event, data)

        start_time = time.time()
        start_dt = datetime.now()

        try:
            # ثبت ورودی (در صورت فعال بودن)
            if self._log_requests:
                await self._log_request_start(user, event_type, callback_data)

            # پردازش توسط هندلر بعدی
            result = await handler(event, data)

            # ثبت خروجی موفق
            if self._log_requests:
                duration_ms = int((time.time() - start_time) * 1000)
                await self._log_request_end(user, event_type, callback_data, duration_ms, success=True)

            return result

        except Exception as e:
            # ثبت خطا
            if self._log_errors:
                duration_ms = int((time.time() - start_time) * 1000)
                await self._log_request_end(
                    user=user,
                    event_type=event_type,
                    callback_data=callback_data,
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e),
                )

            # propagate خطا به بالا
            raise

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

    def _get_event_type(self, event: Update) -> str:
        """
        دریافت نوع رویداد.

        Args:
            event: رویداد دریافتی.

        Returns:
            str: نوع رویداد.
        """
        if event.message:
            return "message"
        if event.callback_query:
            return "callback_query"
        if event.inline_query:
            return "inline_query"
        if event.chosen_inline_result:
            return "chosen_inline_result"
        if event.shipping_query:
            return "shipping_query"
        if event.pre_checkout_query:
            return "pre_checkout_query"
        return "unknown"

    def _get_callback_data(self, event: Update) -> Optional[str]:
        """
        دریافت داده‌های کالبک (در صورت وجود).

        Args:
            event: رویداد دریافتی.

        Returns:
            Optional[str]: داده‌های کالبک یا None.
        """
        if event.callback_query and event.callback_query.data:
            return event.callback_query.data
        if event.message and event.message.text:
            return event.message.text[:100]  # محدود کردن طول
        return None

    async def _log_request_start(
        self,
        user: Optional[User],
        event_type: str,
        callback_data: Optional[str],
    ) -> None:
        """
        ثبت شروع درخواست.

        Args:
            user: کاربر (اختیاری).
            event_type: نوع رویداد.
            callback_data: داده‌های کالبک (اختیاری).
        """
        if not user:
            return

        try:
            # تشخیص نوع عملیات بر اساس کالبک
            action = self._detect_action(callback_data or event_type)
            entity_type = self._detect_entity_type(callback_data or event_type)

            await self._audit_logger.log_event(
                action=action,
                entity_type=entity_type,
                user_id=user.id,
                username=user.username,
                message=f"شروع {event_type}: {callback_data[:50] if callback_data else 'بدون داده'}",
                status=AuditStatus.PENDING,
            )
        except Exception as e:
            logger.error(f"Error logging request start: {e}")

    async def _log_request_end(
        self,
        user: Optional[User],
        event_type: str,
        callback_data: Optional[str],
        duration_ms: int,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        ثبت پایان درخواست.

        Args:
            user: کاربر (اختیاری).
            event_type: نوع رویداد.
            callback_data: داده‌های کالبک (اختیاری).
            duration_ms: مدت زمان بر حسب میلی‌ثانیه.
            success: آیا عملیات موفق بوده.
            error: پیام خطا (در صورت وجود).
        """
        if not user:
            return

        try:
            action = self._detect_action(callback_data or event_type)
            entity_type = self._detect_entity_type(callback_data or event_type)
            status = AuditStatus.SUCCESS if success else AuditStatus.FAILED

            message = f"پایان {event_type}"
            if callback_data:
                message += f": {callback_data[:50]}"
            if error:
                message += f" - خطا: {error[:100]}"

            await self._audit_logger.log_event(
                action=action,
                entity_type=entity_type,
                user_id=user.id,
                username=user.username,
                status=status,
                message=message,
                duration_ms=duration_ms,
                metadata={"success": success, "error": error} if error else {"success": success},
            )
        except Exception as e:
            logger.error(f"Error logging request end: {e}")

    def _detect_action(self, data: str) -> AuditAction:
        """
        تشخیص نوع عملیات از روی داده‌ها.

        Args:
            data: داده‌های کالبک یا متن.

        Returns:
            AuditAction: نوع عملیات تشخیص‌داده‌شده.
        """
        data_lower = data.lower()

        # تشخیص بر اساس کلمات کلیدی
        if "login" in data_lower or "ورود" in data_lower:
            return AuditAction.LOGIN
        if "logout" in data_lower or "خروج" in data_lower:
            return AuditAction.LOGOUT
        if "register" in data_lower or "ثبت" in data_lower:
            return AuditAction.REGISTER
        if "delete" in data_lower or "حذف" in data_lower:
            return AuditAction.DELETE
        if "update" in data_lower or "ویرایش" in data_lower or "به‌روزرسانی" in data_lower:
            return AuditAction.UPDATE
        if "create" in data_lower or "ایجاد" in data_lower:
            return AuditAction.CREATE
        if "payment" in data_lower or "پرداخت" in data_lower:
            return AuditAction.PAYMENT
        if "refund" in data_lower or "بازگشت" in data_lower:
            return AuditAction.REFUND
        if "broadcast" in data_lower or "ارسال گروهی" in data_lower:
            return AuditAction.BROADCAST
        if "export" in data_lower or "خروجی" in data_lower:
            return AuditAction.EXPORT
        if "import" in data_lower or "واردات" in data_lower:
            return AuditAction.IMPORT
        if "backup" in data_lower or "پشتیبان" in data_lower:
            return AuditAction.BACKUP
        if "feature" in data_lower or "فیچر" in data_lower:
            return AuditAction.FEATURE
        if "approve" in data_lower or "تأیید" in data_lower:
            return AuditAction.APPROVE
        if "reject" in data_lower or "رد" in data_lower:
            return AuditAction.REJECT
        if "settings" in data_lower or "تنظیمات" in data_lower:
            return AuditAction.SETTINGS
        if "permission" in data_lower or "دسترسی" in data_lower:
            return AuditAction.PERMISSION
        if "restore" in data_lower or "بازیابی" in data_lower:
            return AuditAction.RESTORE

        # پیش‌فرض: READ
        return AuditAction.READ

    def _detect_entity_type(self, data: str) -> str:
        """
        تشخیص نوع موجودیت از روی داده‌ها.

        Args:
            data: داده‌های کالبک یا متن.

        Returns:
            str: نوع موجودیت تشخیص‌داده‌شده.
        """
        data_lower = data.lower()

        if "user" in data_lower or "کاربر" in data_lower:
            return "user"
        if "order" in data_lower or "سفارش" in data_lower:
            return "order"
        if "payment" in data_lower or "پرداخت" in data_lower:
            return "payment"
        if "form" in data_lower or "فرم" in data_lower:
            return "form"
        if "ticket" in data_lower or "تیکت" in data_lower:
            return "ticket"
        if "coupon" in data_lower or "کوپن" in data_lower:
            return "coupon"
        if "broadcast" in data_lower or "ارسال" in data_lower:
            return "broadcast"
        if "feedback" in data_lower or "بازخورد" in data_lower:
            return "feedback"
        if "abtest" in data_lower or "تست" in data_lower:
            return "ab_test"
        if "feature" in data_lower or "فیچر" in data_lower:
            return "feature_flag"
        if "backup" in data_lower or "پشتیبان" in data_lower:
            return "backup"
        if "export" in data_lower or "خروجی" in data_lower:
            return "export"
        if "import" in data_lower or "واردات" in data_lower:
            return "import"

        return "unknown"

    def enable(self) -> None:
        """فعال کردن میدلور حسابرسی."""
        self._enabled = True
        logger.info("AuditMiddleware enabled.")

    def disable(self) -> None:
        """غیرفعال کردن میدلور حسابرسی."""
        self._enabled = False
        logger.info("AuditMiddleware disabled.")

    def set_excluded_actions(self, actions: list[str]) -> None:
        """
        تنظیم لیست عملیات‌های مستثنی از ثبت.

        Args:
            actions: لیست عملیات‌های مستثنی.
        """
        self._excluded_actions = actions
        logger.info(f"Excluded actions set: {actions}")