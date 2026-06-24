# my_bot_project/src/my_bot/notifications/templates/reminder_template.py
"""
قالب‌های یادآوری (Reminder Templates).

این ماژول شامل کلاس `ReminderTemplate` است که قالب‌های مختلف
برای ساخت پیام‌های یادآوری در کانال‌های مختلف (تلگرام، ایمیل، ...)
را فراهم می‌کند.
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class ReminderTemplate:
    """
    قالب‌های یادآوری برای ساخت پیام‌های مختلف.

    این کلاس با توجه به نوع یادآوری و داده‌های ورودی، پیام‌های
    مناسب برای کانال‌های مختلف تولید می‌کند.

    Attributes:
        default_language: زبان پیش‌فرض (پیش‌فرض: 'fa').
    """

    def __init__(self, default_language: str = "fa") -> None:
        """
        مقداردهی اولیه قالب یادآوری.

        Args:
            default_language: زبان پیش‌فرض (پیش‌فرض: 'fa').
        """
        self.default_language = default_language
        self._templates = self._get_templates()

        logger.info(f"ReminderTemplate initialized: language={default_language}")

    def _get_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        دریافت دیکشنری کامل قالب‌ها.

        Returns:
            Dict[str, Dict[str, Any]]: قالب‌های یادآوری.
        """
        return {
            "order_pending": {
                "telegram": {
                    "text": (
                        "⏳ **یادآوری سفارش**\n\n"
                        "سفارش شما با شماره {order_number} هنوز تکمیل نشده است.\n"
                        "مبلغ: {amount} تومان\n\n"
                        "لطفاً برای پرداخت و تکمیل سفارش اقدام کنید.\n\n"
                        "💡 در صورت نیاز به کمک، با پشتیبانی تماس بگیرید."
                    ),
                    "parse_mode": "Markdown",
                },
                "email": {
                    "subject": "یادآوری سفارش {order_number}",
                    "body": (
                        "سفارش شما با شماره {order_number} هنوز تکمیل نشده است.\n"
                        "مبلغ: {amount} تومان\n\n"
                        "لطفاً برای پرداخت و تکمیل سفارش اقدام کنید.\n\n"
                        "با تشکر، تیم پشتیبانی"
                    ),
                },
            },
            "inactivity": {
                "telegram": {
                    "text": (
                        "👋 **یادآوری عدم فعالیت**\n\n"
                        "شما بیش از {days} روز است که از ربات استفاده نکرده‌اید.\n"
                        "ما منتظر شما هستیم!\n\n"
                        "🌟 برای مشاهده خدمات جدید، به ربات سر بزنید."
                    ),
                    "parse_mode": "Markdown",
                },
                "email": {
                    "subject": "یادآوری عدم فعالیت",
                    "body": (
                        "شما بیش از {days} روز است که از ربات استفاده نکرده‌اید.\n\n"
                        "ما منتظر شما هستیم!\n\n"
                        "با تشکر، تیم پشتیبانی"
                    ),
                },
            },
            "form_incomplete": {
                "telegram": {
                    "text": (
                        "📝 **یادآوری فرم ناقص**\n\n"
                        "شما فرم '{form_title}' را شروع کرده‌اید اما تکمیل نکرده‌اید.\n\n"
                        "برای تکمیل فرم، روی دکمه زیر کلیک کنید:"
                    ),
                    "parse_mode": "Markdown",
                },
                "email": {
                    "subject": "یادآوری فرم ناقص",
                    "body": (
                        "شما فرم '{form_title}' را شروع کرده‌اید اما تکمیل نکرده‌اید.\n\n"
                        "لطفاً هرچه سریع‌تر آن را تکمیل کنید.\n\n"
                        "با تشکر، تیم پشتیبانی"
                    ),
                },
            },
            "payment_reminder": {
                "telegram": {
                    "text": (
                        "💳 **یادآوری پرداخت**\n\n"
                        "پرداخت شما با شناسه {payment_id} هنوز انجام نشده است.\n"
                        "مبلغ: {amount} تومان\n\n"
                        "لطفاً برای تکمیل پرداخت اقدام کنید."
                    ),
                    "parse_mode": "Markdown",
                },
                "email": {
                    "subject": "یادآوری پرداخت",
                    "body": (
                        "پرداخت شما با شناسه {payment_id} هنوز انجام نشده است.\n"
                        "مبلغ: {amount} تومان\n\n"
                        "لطفاً برای تکمیل پرداخت اقدام کنید.\n\n"
                        "با تشکر، تیم پشتیبانی"
                    ),
                },
            },
            "subscription_expiry": {
                "telegram": {
                    "text": (
                        "📅 **یادآوری انقضای اشتراک**\n\n"
                        "اشتراک شما در تاریخ {expiry_date} منقضی می‌شود.\n\n"
                        "برای تمدید اشتراک، روی دکمه زیر کلیک کنید:"
                    ),
                    "parse_mode": "Markdown",
                },
                "email": {
                    "subject": "یادآوری انقضای اشتراک",
                    "body": (
                        "اشتراک شما در تاریخ {expiry_date} منقضی می‌شود.\n\n"
                        "لطفاً برای تمدید اشتراک اقدام کنید.\n\n"
                        "با تشکر، تیم پشتیبانی"
                    ),
                },
            },
            "event_reminder": {
                "telegram": {
                    "text": (
                        "🎪 **یادآوری رویداد**\n\n"
                        "رویداد '{event_name}' در تاریخ {event_date} برگزار می‌شود.\n"
                        "زمان: {event_time}\n"
                        "مکان: {event_location}\n\n"
                        "برای اطلاعات بیشتر، روی دکمه زیر کلیک کنید:"
                    ),
                    "parse_mode": "Markdown",
                },
                "email": {
                    "subject": "یادآوری رویداد {event_name}",
                    "body": (
                        "رویداد '{event_name}' در تاریخ {event_date} برگزار می‌شود.\n"
                        "زمان: {event_time}\n"
                        "مکان: {event_location}\n\n"
                        "برای اطلاعات بیشتر به وب‌سایت مراجعه کنید.\n\n"
                        "با تشکر، تیم مدیریت"
                    ),
                },
            },
            "custom": {
                "telegram": {
                    "text": "{message}",
                    "parse_mode": "Markdown",
                },
                "email": {
                    "subject": "{subject}",
                    "body": "{message}",
                },
            },
        }

    def render_telegram(
        self,
        reminder_type: str,
        data: Dict[str, Any],
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        رندر قالب برای تلگرام.

        Args:
            reminder_type: نوع یادآوری.
            data: داده‌های جایگزینی در قالب.
            language: زبان (اختیاری، در صورت None از زبان پیش‌فرض استفاده می‌شود).

        Returns:
            Dict[str, Any]: شامل متن و parse_mode.

        Raises:
            ValueError: اگر نوع یادآوری نامعتبر باشد.
        """
        template = self._get_template(reminder_type, "telegram")
        if not template:
            raise ValueError(f"قالب یادآوری '{reminder_type}' برای تلگرام یافت نشد.")

        # جایگزینی داده‌ها
        text = template.get("text", "")
        try:
            text = text.format(**data)
        except KeyError as e:
            logger.warning(f"Missing key in reminder data: {e}")
            # ادامه با همان متن (بدون جایگزینی)

        return {
            "text": text,
            "parse_mode": template.get("parse_mode", "Markdown"),
        }

    def render_email(
        self,
        reminder_type: str,
        data: Dict[str, Any],
        language: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        رندر قالب برای ایمیل.

        Args:
            reminder_type: نوع یادآوری.
            data: داده‌های جایگزینی در قالب.
            language: زبان (اختیاری).

        Returns:
            Dict[str, str]: شامل subject و body.

        Raises:
            ValueError: اگر نوع یادآوری نامعتبر باشد.
        """
        template = self._get_template(reminder_type, "email")
        if not template:
            raise ValueError(f"قالب یادآوری '{reminder_type}' برای ایمیل یافت نشد.")

        # جایگزینی داده‌ها
        subject = template.get("subject", "")
        body = template.get("body", "")

        try:
            subject = subject.format(**data)
            body = body.format(**data)
        except KeyError as e:
            logger.warning(f"Missing key in reminder data: {e}")

        return {
            "subject": subject,
            "body": body,
        }

    def render_sms(
        self,
        reminder_type: str,
        data: Dict[str, Any],
        language: Optional[str] = None,
    ) -> str:
        """
        رندر قالب برای پیامک.

        Args:
            reminder_type: نوع یادآوری.
            data: داده‌های جایگزینی در قالب.
            language: زبان (اختیاری).

        Returns:
            str: متن پیامک.

        Raises:
            ValueError: اگر نوع یادآوری نامعتبر باشد.
        """
        template = self._get_template(reminder_type, "sms")
        if not template:
            # اگر قالب SMS وجود نداشت، از قالب تلگرام استفاده کن (با محدودیت کاراکتر)
            telegram_template = self._get_template(reminder_type, "telegram")
            if telegram_template:
                text = telegram_template.get("text", "")
                try:
                    text = text.format(**data)
                except KeyError as e:
                    logger.warning(f"Missing key in reminder data: {e}")
                # محدود کردن طول برای SMS (۱۶۰ کاراکتر)
                if len(text) > 160:
                    text = text[:157] + "..."
                return text

            # اگر هیچ قالبی نبود، از قالب سفارشی استفاده کن
            return self._render_custom_sms(data)

        text = template.get("text", "")
        try:
            text = text.format(**data)
        except KeyError as e:
            logger.warning(f"Missing key in reminder data: {e}")

        return text

    def _render_custom_sms(self, data: Dict[str, Any]) -> str:
        """
        رندر قالب سفارشی برای SMS.

        Args:
            data: داده‌ها.

        Returns:
            str: متن پیامک.
        """
        if "message" in data:
            message = data["message"]
            if len(message) > 160:
                message = message[:157] + "..."
            return message

        return "یادآوری: لطفاً به ربات مراجعه کنید."

    def _get_template(self, reminder_type: str, channel: str) -> Optional[Dict[str, Any]]:
        """
        دریافت قالب بر اساس نوع و کانال.

        Args:
            reminder_type: نوع یادآوری.
            channel: کانال ('telegram', 'email', 'sms').

        Returns:
            Optional[Dict[str, Any]]: قالب یا None.
        """
        if reminder_type not in self._templates:
            # استفاده از قالب سفارشی
            reminder_type = "custom"

        template = self._templates.get(reminder_type, {})
        return template.get(channel)

    def add_template(
        self,
        reminder_type: str,
        channel: str,
        template: Dict[str, Any],
    ) -> None:
        """
        افزودن یک قالب جدید.

        Args:
            reminder_type: نوع یادآوری.
            channel: کانال ('telegram', 'email', 'sms').
            template: قالب جدید.
        """
        if reminder_type not in self._templates:
            self._templates[reminder_type] = {}

        self._templates[reminder_type][channel] = template
        logger.info(f"Template added: type={reminder_type}, channel={channel}")

    def get_supported_types(self) -> list[str]:
        """
        دریافت لیست انواع یادآوری پشتیبانی‌شده.

        Returns:
            list[str]: لیست انواع.
        """
        return list(self._templates.keys())

    def get_supported_channels(self) -> list[str]:
        """
        دریافت لیست کانال‌های پشتیبانی‌شده.

        Returns:
            list[str]: لیست کانال‌ها.
        """
        return ["telegram", "email", "sms"]