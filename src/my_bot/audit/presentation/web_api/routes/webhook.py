# my_bot_project/src/my_bot/presentation/web_api/routes/webhook.py
"""
مسیریاب وب‌هوک (Webhook Router).

این ماژول شامل کلاس `WebhookRouter` است که مسئولیت دریافت و پردازش
وب‌هوک‌های دریافتی از تلگرام را بر عهده دارد. وب‌هوک‌ها به‌عنوان
جایگزین Long Polling برای دریافت به‌روزرسانی‌ها استفاده می‌شوند.
"""

import json
from typing import Optional, Dict, Any, Callable, Awaitable

from aiohttp import web, ClientTimeout
from aiohttp.web import Request, Response, json_response

from aiogram import Bot, Dispatcher
from aiogram.types import Update

from my_bot.core.config.app_config import AppConfig
from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.validation_errors import ValidationError

logger = get_logger(__name__)


class WebhookRouter:
    """
    مسیریاب وب‌هوک برای دریافت و پردازش رویدادهای تلگرام.

    این کلاس با استفاده از aiohttp، درخواست‌های POST ارسال‌شده به
    مسیر /webhook را دریافت کرده و پس از اعتبارسنجی، آنها را به
    Dispatcher تلگرام ارسال می‌کند.

    Attributes:
        bot: نمونه ربات تلگرام.
        dispatcher: نمونه Dispatcher برای پردازش رویدادها.
        config: پیکربندی برنامه.
        secret_token: توکن مخفی برای اعتبارسنجی وب‌هوک (اختیاری).
        timeout: زمان timeout برای پردازش درخواست.
    """

    def __init__(
        self,
        bot: Optional[Bot] = None,
        dispatcher: Optional[Dispatcher] = None,
        config: Optional[AppConfig] = None,
        secret_token: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        """
        مقداردهی اولیه مسیریاب وب‌هوک.

        Args:
            bot: نمونه ربات تلگرام (اختیاری).
            dispatcher: نمونه Dispatcher (اختیاری).
            config: پیکربندی برنامه (اختیاری).
            secret_token: توکن مخفی برای اعتبارسنجی (اختیاری).
            timeout: زمان timeout برای پردازش درخواست (پیش‌فرض ۳۰ ثانیه).
        """
        self.bot = bot
        self.dispatcher = dispatcher
        self.config = config
        self.secret_token = secret_token
        self.timeout = ClientTimeout(total=timeout)

        logger.info(
            f"WebhookRouter initialized: "
            f"bot={bot is not None}, dispatcher={dispatcher is not None}, "
            f"secret_token={'***' if secret_token else 'not set'}"
        )

    async def handle_webhook(self, request: Request) -> Response:
        """
        هندلر اصلی وب‌هوک برای پردازش درخواست‌های تلگرام.

        این متد درخواست POST را دریافت کرده، اعتبارسنجی می‌کند و
        سپس به Dispatcher تلگرام ارسال می‌نماید.

        Args:
            request: درخواست HTTP.

        Returns:
            Response: پاسخ HTTP (۲۰۰ در صورت موفقیت، ۴۰۳ در صورت خطای اعتبارسنجی).

        Raises:
            ValidationError: در صورت نامعتبر بودن درخواست.
        """
        try:
            # اعتبارسنجی هدرها
            if not self._validate_headers(request):
                logger.warning("Invalid webhook headers received.")
                return web.Response(status=403, text="Forbidden")

            # دریافت محتوای درخواست
            try:
                data = await request.json()
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in webhook request: {e}")
                return web.Response(status=400, text="Bad Request")

            # اعتبارسنجی داده‌ها
            if not self._validate_data(data):
                logger.warning("Invalid webhook data received.")
                return web.Response(status=400, text="Bad Request")

            # اگر bot یا dispatcher موجود نیست، فقط تأیید می‌کنیم
            if not self.bot or not self.dispatcher:
                logger.warning("Bot or Dispatcher not configured. Webhook received but not processed.")
                return web.Response(status=200, text="OK")

            # ایجاد شیء Update از داده‌ها
            try:
                update = Update(**data)
            except Exception as e:
                logger.error(f"Error creating Update object: {e}")
                return web.Response(status=400, text="Bad Request")

            # پردازش به‌روزرسانی
            try:
                await self.dispatcher.feed_update(self.bot, update)
                logger.debug(f"Webhook processed: update_id={update.update_id}")
            except Exception as e:
                logger.error(f"Error processing webhook update: {e}", exc_info=True)
                # در صورت خطا در پردازش، همچنان ۲۰۰ برمی‌گردانیم تا تلگرام دوباره تلاش نکند
                # اما خطا را لاگ می‌کنیم

            return web.Response(status=200, text="OK")

        except ValidationError as e:
            logger.warning(f"Validation error in webhook: {e}")
            return web.Response(status=403, text="Forbidden")

        except Exception as e:
            logger.error(f"Unexpected error in webhook handler: {e}", exc_info=True)
            return web.Response(status=500, text="Internal Server Error")

    def _validate_headers(self, request: Request) -> bool:
        """
        اعتبارسنجی هدرهای درخواست وب‌هوک.

        Args:
            request: درخواست HTTP.

        Returns:
            bool: True اگر هدرها معتبر باشند.
        """
        # بررسی Content-Type
        content_type = request.headers.get("Content-Type")
        if content_type != "application/json":
            logger.warning(f"Invalid Content-Type: {content_type}")
            return False

        # بررسی Secret Token (در صورت تنظیم بودن)
        if self.secret_token:
            received_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if received_token != self.secret_token:
                logger.warning("Invalid secret token received.")
                return False

        return True

    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """
        اعتبارسنجی داده‌های وب‌هوک.

        Args:
            data: داده‌های دریافت‌شده.

        Returns:
            bool: True اگر داده‌ها معتبر باشند.
        """
        # بررسی وجود update_id
        if "update_id" not in data:
            logger.warning("Missing update_id in webhook data.")
            return False

        # بررسی اینکه حداقل یکی از فیلدهای رویداد وجود داشته باشد
        valid_fields = [
            "message",
            "edited_message",
            "channel_post",
            "edited_channel_post",
            "inline_query",
            "chosen_inline_result",
            "callback_query",
            "shipping_query",
            "pre_checkout_query",
            "poll",
            "poll_answer",
            "my_chat_member",
            "chat_member",
            "chat_join_request",
        ]

        has_valid_field = any(field in data for field in valid_fields)
        if not has_valid_field:
            logger.warning("No valid event field in webhook data.")
            return False

        return True

    async def set_webhook(self, url: str) -> bool:
        """
        تنظیم وب‌هوک در تلگرام.

        Args:
            url: آدرس وب‌هوک (با فرمت کامل، شامل https).

        Returns:
            bool: True در صورت تنظیم موفق.

        Raises:
            Exception: در صورت بروز خطا در تنظیم وب‌هوک.
        """
        if not self.bot:
            raise RuntimeError("Bot instance not available for setting webhook.")

        try:
            # تنظیم وب‌هوک
            await self.bot.set_webhook(
                url=url,
                secret_token=self.secret_token,
                drop_pending_updates=True,
            )
            logger.info(f"Webhook set successfully: {url}")
            return True

        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            raise

    async def delete_webhook(self) -> bool:
        """
        حذف وب‌هوک از تلگرام (بازگشت به Long Polling).

        Returns:
            bool: True در صورت حذف موفق.

        Raises:
            Exception: در صورت بروز خطا در حذف وب‌هوک.
        """
        if not self.bot:
            raise RuntimeError("Bot instance not available for deleting webhook.")

        try:
            await self.bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook deleted successfully.")
            return True

        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            raise

    async def get_webhook_info(self) -> Dict[str, Any]:
        """
        دریافت اطلاعات وب‌هوک فعلی از تلگرام.

        Returns:
            Dict[str, Any]: اطلاعات وب‌هوک.

        Raises:
            Exception: در صورت بروز خطا در دریافت اطلاعات.
        """
        if not self.bot:
            raise RuntimeError("Bot instance not available.")

        try:
            info = await self.bot.get_webhook_info()
            logger.debug(f"Webhook info retrieved: url={info.url}")
            return {
                "url": info.url,
                "has_custom_certificate": info.has_custom_certificate,
                "pending_update_count": info.pending_update_count,
                "ip_address": info.ip_address,
                "last_error_date": info.last_error_date,
                "last_error_message": info.last_error_message,
                "max_connections": info.max_connections,
                "allowed_updates": info.allowed_updates,
            }

        except Exception as e:
            logger.error(f"Failed to get webhook info: {e}")
            raise

    def set_bot(self, bot: Bot) -> None:
        """
        تنظیم نمونه ربات.

        Args:
            bot: نمونه ربات تلگرام.
        """
        self.bot = bot
        logger.info("Bot instance set in WebhookRouter.")

    def set_dispatcher(self, dispatcher: Dispatcher) -> None:
        """
        تنظیم نمونه Dispatcher.

        Args:
            dispatcher: نمونه Dispatcher.
        """
        self.dispatcher = dispatcher
        logger.info("Dispatcher instance set in WebhookRouter.")