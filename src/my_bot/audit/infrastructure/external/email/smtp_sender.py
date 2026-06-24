# my_bot_project/src/my_bot/infrastructure/external/email/smtp_sender.py
"""
ارسال ایمیل از طریق SMTP (SMTP Sender).

این کلاس مسئولیت ارسال ایمیل‌ها از طریق سرور SMTP را بر عهده دارد.
از کتابخانه aiosmtplib برای ارسال غیرهمگام (Asynchronous) ایمیل استفاده می‌کند.
"""

import asyncio
from typing import Optional, List, Dict, Any
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


class SMTPSender:
    """
    سرویس ارسال ایمیل از طریق SMTP.

    این کلاس با استفاده از aiosmtplib، ایمیل‌ها را به‌صورت غیرهمگام
    از طریق سرور SMTP ارسال می‌کند.

    Attributes:
        host: آدرس سرور SMTP.
        port: پورت سرور SMTP.
        username: نام کاربری (اختیاری).
        password: رمز عبور (اختیاری).
        use_tls: استفاده از TLS (پیش‌فرض True).
        from_address: آدرس فرستنده (اختیاری).
        from_name: نام فرستنده (اختیاری).
        timeout: زمان timeout بر حسب ثانیه.
        _connection_pool: کش اتصالات (اختیاری).
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
    ) -> None:
        """
        مقداردهی اولیه سرویس SMTP.

        Args:
            host: آدرس سرور SMTP.
            port: پورت سرور SMTP (پیش‌فرض ۵۸۷).
            username: نام کاربری (اختیاری).
            password: رمز عبور (اختیاری).
            use_tls: استفاده از TLS (پیش‌فرض True).
            from_address: آدرس فرستنده (اختیاری).
            from_name: نام فرستنده (اختیاری).
            timeout: زمان timeout بر حسب ثانیه (پیش‌فرض ۳۰).
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_address = from_address
        self.from_name = from_name
        self.timeout = timeout
        self._connection_pool: List[SMTP] = []
        self._max_connections = 5
        self._lock = asyncio.Lock()

        logger.info(
            f"SMTPSender initialized: host={host}, port={port}, "
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
            # اگر اتصال موجود در کش وجود دارد، از آن استفاده کن
            if self._connection_pool:
                return self._connection_pool.pop()

        # ایجاد اتصال جدید
        try:
            smtp = SMTP(
                hostname=self.host,
                port=self.port,
                use_tls=self.use_tls,
                timeout=self.timeout,
            )
            await smtp.connect()

            # احراز هویت (در صورت وجود نام کاربری)
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
            if len(self._connection_pool) < self._max_connections:
                self._connection_pool.append(smtp)
            else:
                try:
                    await smtp.quit()
                except Exception as e:
                    logger.warning(f"Error closing SMTP connection: {e}")

    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_address: Optional[str] = None,
        from_name: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        reply_to: Optional[List[str]] = None,
    ) -> bool:
        """
        ارسال یک ایمیل.

        Args:
            to: لیست آدرس‌های گیرنده.
            subject: موضوع ایمیل.
            body: متن ساده ایمیل.
            html_body: متن HTML ایمیل (اختیاری).
            from_address: آدرس فرستنده (اختیاری، در صورت عدم مشخص بودن از تنظیمات استفاده می‌شود).
            from_name: نام فرستنده (اختیاری).
            cc: لیست آدرس‌های CC (اختیاری).
            bcc: لیست آدرس‌های BCC (اختیاری).
            attachments: لیست پیوست‌ها (هر پیوست شامل 'filename', 'content', 'content_type') (اختیاری).
            reply_to: لیست آدرس‌های Reply-To (اختیاری).

        Returns:
            bool: True در صورت ارسال موفق.

        Raises:
            EmailServiceError: در صورت بروز خطا در ارسال.
        """
        if not to:
            raise EmailServiceError(
                message="حداقل یک گیرنده باید مشخص شود.",
                context={"to": to},
            )

        # استفاده از آدرس فرستنده از تنظیمات یا پارامتر
        from_addr = from_address or self.from_address
        if not from_addr:
            raise EmailServiceError(
                message="آدرس فرستنده مشخص نشده است.",
                context={},
            )

        # نام فرستنده
        from_name_display = from_name or self.from_name or ""

        try:
            # ساخت ایمیل
            msg = await self._create_message(
                from_addr=from_addr,
                from_name=from_name_display,
                to=to,
                subject=subject,
                body=body,
                html_body=html_body,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                reply_to=reply_to,
            )

            # دریافت اتصال SMTP
            smtp = await self._get_connection()
            try:
                # ارسال ایمیل
                await smtp.send_message(msg)
                logger.info(
                    f"Email sent: subject='{subject}', to={to}, "
                    f"from={from_addr}"
                )
                return True

            finally:
                # بازگرداندن اتصال به کش
                await self._release_connection(smtp)

        except SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            raise EmailServiceError(
                message=f"خطا در ارسال ایمیل: {str(e)}",
                context={
                    "to": to,
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
                    "to": to,
                    "subject": subject,
                    "from": from_addr,
                    "error": str(e),
                },
            )

    async def _create_message(
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

        Raises:
            EmailServiceError: در صورت بروز خطا.
        """
        if not emails:
            return {"total": 0, "sent": 0, "failed": 0, "errors": []}

        logger.info(f"Sending bulk emails: {len(emails)} emails, max_concurrent={max_concurrent}")

        # ایجاد محدودیت همزمانی
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
                    return {"success": False, "error": str(e)}

        # اجرای ارسال‌ها
        tasks = [send_one(email) for email in emails]
        results = await asyncio.gather(*tasks)

        # محاسبه آمار
        total = len(results)
        sent = sum(1 for r in results if r["success"])
        failed = total - sent
        errors = [r["error"] for r in results if not r["success"] and r["error"]]

        logger.info(f"Bulk email sent: total={total}, sent={sent}, failed={failed}")

        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "errors": errors[:10],  # فقط ۱۰ خطا برای جلوگیری از حجم بالا
        }

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
            logger.info("SMTPSender closed successfully.")

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