# my_bot_project/src/my_bot/core/exceptions/db_errors.py
"""
استثناهای مربوط به دیتابیس (Database Errors).

این ماژول شامل کلاس‌های استثنایی است که در زمان ارتباط با دیتابیس،
اجرای کوئری‌ها، مدیریت تراکنش‌ها و سایر عملیات‌های دیتابیسی رخ می‌دهند.
"""

from typing import Any, Dict, Optional

from my_bot.core.exceptions.base import MyBotError


class DatabaseError(MyBotError):
    """
    خطای عمومی مربوط به دیتابیس.

    این استثنا زمانی رخ می‌دهد که مشکلی در ارتباط با دیتابیس،
    اجرای کوئری یا سایر عملیات‌های دیتابیسی وجود داشته باشد.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای دیتابیس.

        Args:
            message: پیام خطا.
            error_code: کد خطای اختیاری (پیش‌فرض: 'DB_ERROR').
            context: اطلاعات زمینه‌ای اضافی.
        """
        if error_code is None:
            error_code = "DB_ERROR"
        super().__init__(message, error_code, context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "مشکلی در ارتباط با پایگاه داده وجود دارد. لطفاً دوباره تلاش کنید."


class ConnectionError(DatabaseError):
    """
    خطای اتصال به دیتابیس.

    این استثنا زمانی رخ می‌دهد که امکان برقراری اتصال به دیتابیس وجود نداشته باشد.
    """

    def __init__(
        self,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای اتصال.

        Args:
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = "خطا در برقراری اتصال به پایگاه داده."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="DB_CONNECTION_ERROR", context=context)


class QueryError(DatabaseError):
    """
    خطای اجرای کوئری.

    این استثنا زمانی رخ می‌دهد که اجرای یک کوئری با خطا مواجه شود.
    """

    def __init__(
        self,
        query: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای کوئری.

        Args:
            query: متن کوئری که با خطا مواجه شده است.
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در اجرای کوئری دیتابیس."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["query"] = query[:500]  # محدود کردن طول کوئری برای جلوگیری از حجم زیاد
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="DB_QUERY_ERROR", context=context)


class IntegrityError(DatabaseError):
    """
    خطای یکپارچگی داده‌ها.

    این استثنا زمانی رخ می‌دهد که عملیات دیتابیسی با محدودیت‌های یکپارچگی
    (مانند کلید خارجی، کلید یکتا، NOT NULL و ...) در تضاد باشد.
    """

    def __init__(
        self,
        table: str,
        field: Optional[str] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای یکپارچگی داده‌ها.

        Args:
            table: نام جدول مربوطه.
            field: نام فیلد مربوطه (اختیاری).
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطای یکپارچگی داده‌ها در جدول '{table}'."
        if field:
            message += f" فیلد: '{field}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["table"] = table
        if field:
            context["field"] = field
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="DB_INTEGRITY_ERROR", context=context)


class DuplicateEntryError(IntegrityError):
    """
    خطای ورود تکراری.

    این استثنا زمانی رخ می‌دهد که تلاش برای درج یک رکورد تکراری
    (با کلید یکتا یا کلید اصلی تکراری) انجام شود.
    """

    def __init__(
        self,
        table: str,
        field: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای ورود تکراری.

        Args:
            table: نام جدول مربوطه.
            field: نام فیلد با مقدار تکراری.
            value: مقدار تکراری.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"رکورد تکراری در جدول '{table}' با فیلد '{field}' و مقدار '{value}'."

        context = context or {}
        context["table"] = table
        context["field"] = field
        context["value"] = str(value)

        super().__init__(
            message=message,
            context=context,
        )
        # تغییر کد خطا
        self.error_code = "DB_DUPLICATE_ENTRY"


class TransactionError(DatabaseError):
    """
    خطای تراکنش دیتابیس.

    این استثنا زمانی رخ می‌دهد که مشکلی در شروع، commit یا rollback تراکنش وجود داشته باشد.
    """

    def __init__(
        self,
        operation: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای تراکنش.

        Args:
            operation: نوع عملیات (begin, commit, rollback).
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در عملیات تراکنش '{operation}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["operation"] = operation
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="DB_TRANSACTION_ERROR", context=context)


class MigrationError(DatabaseError):
    """
    خطای مایگریشن دیتابیس.

    این استثنا زمانی رخ می‌دهد که مشکلی در اجرای مایگریشن‌ها وجود داشته باشد.
    """

    def __init__(
        self,
        migration_id: Optional[str] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای مایگریشن.

        Args:
            migration_id: شناسه مایگریشن (اختیاری).
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = "خطا در اجرای مایگریشن دیتابیس."
        if migration_id:
            message += f" مایگریشن: '{migration_id}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        if migration_id:
            context["migration_id"] = migration_id
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="DB_MIGRATION_ERROR", context=context)


class PoolError(DatabaseError):
    """
    خطای Connection Pool دیتابیس.

    این استثنا زمانی رخ می‌دهد که مشکلی در Connection Pool
    (مانند تمام شدن اتصالات، timeout و ...) وجود داشته باشد.
    """

    def __init__(
        self,
        operation: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای Connection Pool.

        Args:
            operation: نوع عملیات (get_connection, release_connection, etc).
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در Connection Pool هنگام عملیات '{operation}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["operation"] = operation
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="DB_POOL_ERROR", context=context)


__all__ = [
    "DatabaseError",
    "ConnectionError",
    "QueryError",
    "IntegrityError",
    "DuplicateEntryError",
    "TransactionError",
    "MigrationError",
    "PoolError",
]