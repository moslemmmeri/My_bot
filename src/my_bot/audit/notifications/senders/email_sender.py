# my_bot_project/src/my_bot/notifications/senders/email_sender.py
"""
فرستنده نوتیفیکیشن ایمیل (Email Sender).

این کلاس مسئولیت ارسال نوتیفیکیشن‌ها و پیام‌های سیستمی از طریق ایمیل را بر عهده دارد.
با استفاده از aiosmtplib، ایمیل‌ها را به‌صورت غیرهمگام از طریق سرور SMTP ارسال می‌کند.
"""

import asyncio
from typing import Optional, List, Dict, Any, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate
from pathlib import Path

import aiosmtplib
from aiosmtplib import SMTP, SMTPException

from my_bot.core.exceptions.external_errors import EmailServiceError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class EmailSender:
    """
    فرستنده نوتیفیکیشن ایمیل.

    این کلاس با استفاده از aiosmtplib، ایمیل‌ها را به‌صورت غیرهمگام
    از طریق سرور SMTP ارسال می‌کند و از Connection Pool برای
    مدیریت اتصالات استفاده می‌نماید.

    Attributes:
        host: آدرس سرور SMTP.
        port: پورت سرور SMTP.
        username: نام کاربری (اختیاری).
        password: رمز عبور (اختیاری).
        use_tls: استفاده از TLS (پیش‌فرض True).
        from_address: آدرس فرستنده (اجباری).
        from_name: نام فرستنده (اختیاری).
        timeout: زمان timeout بر حسب ثانیه (پیش‌فرض ۳۰).
        max_connections: حداکثر تعداد اتصالات همزمان (پیش‌فرض ۵).
        _connection_pool: کش اتصالات SMTP.
        _lock: قفل برای عملیات اتمیک.
    """

    def __init__(
        self,
        host: str,
        port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
        from_address: Optional[str] = None,
        from_name: Optional[str] = None,
        timeout: int = 30,
        max_connections: int = 5,
    ) -> None:
        """
        مقداردهی اولیه فرستنده ایمیل.

        Args:
            host: آدرس سرور SMTP.
            port: پورت سرور SMTP (پیش‌فرض ۵۸۷).
            username: نام کاربری (اختیاری).
            password: رمز عبور (اختیاری).
            use_tls: استفاده از TLS (پیش‌فرض True).
            from_address: آدرس فرستنده (اجباری).
            from_name: نام فرستنده (اختیاری).
            timeout: زمان timeout بر حسب ثانیه (پیش‌فرض ۳۰).
            max_connections: حداکثر تعداد اتصالات همزمان (پیش‌فرض ۵).

        Raises:
            EmailServiceError: اگر آدرس فرستنده مشخص نشده باشد.
        """
        if not from_address:
            raise EmailServiceError(
                message="آدرس فرستنده (from_address) اجباری است.",
                context={},
            )

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_address = from_address
        self.from_name = from_name
        self.timeout = timeout
        self.max_connections = max_connections

        self._connection_pool: List[SMTP] = []
        self._lock = asyncio.Lock()

        logger.info(
            f"EmailSender initialized: host={host}, port={port}, "
            f"use_tls={use_tls}, from_address={from_address}"
        )

    async def _get_connection(self) -> SMTP:
        """
        دریافت یا ایجاد یک اتصال SMTP.

        Returns:
            SMTP: اتصال SMTP.

        Raises:
            EmailServiceError: در صورت بروز خطا در اتصال.
        """
        async with self._lock:
            if self._connection_pool:
                return self._connection_pool.pop()

        try:
            smtp = SMTP(
                hostname=self.host,
                port=self.port,
                use_tls=self.use_tls,
                timeout=self.timeout,
            )
            await smtp.connect()

            if self.username and self.password:
                await smtp.login(self.username, self.password)

            logger.debug(f"SMTP connection established to {self.host}:{self.port}")
            return smtp

        except SMTPException as e:
            logger.error(f"SMTP connection failed: {e}")
            raise EmailServiceError(
                message=f"خطا در اتصال به سرور SMTP: {str(e)}",
                context={"host": self.host, "port": self.port, "error": str(e)},
            )
        except Exception as e:
            logger.error(f"Unexpected error in SMTP connection: {e}")
            raise EmailServiceError(
                message=f"خطای غیرمنتظره در اتصال SMTP: {str(e)}",
                context={"host": self.host, "port": self.port, "error": str(e)},
            )

    async def _release_connection(self, smtp: SMTP) -> None:
        """
        بازگرداندن اتصال به کش.

        Args:
            smtp: اتصال SMTP برای بازگرداندن.
        """
        async with self._lock:
            if len(self._connection_pool) < self.max_connections:
                self._connection_pool.append(smtp)
            else:
                try:
                    await smtp.quit()
                except Exception as e:
                    logger.warning(f"Error closing SMTP connection: {e}")

    async def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_address: Optional[str] = None,
        from_name: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        reply_to: Optional[Union[str, List[str]]] = None,
    ) -> bool:
        """
        ارسال یک ایمیل.

        Args:
            to: آدرس یا لیست آدرس‌های گیرنده.
            subject: موضوع ایمیل.
            body: متن ساده ایمیل.
            html_body: متن HTML ایمیل (اختیاری).
            from_address: آدرس فرستنده (اختیاری، در صورت عدم مشخص بودن از تنظیمات استفاده می‌شود).
            from_name: نام فرستنده (اختیاری).
            cc: آدرس یا لیست آدرس‌های CC (اختیاری).
            bcc: آدرس یا لیست آدرس‌های BCC (اختیاری).
            attachments: لیست پیوست‌ها (هر پیوست شامل 'filename', 'content', 'content_type') (اختیاری).
            reply_to: آدرس یا لیست آدرس‌های Reply-To (اختیاری).

        Returns:
            bool: True در صورت ارسال موفق.

        Raises:
            EmailServiceError: در صورت بروز خطا در ارسال.
        """
        # تبدیل ورودی‌ها به لیست
        to_list = [to] if isinstance(to, str) else to
        if not to_list:
            raise EmailServiceError(
                message="حداقل یک گیرنده باید مشخص شود.",
                context={"to": to},
            )

        cc_list = [cc] if isinstance(cc, str) else cc if cc else []
        bcc_list = [bcc] if isinstance(bcc, str) else bcc if bcc else []
        reply_to_list = [reply_to] if isinstance(reply_to, str) else reply_to if reply_to else []

        # استفاده از آدرس فرستنده
        from_addr = from_address or self.from_address
        if not from_addr:
            raise EmailServiceError(
                message="آدرس فرستنده مشخص نشده است.",
                context={},
            )

        from_name_display = from_name or self.from_name or ""

        try:
            # ساخت ایمیل
            msg = self._create_message(
                from_addr=from_addr,
                from_name=from_name_display,
                to=to_list,
                subject=subject,
                body=body,
                html_body=html_body,
                cc=cc_list,
                bcc=bcc_list,
                attachments=attachments,
                reply_to=reply_to_list,
            )

            # دریافت اتصال SMTP
            smtp = await self._get_connection()
            try:
                # ارسال ایمیل
                await smtp.send_message(msg)
                logger.info(
                    f"Email sent: subject='{subject}', to={to_list}, "
                    f"from={from_addr}"
                )
                return True

            finally:
                await self._release_connection(smtp)

        except SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            raise EmailServiceError(
                message=f"خطا در ارسال ایمیل: {str(e)}",
                context={
                    "to": to_list,
                    "subject": subject,
                    "from": from_addr,
                    "error": str(e),
                },
            )
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            raise EmailServiceError(
                message=f"خطای غیرمنتظره در ارسال ایمیل: {str(e)}",
                context={
                    "to": to_list,
                    "subject": subject,
                    "from": from_addr,
                    "error": str(e),
                },
            )

    def _create_message(
        self,
        from_addr: str,
        from_name: str,
        to: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        reply_to: Optional[List[str]] = None,
    ) -> MIMEMultipart:
        """
        ساخت یک پیام MIME.

        Args:
            from_addr: آدرس فرستنده.
            from_name: نام فرستنده.
            to: لیست آدرس‌های گیرنده.
            subject: موضوع ایمیل.
            body: متن ساده ایمیل.
            html_body: متن HTML ایمیل (اختیاری).
            cc: لیست آدرس‌های CC (اختیاری).
            bcc: لیست آدرس‌های BCC (اختیاری).
            attachments: لیست پیوست‌ها (اختیاری).
            reply_to: لیست آدرس‌های Reply-To (اختیاری).

        Returns:
            MIMEMultipart: پیام ساخته‌شده.
        """
        # ایجاد پیام چندبخشی
        msg = MIMEMultipart("alternative")

        # تنظیم هدرها
        msg["From"] = f"{from_name} <{from_addr}>" if from_name else from_addr
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject
        msg["Date"] = formatdate()

        if cc:
            msg["Cc"] = ", ".join(cc)
        if reply_to:
            msg["Reply-To"] = ", ".join(reply_to)

        # افزودن متن ساده
        text_part = MIMEText(body, "plain", "utf-8")
        msg.attach(text_part)

        # افزودن متن HTML (در صورت وجود)
        if html_body:
            html_part = MIMEText(html_body, "html", "utf-8")
            msg.attach(html_part)

        # افزودن پیوست‌ها
        if attachments:
            for attachment in attachments:
                content = attachment.get("content")
                filename = attachment.get("filename", "attachment")
                content_type = attachment.get("content_type", "application/octet-stream")

                if content is None:
                    logger.warning(f"Skipping attachment with no content: {filename}")
                    continue

                # ساخت بخش پیوست
                part = MIMEBase(*content_type.split("/"))
                part.set_payload(content)

                # کدگذاری base64
                encoders.encode_base64(part)

                # تنظیم هدرهای پیوست
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={filename}",
                )
                msg.attach(part)

        return msg

    async def send_notification(
        self,
        to: Union[str, List[str]],
        notification_type: str,
        data: Dict[str, Any],
        template_func: Optional[callable] = None,
    ) -> bool:
        """
        ارسال یک نوتیفیکیشن از طریق ایمیل.

        Args:
            to: آدرس یا لیست آدرس‌های گیرنده.
            notification_type: نوع نوتیفیکیشن.
            data: داده‌های نوتیفیکیشن.
            template_func: تابع قالب‌سازی (اختیاری).

        Returns:
            bool: True در صورت ارسال موفق.
        """
        # ساخت موضوع و محتوا
        if template_func:
            subject, body, html_body = template_func(notification_type, data)
        else:
            subject, body, html_body = self._default_notification_template(
                notification_type, data
            )

        return await self.send_email(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
        )

    def _default_notification_template(
        self,
        notification_type: str,
        data: Dict[str, Any],
    ) -> tuple[str, str, Optional[str]]:
        """
        قالب پیش‌فرض برای نوتیفیکیشن‌های ایمیل.

        Args:
            notification_type: نوع نوتیفیکیشن.
            data: داده‌های نوتیفیکیشن.

        Returns:
            tuple[str, str, Optional[str]]: موضوع، متن ساده و متن HTML.
        """
        subject_map = {
            "order_status": "به‌روزرسانی سفارش",
            "payment_success": "پرداخت موفق",
            "payment_failed": "پرداخت ناموفق",
            "form_submission": "فرم جدید",
            "level_upgrade": "ارتقاء سطح",
            "coupon_available": "کوپن تخفیف",
            "ticket_response": "پاسخ به تیکت",
            "broadcast": "پیام گروهی",
            "report": "گزارش سیستم",
        }

        subject = subject_map.get(notification_type, "نوتیفیکیشن")

        # محتوای ساده
        body = f"{subject}\n\n"
        for key, value in data.items():
            body += f"{key}: {value}\n"

        # محتوای HTML (اختیاری)
        html_body = f"<html><body><h2>{subject}</h2><ul>"
        for key, value in data.items():
            html_body += f"<li><b>{key}:</b> {value}</li>"
        html_body += "</ul></body></html>"

        return subject, body, html_body

    async def send_bulk(
        self,
        emails: List[Dict[str, Any]],
        max_concurrent: int = 5,
    ) -> Dict[str, Any]:
        """
        ارسال ایمیل‌های انبوه.

        Args:
            emails: لیست ایمیل‌ها برای ارسال (هر کدام شامل to, subject, body و ...).
            max_concurrent: حداکثر تعداد ارسال همزمان.

        Returns:
            Dict[str, Any]: آمار ارسال (total, sent, failed, errors).
        """
        if not emails:
            return {"total": 0, "sent": 0, "failed": 0, "errors": []}

        logger.info(f"Sending bulk emails: {len(emails)} emails, max_concurrent={max_concurrent}")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_one(email_data: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                try:
                    to = email_data.get("to")
                    if isinstance(to, str):
                        to = [to]
                    elif not to:
                        return {"success": False, "error": "No recipient"}

                    success = await self.send_email(
                        to=to,
                        subject=email_data.get("subject", ""),
                        body=email_data.get("body", ""),
                        html_body=email_data.get("html_body"),
                        from_address=email_data.get("from_address"),
                        from_name=email_data.get("from_name"),
                        cc=email_data.get("cc"),
                        bcc=email_data.get("bcc"),
                        attachments=email_data.get("attachments"),
                        reply_to=email_data.get("reply_to"),
                    )
                    return {"success": success, "error": None}
                except Exception as e:
                    logger.error(f"Error sending bulk email: {e}")
                    return {"success": False, "error": str(e)}

        tasks = [send_one(email) for email in emails]
        results = await asyncio.gather(*tasks)

        total = len(results)
        sent = sum(1 for r in results if r["success"])
        failed = total - sent
        errors = [r["error"] for r in results if not r["success"] and r["error"]]

        logger.info(f"Bulk email sent: total={total}, sent={sent}, failed={failed}")

        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "errors": errors[:10],
        }

    async def health_check(self) -> bool:
        """
        بررسی سلامت سرویس SMTP.

        Returns:
            bool: True اگر سرویس سالم باشد.
        """
        try:
            smtp = await self._get_connection()
            try:
                await smtp.noop()
                return True
            finally:
                await self._release_connection(smtp)
        except Exception as e:
            logger.warning(f"SMTP health check failed: {e}")
            return False

    async def close(self) -> None:
        """
        بستن تمام اتصالات SMTP.
        """
        async with self._lock:
            for smtp in self._connection_pool:
                try:
                    await smtp.quit()
                except Exception as e:
                    logger.warning(f"Error closing SMTP connection: {e}")
            self._connection_pool.clear()
            logger.info("EmailSender closed successfully.")