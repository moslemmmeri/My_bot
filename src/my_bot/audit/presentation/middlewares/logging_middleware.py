# my_bot_project/src/my_bot/presentation/middlewares/logging_middleware.py
"""
میدلور ثبت لاگ (Logging Middleware).

این میدلور مسئولیت ثبت لاگ تمام درخواست‌ها و پاسخ‌های دریافتی
از تلگرام را بر عهده دارد. اطلاعاتی مانند شناسه کاربر، نوع رویداد،
زمان پردازش و خطاهای احتمالی را ثبت می‌کند.
"""

import time
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery, User
from aiogram.exceptions import TelegramAPIError

from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """
    میدلور ثبت لاگ درخواست‌ها و پاسخ‌ها.

    این میدلور تمام رویدادهای دریافتی از تلگرام را لاگ می‌کند
    و اطلاعات مفیدی برای دیباگ و تحلیل فراهم می‌آورد.

    Attributes:
        log_requests: آیا درخواست‌ها لاگ شوند (پیش‌فرض True).
        log_responses: آیا پاسخ‌ها لاگ شوند (پیش‌فرض True).
        log_errors: آیا خطاها لاگ شوند (پیش‌فرض True).
        log_private: آیا پیام‌های خصوصی لاگ شوند (پیش‌فرض True).
        log_groups: آیا پیام‌های گروهی لاگ شوند (پیش‌فرض False).
    """

    def __init__(
        self,
        log_requests: bool = True,
        log_responses: bool = True,
        log_errors: bool = True,
        log_private: bool = True,
        log_groups: bool = False,
    ) -> None:
        """
        مقداردهی اولیه میدلور.

        Args:
            log_requests: آیا درخواست‌ها لاگ شوند.
            log_responses: آیا پاسخ‌ها لاگ شوند.
            log_errors: آیا خطاها لاگ شوند.
            log_private: آیا پیام‌های خصوصی لاگ شوند.
            log_groups: آیا پیام‌های گروهی لاگ شوند.
        """
        super().__init__()
        self._log_requests = log_requests
        self._log_responses = log_responses
        self._log_errors = log_errors
        self._log_private = log_private
        self._log_groups = log_groups

        logger.info(
            f"LoggingMiddleware initialized: "
            f"requests={log_requests}, responses={log_responses}, "
            f"errors={log_errors}, private={log_private}, groups={log_groups}"
        )

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        """
        پردازش ورودی و ثبت لاگ.

        Args:
            handler: هندلر بعدی در زنجیره.
            event: رویداد دریافتی از تلگرام.
            data: داده‌های زمینه (Context Data).

        Returns:
            Any: نتیجه پردازش توسط هندلر بعدی.
        """
        # استخراج اطلاعات رویداد
        event_info = self._extract_event_info(event)
        user = self._get_user_from_event(event)

        # اگر باید لاگ شود
        if self._should_log(event, user):
            # لاگ شروع پردازش
            start_time = time.time()
            self._log_request(event_info, user)

        try:
            # پردازش توسط هندلر بعدی
            result = await handler(event, data)

            # لاگ پایان پردازش
            if self._should_log(event, user):
                elapsed = time.time() - start_time
                self._log_response(event_info, user, elapsed, success=True)

            return result

        except Exception as e:
            # لاگ خطا
            if self._log_errors:
                elapsed = time.time() - start_time if 'start_time' in locals() else 0
                self._log_error(event_info, user, e, elapsed)

            # propagate خطا به بالا
            raise

    def _should_log(self, event: Update, user: Optional[User]) -> bool:
        """
        بررسی اینکه آیا رویداد باید لاگ شود.

        Args:
            event: رویداد دریافتی.
            user: کاربر (اختیاری).

        Returns:
            bool: True اگر رویداد باید لاگ شود.
        """
        if not self._log_requests:
            return False

        # اگر پیام است
        if event.message:
            chat = event.message.chat
            if chat.type == "private" and not self._log_private:
                return False
            if chat.type in ("group", "supergroup") and not self._log_groups:
                return False

        # اگر کالبک است
        if event.callback_query:
            # کالبک‌ها معمولاً از پیام‌های خصوصی هستند
            if event.callback_query.message:
                chat = event.callback_query.message.chat
                if chat.type == "private" and not self._log_private:
                    return False
                if chat.type in ("group", "supergroup") and not self._log_groups:
                    return False

        return True

    def _extract_event_info(self, event: Update) -> Dict[str, Any]:
        """
        استخراج اطلاعات از رویداد.

        Args:
            event: رویداد دریافتی.

        Returns:
            Dict[str, Any]: اطلاعات رویداد.
        """
        info = {
            "type": "unknown",
            "chat_id": None,
            "message_id": None,
            "text": None,
            "callback_data": None,
        }

        if event.message:
            info["type"] = "message"
            info["chat_id"] = event.message.chat.id
            info["message_id"] = event.message.message_id
            if event.message.text:
                info["text"] = event.message.text[:200]  # محدود کردن طول
            elif event.message.caption:
                info["text"] = event.message.caption[:200]

        elif event.callback_query:
            info["type"] = "callback_query"
            if event.callback_query.message:
                info["chat_id"] = event.callback_query.message.chat.id
                info["message_id"] = event.callback_query.message.message_id
            info["callback_data"] = event.callback_query.data

        elif event.inline_query:
            info["type"] = "inline_query"
            info["query"] = event.inline_query.query

        elif event.chosen_inline_result:
            info["type"] = "chosen_inline_result"
            info["result_id"] = event.chosen_inline_result.result_id

        elif event.shipping_query:
            info["type"] = "shipping_query"

        elif event.pre_checkout_query:
            info["type"] = "pre_checkout_query"

        return info

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
        if event.shipping_query and event.shipping_query.from_user:
            return event.shipping_query.from_user
        if event.pre_checkout_query and event.pre_checkout_query.from_user:
            return event.pre_checkout_query.from_user
        return None

    def _log_request(self, event_info: Dict[str, Any], user: Optional[User]) -> None:
        """
        ثبت لاگ درخواست.

        Args:
            event_info: اطلاعات رویداد.
            user: کاربر (اختیاری).
        """
        user_info = self._get_user_info(user)

        log_data = {
            "event_type": event_info.get("type", "unknown"),
            "chat_id": event_info.get("chat_id"),
            "message_id": event_info.get("message_id"),
            "user": user_info,
            "timestamp": datetime.now().isoformat(),
        }

        # اضافه کردن اطلاعات خاص
        if event_info.get("text"):
            log_data["text"] = event_info["text"]
        if event_info.get("callback_data"):
            log_data["callback_data"] = event_info["callback_data"]
        if event_info.get("query"):
            log_data["query"] = event_info["query"]

        logger.info(f"Request: {log_data}")

    def _log_response(
        self,
        event_info: Dict[str, Any],
        user: Optional[User],
        elapsed: float,
        success: bool = True,
    ) -> None:
        """
        ثبت لاگ پاسخ.

        Args:
            event_info: اطلاعات رویداد.
            user: کاربر (اختیاری).
            elapsed: زمان پردازش بر حسب ثانیه.
            success: آیا پردازش با موفقیت انجام شد.
        """
        user_info = self._get_user_info(user)

        log_data = {
            "event_type": event_info.get("type", "unknown"),
            "chat_id": event_info.get("chat_id"),
            "message_id": event_info.get("message_id"),
            "user": user_info,
            "elapsed_seconds": round(elapsed, 4),
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"Response: {log_data}")

    def _log_error(
        self,
        event_info: Dict[str, Any],
        user: Optional[User],
        error: Exception,
        elapsed: float,
    ) -> None:
        """
        ثبت لاگ خطا.

        Args:
            event_info: اطلاعات رویداد.
            user: کاربر (اختیاری).
            error: استثنا.
            elapsed: زمان پردازش بر حسب ثانیه.
        """
        user_info = self._get_user_info(user)

        log_data = {
            "event_type": event_info.get("type", "unknown"),
            "chat_id": event_info.get("chat_id"),
            "message_id": event_info.get("message_id"),
            "user": user_info,
            "elapsed_seconds": round(elapsed, 4),
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
        }

        # اضافه کردن اطلاعات خاص
        if event_info.get("text"):
            log_data["text"] = event_info["text"]
        if event_info.get("callback_data"):
            log_data["callback_data"] = event_info["callback_data"]

        # اگر خطای تلگرام است، کد خطا را هم اضافه کن
        if isinstance(error, TelegramAPIError):
            log_data["telegram_error_code"] = getattr(error, "code", None)

        logger.error(f"Error: {log_data}", exc_info=True)

    def _get_user_info(self, user: Optional[User]) -> Dict[str, Any]:
        """
        دریافت اطلاعات کاربر.

        Args:
            user: کاربر (اختیاری).

        Returns:
            Dict[str, Any]: اطلاعات کاربر.
        """
        if not user:
            return {"id": None, "username": None, "full_name": None}

        return {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "is_bot": user.is_bot,
        }

    async def get_log_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار لاگ‌ها (برای استفاده در پنل مدیریت).

        Returns:
            Dict[str, Any]: آمار لاگ‌ها.
        """
        # در عمل، این آمار از سیستم لاگ جمع‌آوری می‌شود
        # اینجا یک پیاده‌سازی ساده ارائه می‌شود
        return {
            "log_requests": self._log_requests,
            "log_responses": self._log_responses,
            "log_errors": self._log_errors,
            "log_private": self._log_private,
            "log_groups": self._log_groups,
        }