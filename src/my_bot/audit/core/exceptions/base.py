# my_bot_project/src/my_bot/core/exceptions/base.py
"""
کلاس پایه استثناهای سفارشی (Base Exception).

این ماژول شامل کلاس `MyBotError` است که به‌عنوان کلاس پایه برای تمام
استثناهای سفارشی پروژه عمل می‌کند. این کلاس قابلیت ذخیره‌سازی پیام خطا،
کد خطا و اطلاعات زمینه‌ای (context) را دارد.
"""

from typing import Any, Dict, Optional


class MyBotError(Exception):
    """
    کلاس پایه برای تمام استثناهای سفارشی پروژه.

    این کلاس از `Exception` ارث‌بری می‌کند و امکانات زیر را فراهم می‌کند:
        - ذخیره‌سازی پیام خطا (message)
        - ذخیره‌سازی کد خطای اختیاری (error_code)
        - ذخیره‌سازی اطلاعات زمینه‌ای اضافی (context)
        - متدهایی برای تبدیل خطا به رشته و دریافت اطلاعات کامل

    Attributes:
        message: پیام خطای قابل نمایش به کاربر یا توسعه‌دهنده.
        error_code: کد عددی یا رشته‌ای برای شناسایی نوع خطا (اختیاری).
        context: دیکشنری حاوی اطلاعات اضافی برای دیباگ (اختیاری).
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنا.

        Args:
            message: پیام خطا.
            error_code: کد خطای اختیاری برای شناسایی نوع خطا.
            context: اطلاعات زمینه‌ای اضافی (مثلاً شناسه کاربر، داده‌های مربوطه).
        """
        self.message = message
        self.error_code = error_code
        self.context = context or {}

        # فراخوانی سازنده کلاس پایه با پیام
        super().__init__(message)

    def __str__(self) -> str:
        """
        نمایش رشته‌ای از خطا.

        Returns:
            رشته شامل پیام خطا و (در صورت وجود) کد خطا.
        """
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل استثنا به دیکشنری برای استفاده در لاگ‌ها یا پاسخ‌های API.

        Returns:
            دیکشنری شامل اطلاعات کامل خطا.
        """
        result: Dict[str, Any] = {
            "error": self.message,
            "type": self.__class__.__name__,
        }
        if self.error_code:
            result["code"] = self.error_code
        if self.context:
            result["context"] = self.context
        return result

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        این متد در کلاس‌های فرزند می‌تواند بازنویسی شود تا پیام‌های
        کاربرپسندتری ارائه دهد.

        Returns:
            پیام خطای قابل نمایش به کاربر.
        """
        # پیام پایه، در فرزندان می‌تواند سفارشی‌سازی شود
        return self.message