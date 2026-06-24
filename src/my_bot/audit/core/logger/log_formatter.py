# my_bot_project/src/my_bot/core/logger/log_formatter.py
"""
فرمت‌دهنده‌ی لاگ‌ها (Log Formatter).

این ماژول شامل کلاس `LogFormatter` است که برای فرمت‌سازی پیام‌های لاگ
با قابلیت خروجی JSON و فرمت‌های سفارشی استفاده می‌شود.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional


class LogFormatter(logging.Formatter):
    """
    فرمت‌دهنده‌ی پیشرفته برای لاگ‌ها با پشتیبانی از خروجی JSON.

    این کلاس از `logging.Formatter` ارث‌بری می‌کند و امکانات زیر را فراهم می‌کند:
        - فرمت‌سازی استاندارد با تاریخ و زمان
        - خروجی JSON برای استفاده در سیستم‌های جمع‌آوری لاگ
        - اضافه کردن فیلدهای سفارشی به لاگ
        - پشتیبانی از استثناها و traceback

    Attributes:
        fmt: فرمت رشته‌ای لاگ.
        datefmt: فرمت تاریخ و زمان.
        use_json: فعال‌سازی خروجی JSON.
        extra_fields: فیلدهای اضافی برای اضافه کردن به لاگ.
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        use_json: bool = False,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه فرمت‌دهنده.

        Args:
            fmt: فرمت رشته‌ای لاگ (پیش‌فرض: استاندارد).
            datefmt: فرمت تاریخ و زمان (پیش‌فرض: '%Y-%m-%d %H:%M:%S').
            use_json: فعال‌سازی خروجی JSON (پیش‌فرض: False).
            extra_fields: فیلدهای اضافی برای اضافه کردن به لاگ (اختیاری).
        """
        if fmt is None:
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"

        super().__init__(fmt=fmt, datefmt=datefmt)
        self.use_json = use_json
        self.extra_fields = extra_fields or {}
        self._default_fmt = fmt
        self._default_datefmt = datefmt

    def format(self, record: logging.LogRecord) -> str:
        """
        فرمت‌سازی یک رکورد لاگ.

        Args:
            record: رکورد لاگ برای فرمت‌سازی.

        Returns:
            رشته‌ی فرمت‌شده‌ی لاگ.
        """
        # اگر use_json فعال باشد، خروجی JSON تولید می‌شود
        if self.use_json:
            return self._format_json(record)

        # در غیر این صورت، از فرمت استاندارد استفاده می‌شود
        return super().format(record)

    def _format_json(self, record: logging.LogRecord) -> str:
        """
        فرمت‌سازی رکورد لاگ به صورت JSON.

        Args:
            record: رکورد لاگ.

        Returns:
            رشته‌ی JSON شامل اطلاعات لاگ.
        """
        # ایجاد دیکشنری پایه
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "path": record.pathname,
        }

        # اضافه کردن فیلدهای اضافی
        if self.extra_fields:
            log_data.update(self.extra_fields)

        # اضافه کردن فیلدهای سفارشی از رکورد (در صورت وجود)
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        # اضافه کردن استثنا (در صورت وجود)
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # اضافه کردن stack trace (در صورت وجود)
        if record.stack_info:
            log_data["stack_info"] = record.stack_info

        # اضافه کردن process و thread (اختیاری)
        log_data["process"] = record.process
        log_data["thread"] = record.thread

        return json.dumps(log_data, ensure_ascii=False)

    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        """
        فرمت‌سازی زمان رکورد لاگ.

        Args:
            record: رکورد لاگ.
            datefmt: فرمت تاریخ و زمان (اختیاری).

        Returns:
            رشته‌ی زمان فرمت‌شده.
        """
        if datefmt is None:
            datefmt = self.datefmt

        # استفاده از datetime برای فرمت‌سازی دقیق‌تر
        dt = datetime.fromtimestamp(record.created)
        if datefmt:
            return dt.strftime(datefmt)

        # استفاده از فرمت پیش‌فرض
        return dt.isoformat()

    def set_json_mode(self, enabled: bool) -> None:
        """
        فعال یا غیرفعال کردن خروجی JSON.

        Args:
            enabled: True برای فعال‌سازی، False برای غیرفعال‌سازی.
        """
        self.use_json = enabled

    def add_extra_field(self, key: str, value: Any) -> None:
        """
        اضافه کردن یک فیلد اضافی به لاگ‌ها.

        Args:
            key: نام فیلد.
            value: مقدار فیلد.
        """
        self.extra_fields[key] = value

    def remove_extra_field(self, key: str) -> None:
        """
        حذف یک فیلد اضافی از لاگ‌ها.

        Args:
            key: نام فیلد.
        """
        if key in self.extra_fields:
            del self.extra_fields[key]

    def clear_extra_fields(self) -> None:
        """پاک کردن تمام فیلدهای اضافی."""
        self.extra_fields.clear()

    def format_exception(self, exc_info: Any) -> str:
        """
        فرمت‌سازی استثنا برای خروجی JSON.

        Args:
            exc_info: اطلاعات استثنا.

        Returns:
            رشته‌ی فرمت‌شده‌ی استثنا.
        """
        return self.formatException(exc_info)

    def get_formatted_record(self, record: logging.LogRecord) -> Dict[str, Any]:
        """
        دریافت دیکشنری فرمت‌شده از رکورد لاگ (برای استفاده در JSON).

        Args:
            record: رکورد لاگ.

        Returns:
            دیکشنری شامل اطلاعات لاگ.
        """
        return json.loads(self._format_json(record))

    def set_format(self, fmt: str) -> None:
        """
        تنظیم فرمت جدید برای لاگ‌ها.

        Args:
            fmt: فرمت جدید.
        """
        self._fmt = fmt
        self._style = logging.PercentStyle(fmt)

    def set_date_format(self, datefmt: str) -> None:
        """
        تنظیم فرمت جدید برای تاریخ و زمان.

        Args:
            datefmt: فرمت جدید تاریخ.
        """
        self.datefmt = datefmt


# تابع کمکی برای ایجاد فرمتر پیش‌فرض
def create_default_formatter(
    use_json: bool = False,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> LogFormatter:
    """
    ایجاد یک فرمتر با تنظیمات پیش‌فرض.

    Args:
        use_json: فعال‌سازی خروجی JSON.
        extra_fields: فیلدهای اضافی (اختیاری).

    Returns:
        نمونه‌ی LogFormatter با تنظیمات پیش‌فرض.
    """
    return LogFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        use_json=use_json,
        extra_fields=extra_fields,
    )


# تابع کمکی برای ایجاد فرمتر مختص خطاها
def create_error_formatter(
    use_json: bool = False,
) -> LogFormatter:
    """
    ایجاد یک فرمتر با جزئیات بیشتر برای لاگ‌های خطا.

    Args:
        use_json: فعال‌سازی خروجی JSON.

    Returns:
        نمونه‌ی LogFormatter با جزئیات بیشتر.
    """
    return LogFormatter(
        fmt=(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s\n"
            "File: %(pathname)s, Line: %(lineno)d, Function: %(funcName)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        use_json=use_json,
    )


__all__ = [
    "LogFormatter",
    "create_default_formatter",
    "create_error_formatter",
]