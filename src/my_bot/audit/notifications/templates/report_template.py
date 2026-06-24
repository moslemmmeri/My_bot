# my_bot_project/src/my_bot/notifications/templates/report_template.py
"""
قالب‌های گزارش (Report Templates).

این ماژول شامل کلاس `ReportTemplate` است که قالب‌های مختلف
برای تولید گزارش‌های دوره‌ای (روزانه، هفتگی، ماهانه) را در کانال‌های
مختلف (تلگرام، ایمیل، ...) فراهم می‌کند.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class ReportTemplate:
    """
    قالب‌های گزارش برای ساخت پیام‌های گزارش.

    این کلاس با توجه به نوع گزارش و داده‌های ورودی، پیام‌های
    مناسب برای کانال‌های مختلف تولید می‌کند.

    Attributes:
        default_language: زبان پیش‌فرض (پیش‌فرض: 'fa').
    """

    def __init__(self, default_language: str = "fa") -> None:
        """
        مقداردهی اولیه قالب گزارش.

        Args:
            default_language: زبان پیش‌فرض (پیش‌فرض: 'fa').
        """
        self.default_language = default_language
        self._templates = self._get_templates()

        logger.info(f"ReportTemplate initialized: language={default_language}")

    def _get_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        دریافت دیکشنری کامل قالب‌های گزارش.

        Returns:
            Dict[str, Dict[str, Any]]: قالب‌های گزارش.
        """
        return {
            "daily": {
                "telegram": {
                    "text": (
                        "📊 **گزارش روزانه**\n\n"
                        "📅 تاریخ: {date}\n"
                        "👥 کاربران جدید: {new_users}\n"
                        "🛒 سفارشات جدید: {new_orders}\n"
                        "💰 درآمد امروز: {revenue} تومان\n"
                        "📝 فرم‌های تکمیل‌شده: {completed_forms}\n\n"
                        "🔍 برای مشاهده جزئیات بیشتر، به پنل مدیریت مراجعه کنید."
                    ),
                    "parse_mode": "Markdown",
                },
                "email": {
                    "subject": "گزارش روزانه - {date}",
                    "body": (
                        "گزارش روزانه\n"
                        "تاریخ: {date}\n"
                        "کاربران جدید: {new_users}\n"
                        "سفارشات جدید: {new_orders}\n"
                        "درآمد امروز: {revenue} تومان\n"
                        "فرم‌های تکمیل‌شده: {completed_forms}\n\n"
                        "با تشکر، تیم مدیریت"
                    ),
                },
            },
            "weekly": {
                "telegram": {
                    "text": (
                        "📊 **گزارش هفتگی**\n\n"
                        "📅 هفته: {week}\n"
                        "👥 کاربران جدید: {new_users}\n"
                        "🛒 سفارشات جدید: {new_orders}\n"
                        "💰 درآمد هفته: {revenue} تومان\n"
                        "📝 فرم‌های تکمیل‌شده: {completed_forms}\n"
                        "⭐ میانگین امتیاز کاربران: {avg_rating}\n\n"
                        "🔍 برای مشاهده جزئیات بیشتر، به پنل مدیریت مراجعه کنید."
                    ),
                    "parse_mode": "Markdown",
                },
                "email": {
                    "subject": "گزارش هفتگی - هفته {week}",
                    "body": (
                        "گزارش هفتگی\n"
                        "هفته: {week}\n"
                        "کاربران جدید: {new_users}\n"
                        "سفارشات جدید: {new_orders}\n"
                        "درآمد هفته: {revenue} تومان\n"
                        "فرم‌های تکمیل‌شده: {completed_forms}\n"
                        "میانگین امتیاز کاربران: {avg_rating}\n\n"
                        "با تشکر، تیم مدیریت"
                    ),
                },
            },
            "monthly": {
                "telegram": {
                    "text": (
                        "📊 **گزارش ماهانه**\n\n"
                        "📅 ماه: {month}\n"
                        "👥 کاربران جدید: {new_users}\n"
                        "🛒 سفارشات جدید: {new_orders}\n"
                        "💰 درآمد ماه: {revenue} تومان\n"
                        "📝 فرم‌های تکمیل‌شده: {completed_forms}\n"
                        "⭐ میانگین امتیاز کاربران: {avg_rating}\n"
                        "🏆 کاربر برتر: {top_user}\n\n"
                        "🔍 برای مشاهده جزئیات بیشتر، به پنل مدیریت مراجعه کنید."
                    ),
                    "parse_mode": "Markdown",
                },
                "email": {
                    "subject": "گزارش ماهانه - {month}",
                    "body": (
                        "گزارش ماهانه\n"
                        "ماه: {month}\n"
                        "کاربران جدید: {new_users}\n"
                        "سفارشات جدید: {new_orders}\n"
                        "درآمد ماه: {revenue} تومان\n"
                        "فرم‌های تکمیل‌شده: {completed_forms}\n"
                        "میانگین امتیاز کاربران: {avg_rating}\n"
                        "کاربر برتر: {top_user}\n\n"
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
        report_type: str,
        data: Dict[str, Any],
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        رندر قالب گزارش برای تلگرام.

        Args:
            report_type: نوع گزارش ('daily', 'weekly', 'monthly', 'custom').
            data: داده‌های جایگزینی در قالب.
            language: زبان (اختیاری، در صورت None از زبان پیش‌فرض استفاده می‌شود).

        Returns:
            Dict[str, Any]: شامل متن و parse_mode.

        Raises:
            ValueError: اگر نوع گزارش نامعتبر باشد.
        """
        template = self._get_template(report_type, "telegram")
        if not template:
            raise ValueError(f"قالب گزارش '{report_type}' برای تلگرام یافت نشد.")

        text = template.get("text", "")
        try:
            text = text.format(**data)
        except KeyError as e:
            logger.warning(f"Missing key in report data: {e}")

        return {
            "text": text,
            "parse_mode": template.get("parse_mode", "Markdown"),
        }

    def render_email(
        self,
        report_type: str,
        data: Dict[str, Any],
        language: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        رندر قالب گزارش برای ایمیل.

        Args:
            report_type: نوع گزارش.
            data: داده‌های جایگزینی.
            language: زبان (اختیاری).

        Returns:
            Dict[str, str]: شامل subject و body.

        Raises:
            ValueError: اگر نوع گزارش نامعتبر باشد.
        """
        template = self._get_template(report_type, "email")
        if not template:
            raise ValueError(f"قالب گزارش '{report_type}' برای ایمیل یافت نشد.")

        subject = template.get("subject", "")
        body = template.get("body", "")

        try:
            subject = subject.format(**data)
            body = body.format(**data)
        except KeyError as e:
            logger.warning(f"Missing key in report data: {e}")

        return {
            "subject": subject,
            "body": body,
        }

    def render_sms(
        self,
        report_type: str,
        data: Dict[str, Any],
        language: Optional[str] = None,
    ) -> str:
        """
        رندر قالب گزارش برای پیامک (خلاصه).

        Args:
            report_type: نوع گزارش.
            data: داده‌های جایگزینی.
            language: زبان (اختیاری).

        Returns:
            str: متن پیامک.

        Raises:
            ValueError: اگر نوع گزارش نامعتبر باشد.
        """
        template = self._get_template(report_type, "sms")
        if not template:
            # اگر قالب SMS وجود نداشت، از قالب تلگرام استفاده کن (با محدودیت کاراکتر)
            telegram_template = self._get_template(report_type, "telegram")
            if telegram_template:
                text = telegram_template.get("text", "")
                try:
                    text = text.format(**data)
                except KeyError as e:
                    logger.warning(f"Missing key in report data: {e}")
                # محدود کردن طول برای SMS (۱۶۰ کاراکتر)
                if len(text) > 160:
                    text = text[:157] + "..."
                return text

            # اگر هیچ قالبی نبود، یک پیام خلاصه تولید کن
            return self._render_custom_sms(data)

        text = template.get("text", "")
        try:
            text = text.format(**data)
        except KeyError as e:
            logger.warning(f"Missing key in report data: {e}")

        return text

    def _render_custom_sms(self, data: Dict[str, Any]) -> str:
        """
        رندر قالب سفارشی برای SMS.

        Args:
            data: داده‌ها.

        Returns:
            str: متن پیامک.
        """
        if "summary" in data:
            summary = data["summary"]
            if len(summary) > 160:
                summary = summary[:157] + "..."
            return summary

        if "revenue" in data:
            return f"گزارش: درآمد {data.get('revenue', 0)} تومان، {data.get('new_orders', 0)} سفارش جدید"

        return "گزارش سیستم - برای مشاهده جزئیات به ربات مراجعه کنید."

    def _get_template(self, report_type: str, channel: str) -> Optional[Dict[str, Any]]:
        """
        دریافت قالب بر اساس نوع و کانال.

        Args:
            report_type: نوع گزارش.
            channel: کانال ('telegram', 'email', 'sms').

        Returns:
            Optional[Dict[str, Any]]: قالب یا None.
        """
        if report_type not in self._templates:
            report_type = "custom"

        template = self._templates.get(report_type, {})
        return template.get(channel)

    def add_template(
        self,
        report_type: str,
        channel: str,
        template: Dict[str, Any],
    ) -> None:
        """
        افزودن یک قالب جدید.

        Args:
            report_type: نوع گزارش.
            channel: کانال ('telegram', 'email', 'sms').
            template: قالب جدید.
        """
        if report_type not in self._templates:
            self._templates[report_type] = {}

        self._templates[report_type][channel] = template
        logger.info(f"Template added: type={report_type}, channel={channel}")

    def get_supported_types(self) -> list[str]:
        """
        دریافت لیست انواع گزارش پشتیبانی‌شده.

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

    def render(
        self,
        report_type: str,
        data: Dict[str, Any],
        description: Optional[str] = None,
        channel: str = "telegram",
    ) -> str:
        """
        متد عمومی برای رندر گزارش در کانال مشخص.

        Args:
            report_type: نوع گزارش.
            data: داده‌های جایگزینی.
            description: توضیحات اضافی (اختیاری).
            channel: کانال ('telegram', 'email', 'sms').

        Returns:
            str: متن رندر شده.

        Raises:
            ValueError: اگر کانال یا نوع گزارش نامعتبر باشد.
        """
        if channel == "telegram":
            result = self.render_telegram(report_type, data)
            return result["text"]
        elif channel == "email":
            result = self.render_email(report_type, data)
            return f"Subject: {result['subject']}\n\n{result['body']}"
        elif channel == "sms":
            return self.render_sms(report_type, data)
        else:
            raise ValueError(f"کانال '{channel}' پشتیبانی نمی‌شود.")