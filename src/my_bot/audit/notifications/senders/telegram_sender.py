# my_bot_project/src/my_bot/notifications/senders/telegram_sender.py
"""
فرستنده نوتیفیکیشن تلگرام (Telegram Sender).

این کلاس مسئولیت ارسال نوتیفیکیشن‌ها از طریق ربات تلگرام را بر عهده دارد.
با استفاده از کتابخانه aiogram، پیام‌ها را به کاربران یا گروه‌ها ارسال می‌کند.
"""

import asyncio
from typing import Optional, List, Dict, Any, Union, Callable, Awaitable
from datetime import datetime

from aiogram import Bot
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ParseMode,
)
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramRetryAfter,
    TelegramForbiddenError,
)

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.not_found_errors import UserNotFoundError
from my_bot.core.exceptions.broadcast_errors import BroadcastSendingError
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.shared.decorators.retry_backoff import retry_backoff

logger = get_logger(__name__)


class TelegramSender:
    """
    فرستنده نوتیفیکیشن تلگرام.

    این کلاس با استفاده از Bot تلگرام، پیام‌ها را به کاربران یا گروه‌ها
    ارسال می‌کند و از مکانیزم Retry برای مقابله با خطاهای موقتی استفاده می‌کند.

    Attributes:
        bot: نمونه ربات تلگرام.
        user_repository: ریپازیتوری کاربر (برای دریافت شناسه‌های کاربران).
        default_parse_mode: حالت پارسینگ پیش‌فرض (پیش‌فرض: "HTML").
        retry_on_error: تلاش مجدد در صورت بروز خطا (پیش‌فرض True).
        max_retries: حداکثر تعداد تلاش‌های مجدد (پیش‌فرض ۳).
        retry_delay: تأخیر بین تلاش‌ها بر حسب ثانیه (پیش‌فرض ۱).
    """

    def __init__(
        self,
        bot: Bot,
        user_repository: Optional[UserRepository] = None,
        default_parse_mode: str = "HTML",
        retry_on_error: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """
        مقداردهی اولیه فرستنده تلگرام.

        Args:
            bot: نمونه ربات تلگرام.
            user_repository: ریپازیتوری کاربر (اختیاری).
            default_parse_mode: حالت پارسینگ پیش‌فرض (پیش‌فرض: "HTML").
            retry_on_error: تلاش مجدد در صورت بروز خطا (پیش‌فرض True).
            max_retries: حداکثر تعداد تلاش‌های مجدد (پیش‌فرض ۳).
            retry_delay: تأخیر بین تلاش‌ها بر حسب ثانیه (پیش‌فرض ۱).
        """
        self._bot = bot
        self._user_repository = user_repository
        self._default_parse_mode = default_parse_mode
        self._retry_on_error = retry_on_error
        self._max_retries = max_retries
        self._retry_delay = retry_delay

        logger.info(
            f"TelegramSender initialized: parse_mode={default_parse_mode}, "
            f"retry_on_error={retry_on_error}, max_retries={max_retries}"
        )

    @retry_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(TelegramRetryAfter,),
    )
    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        disable_web_page_preview: bool = False,
        disable_notification: bool = False,
        protect_content: bool = False,
    ) -> Optional[Message]:
        """
        ارسال یک پیام به یک کاربر یا گروه.

        Args:
            chat_id: شناسه چت (کاربر، گروه یا کانال).
            text: متن پیام.
            parse_mode: حالت پارسینگ (در صورت None از پیش‌فرض استفاده می‌شود).
            reply_markup: کیبورد شیشه‌ای (اختیاری).
            disable_web_page_preview: غیرفعال کردن پیش‌نمایش صفحات وب (پیش‌فرض False).
            disable_notification: ارسال بی‌صدا (پیش‌فرض False).
            protect_content: محافظت از محتوا (پیش‌فرض False).

        Returns:
            Optional[Message]: پیام ارسال‌شده در صورت موفقیت، یا None در صورت خطا.

        Raises:
            TelegramForbiddenError: اگر ربات دسترسی ارسال به کاربر را نداشته باشد.
            TelegramAPIError: در صورت بروز خطای دیگر از تلگرام.
        """
        try:
            parse_mode = parse_mode or self._default_parse_mode

            # برای شناسه‌های عددی (کاربران)، بررسی وجود کاربر
            if isinstance(chat_id, int) and chat_id > 0:
                # اگر ریپازیتوری کاربر وجود دارد، بررسی می‌کنیم
                if self._user_repository:
                    try:
                        user = await self._user_repository.get_by_telegram_id(chat_id)
                        if not user:
                            logger.warning(f"User with telegram_id {chat_id} not found.")
                    except Exception as e:
                        logger.warning(f"Error checking user existence: {e}")

            # ارسال پیام
            message = await self._bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification,
                protect_content=protect_content,
            )

            logger.debug(f"Message sent to {chat_id}: {text[:50]}...")
            return message

        except TelegramForbiddenError as e:
            logger.error(f"Bot blocked by user {chat_id}: {e}")
            raise

        except TelegramRetryAfter as e:
            logger.warning(f"Rate limited for {chat_id}, retry after {e.retry_after}s")
            raise

        except TelegramAPIError as e:
            logger.error(f"Telegram API error sending to {chat_id}: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error sending message to {chat_id}: {e}")
            raise

    @retry_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(TelegramRetryAfter,),
    )
    async def send_message_to_user(
        self,
        user_id: int,
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        disable_web_page_preview: bool = False,
        disable_notification: bool = False,
        protect_content: bool = False,
    ) -> Optional[Message]:
        """
        ارسال پیام به یک کاربر با شناسه تلگرام.

        Args:
            user_id: شناسه تلگرام کاربر.
            text: متن پیام.
            parse_mode: حالت پارسینگ (اختیاری).
            reply_markup: کیبورد شیشه‌ای (اختیاری).
            disable_web_page_preview: غیرفعال کردن پیش‌نمایش صفحات وب.
            disable_notification: ارسال بی‌صدا.
            protect_content: محافظت از محتوا.

        Returns:
            Optional[Message]: پیام ارسال‌شده.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        # اگر ریپازیتوری کاربر وجود دارد، وجود کاربر را بررسی می‌کنیم
        if self._user_repository:
            user = await self._user_repository.get_by_telegram_id(user_id)
            if not user:
                raise UserNotFoundError(telegram_id=user_id)

        return await self.send_message(
            chat_id=user_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            protect_content=protect_content,
        )

    @retry_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(TelegramRetryAfter,),
    )
    async def send_message_to_users(
        self,
        user_ids: List[int],
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        disable_web_page_preview: bool = False,
        disable_notification: bool = False,
        protect_content: bool = False,
        max_concurrent: int = 10,
    ) -> Dict[str, Any]:
        """
        ارسال یک پیام به چندین کاربر.

        Args:
            user_ids: لیست شناسه‌های تلگرام کاربران.
            text: متن پیام.
            parse_mode: حالت پارسینگ (اختیاری).
            reply_markup: کیبورد شیشه‌ای (اختیاری).
            disable_web_page_preview: غیرفعال کردن پیش‌نمایش صفحات وب.
            disable_notification: ارسال بی‌صدا.
            protect_content: محافظت از محتوا.
            max_concurrent: حداکثر تعداد ارسال همزمان (پیش‌فرض ۱۰).

        Returns:
            Dict[str, Any]: آمار ارسال شامل:
                - total: تعداد کل
                - sent: تعداد ارسال موفق
                - failed: تعداد ارسال ناموفق
                - errors: لیست خطاها
        """
        if not user_ids:
            return {"total": 0, "sent": 0, "failed": 0, "errors": []}

        logger.info(f"Sending message to {len(user_ids)} users")

        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def send_one(user_id: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    await self.send_message(
                        chat_id=user_id,
                        text=text,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup,
                        disable_web_page_preview=disable_web_page_preview,
                        disable_notification=disable_notification,
                        protect_content=protect_content,
                    )
                    return {"user_id": user_id, "success": True, "error": None}
                except Exception as e:
                    logger.error(f"Failed to send to {user_id}: {e}")
                    return {"user_id": user_id, "success": False, "error": str(e)}

        # ارسال به تمام کاربران
        tasks = [send_one(user_id) for user_id in user_ids]
        results = await asyncio.gather(*tasks)

        # محاسبه آمار
        total = len(results)
        sent = sum(1 for r in results if r["success"])
        failed = total - sent
        errors = [r["error"] for r in results if not r["success"] and r["error"]]

        logger.info(
            f"Bulk message sent: total={total}, sent={sent}, failed={failed}"
        )

        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "errors": errors,
        }

    @retry_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(TelegramRetryAfter,),
    )
    async def send_photo(
        self,
        chat_id: Union[int, str],
        photo: Union[str, bytes],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        disable_notification: bool = False,
        protect_content: bool = False,
    ) -> Optional[Message]:
        """
        ارسال یک عکس به کاربر یا گروه.

        Args:
            chat_id: شناسه چت.
            photo: آدرس عکس یا bytes.
            caption: کپشن (اختیاری).
            parse_mode: حالت پارسینگ (اختیاری).
            reply_markup: کیبورد شیشه‌ای (اختیاری).
            disable_notification: ارسال بی‌صدا.
            protect_content: محافظت از محتوا.

        Returns:
            Optional[Message]: پیام ارسال‌شده.
        """
        try:
            parse_mode = parse_mode or self._default_parse_mode

            message = await self._bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_notification=disable_notification,
                protect_content=protect_content,
            )

            logger.debug(f"Photo sent to {chat_id}: {caption[:50] if caption else ''}...")
            return message

        except TelegramAPIError as e:
            logger.error(f"Telegram API error sending photo to {chat_id}: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error sending photo to {chat_id}: {e}")
            raise

    async def send_media_group(
        self,
        chat_id: Union[int, str],
        media: List[Dict[str, Any]],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: bool = False,
        protect_content: bool = False,
    ) -> List[Message]:
        """
        ارسال گروهی از رسانه‌ها (تا ۱۰ عدد).

        Args:
            chat_id: شناسه چت.
            media: لیست رسانه‌ها (هر کدام شامل type, media, caption).
            caption: کپشن کلی (اختیاری).
            parse_mode: حالت پارسینگ (اختیاری).
            disable_notification: ارسال بی‌صدا.
            protect_content: محافظت از محتوا.

        Returns:
            List[Message]: لیست پیام‌های ارسال‌شده.

        Raises:
            TelegramAPIError: در صورت بروز خطا از تلگرام.
        """
        try:
            from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument

            media_list = []
            for item in media:
                media_type = item.get("type", "photo")
                media_file = item.get("media")
                media_caption = item.get("caption")

                if media_type == "photo":
                    media_list.append(
                        InputMediaPhoto(
                            media=media_file,
                            caption=media_caption,
                            parse_mode=parse_mode or self._default_parse_mode,
                        )
                    )
                elif media_type == "video":
                    media_list.append(
                        InputMediaVideo(
                            media=media_file,
                            caption=media_caption,
                            parse_mode=parse_mode or self._default_parse_mode,
                        )
                    )
                elif media_type == "document":
                    media_list.append(
                        InputMediaDocument(
                            media=media_file,
                            caption=media_caption,
                            parse_mode=parse_mode or self._default_parse_mode,
                        )
                    )

            if not media_list:
                raise ValueError("No valid media provided")

            messages = await self._bot.send_media_group(
                chat_id=chat_id,
                media=media_list,
                disable_notification=disable_notification,
                protect_content=protect_content,
            )

            logger.debug(f"Media group sent to {chat_id}: {len(messages)} items")
            return messages

        except TelegramAPIError as e:
            logger.error(f"Telegram API error sending media group to {chat_id}: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error sending media group to {chat_id}: {e}")
            raise

    @retry_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(TelegramRetryAfter,),
    )
    async def send_notification(
        self,
        user_id: int,
        notification_type: str,
        data: Dict[str, Any],
        template_func: Optional[Callable[[str, Dict[str, Any]], str]] = None,
    ) -> Optional[Message]:
        """
        ارسال یک نوتیفیکیشن به کاربر با استفاده از قالب.

        Args:
            user_id: شناسه تلگرام کاربر.
            notification_type: نوع نوتیفیکیشن (برای انتخاب قالب).
            data: داده‌های نوتیفیکیشن.
            template_func: تابع قالب‌سازی (اختیاری).

        Returns:
            Optional[Message]: پیام ارسال‌شده.
        """
        # ساخت متن پیام
        if template_func:
            text = template_func(notification_type, data)
        else:
            # قالب پیش‌فرض
            text = self._default_notification_template(notification_type, data)

        return await self.send_message_to_user(
            user_id=user_id,
            text=text,
            parse_mode="HTML",
        )

    def _default_notification_template(
        self,
        notification_type: str,
        data: Dict[str, Any],
    ) -> str:
        """
        قالب پیش‌فرض برای نوتیفیکیشن‌ها.

        Args:
            notification_type: نوع نوتیفیکیشن.
            data: داده‌های نوتیفیکیشن.

        Returns:
            str: متن نوتیفیکیشن.
        """
        templates = {
            "order_status": (
                "📦 **به‌روزرسانی سفارش**\n\n"
                "سفارش شما با شماره {order_number} به وضعیت {status} تغییر یافت."
            ),
            "payment_success": (
                "✅ **پرداخت موفق**\n\n"
                "پرداخت شما به مبلغ {amount} تومان با موفقیت انجام شد.\n"
                "کد پیگیری: {tracking_code}"
            ),
            "payment_failed": (
                "❌ **پرداخت ناموفق**\n\n"
                "پرداخت شما به مبلغ {amount} تومان ناموفق بود.\n"
                "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
            ),
            "form_submission": (
                "📝 **فرم جدید**\n\n"
                "فرم '{form_title}' توسط کاربر {user_name} ارسال شد."
            ),
            "level_upgrade": (
                "🎉 **ارتقاء سطح**\n\n"
                "تبریک! سطح شما از {old_level} به {new_level} ارتقاء یافت."
            ),
            "coupon_available": (
                "🎫 **کوپن تخفیف**\n\n"
                "یک کوپن تخفیف جدید برای شما در دسترس است.\n"
                "کد: {coupon_code}\n"
                "مبلغ تخفیف: {discount} تومان"
            ),
            "ticket_response": (
                "💬 **پاسخ به تیکت**\n\n"
                "به تیکت شما با موضوع '{subject}' پاسخ داده شد."
            ),
            "broadcast": (
                "📢 **پیام گروهی**\n\n"
                "{message}"
            ),
            "reminder_order_pending": (
                "⏳ **یادآوری سفارش**\n\n"
                "سفارش شما با شماره {order_number} هنوز تکمیل نشده است.\n"
                "لطفاً برای پرداخت اقدام کنید."
            ),
            "reminder_inactivity": (
                "👋 **یادآوری**\n\n"
                "شما مدتی است که از ربات استفاده نکرده‌اید.\n"
                "ما منتظر شما هستیم!"
            ),
        }

        template = templates.get(notification_type, "🔔 **نوتیفیکیشن**\n\n{message}")
        try:
            return template.format(**data)
        except KeyError as e:
            logger.warning(f"Missing key in notification data: {e}")
            return f"🔔 **نوتیفیکیشن**\n\n{data.get('message', '')}"

    async def get_bot_info(self) -> Dict[str, Any]:
        """
        دریافت اطلاعات ربات.

        Returns:
            Dict[str, Any]: اطلاعات ربات.
        """
        try:
            bot_info = await self._bot.get_me()
            return {
                "id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name,
                "is_bot": bot_info.is_bot,
                "can_join_groups": bot_info.can_join_groups,
                "can_read_all_group_messages": bot_info.can_read_all_group_messages,
                "supports_inline_queries": bot_info.supports_inline_queries,
            }
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return {"error": str(e)}