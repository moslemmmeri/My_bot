# my_bot_project/src/my_bot/shared/utils/message_pool.py
"""
بانک پیام‌های تصادفی (Message Pool).

این ماژول شامل کلاس `MessagePool` است که پیام‌های تصادفی و حرفه‌ای
را برای جلوگیری از خستگی کاربر در تعاملات مختلف فراهم می‌کند.
پیام‌ها در دسته‌بندی‌های مختلف مانند خوش‌آمدگویی، خداحافظی،
تأیید فرم، خطا و ... سازماندهی شده‌اند.
"""

import random
from typing import List, Optional


class MessagePool:
    """
    بانک پیام‌های تصادفی برای استفاده در تعاملات با کاربر.

    این کلاس شامل دسته‌بندی‌های مختلف پیام است و متدهایی برای
    دریافت پیام‌های تصادفی از هر دسته فراهم می‌کند.
    """

    # ==========================================
    # دسته‌بندی پیام‌های خوش‌آمدگویی
    # ==========================================
    GREETINGS = [
        "👋 سلام! خوش اومدی!",
        "😊 درود بر تو!",
        "🌟 خوش‌آمدی! چطور می‌تونم کمکت کنم؟",
        "🤗 سلام دوباره!",
        "🎉 سلام! به جمع ما خوش آمدی!",
        "👋 سلام! از دیدنت خوشحالم!",
        "😍 سلام! چطور هستی؟",
        "💫 درود! خوش آمدی به ربات ما!",
        "🌸 سلام! روز خوبی داری؟",
        "🌺 درود بر تو! خوش آمدی!",
    ]

    # ==========================================
    # دسته‌بندی پیام‌های خوش‌آمدگویی مجدد
    # ==========================================
    WELCOME_BACK = [
        "😊 خوش برگشتی! دوباره دیدمت!",
        "🌟 باز هم به ما سر زدی! خوش آمدی!",
        "👋 سلام دوباره! چطور بودی؟",
        "🎉 خوش برگشتی! منتظرت بودیم!",
        "💫 به ربات ما خوش برگشتی!",
        "🌸 خوش آمدی! امیدوارم خسته نباشی!",
        "🌺 سلام دوباره! وقت خوش!",
    ]

    # ==========================================
    # دسته‌بندی پیام‌های تأیید فرم
    # ==========================================
    FORM_COMPLETED = [
        "✅ فرم با موفقیت ثبت شد.",
        "📝 اطلاعات شما ذخیره گردید.",
        "🎉 عالی! فرم تکمیل شد.",
        "👍 ثبت شد! از مشارکت شما سپاسگزاریم.",
        "🙏 فرم شما با موفقیت ارسال شد.",
        "✨ ثبت اطلاعات شما انجام شد.",
        "💯 فرم شما تکمیل و ارسال شد.",
        "✅ پاسخ شما با موفقیت ثبت شد.",
        "🎊 تبریک! فرم شما ثبت شد.",
    ]

    # ==========================================
    # دسته‌بندی پیام‌های تأیید سفارش
    # ==========================================
    ORDER_COMPLETED = [
        "✅ سفارش شما با موفقیت ثبت شد.",
        "🛒 سفارش شما ثبت گردید.",
        "🎉 عالی! سفارش شما ثبت شد.",
        "👍 ثبت سفارش انجام شد.",
        "🙏 از اعتماد شما سپاسگزاریم.",
        "✨ سفارش شما در صف پردازش قرار گرفت.",
        "💯 سفارش شما با موفقیت ثبت شد.",
        "🛍️ سفارش شما ثبت و تایید شد.",
    ]

    # ==========================================
    # دسته‌بندی پیام‌های پرداخت موفق
    # ==========================================
    PAYMENT_SUCCESS = [
        "✅ پرداخت با موفقیت انجام شد.",
        "💰 پرداخت شما تایید شد.",
        "🎉 پرداخت موفق! از خرید شما متشکریم.",
        "👍 پرداخت انجام شد. سفارش شما در حال پردازش است.",
        "💳 پرداخت شما با موفقیت انجام شد.",
        "✨ پرداخت شما تایید شد. به‌زودی سفارش ارسال می‌شود.",
        "🎊 پرداخت موفق! از شما سپاسگزاریم.",
        "✅ پرداخت شما انجام شد. کد رهگیری برای شما ارسال می‌شود.",
    ]

    # ==========================================
    # دسته‌بندی پیام‌های پرداخت ناموفق
    # ==========================================
    PAYMENT_FAILED = [
        "❌ پرداخت ناموفق بود. لطفاً دوباره تلاش کنید.",
        "⚠️ پرداخت با خطا مواجه شد. اطلاعات کارت را بررسی کنید.",
        "🔴 پرداخت انجام نشد. لطفاً دوباره امتحان کنید.",
        "💔 متأسفانه پرداخت ناموفق بود.",
        "❌ خطا در پرداخت. لطفاً با پشتیبانی تماس بگیرید.",
    ]

    # ==========================================
    # دسته‌بندی پیام‌های لغو عملیات
    # ==========================================
    CANCELLATION = [
        "❌ عملیات لغو شد.",
        "🚫 انصراف انجام شد.",
        "⛔ عملیات کنسل شد.",
        "❌ شما عملیات را لغو کردید.",
        "🚫 لغو شد. در صورت نیاز دوباره تلاش کنید.",
    ]

    # ==========================================
    # دسته‌بندی پیام‌های خطا
    # ==========================================
    ERRORS = [
        "⚠️ متأسفانه خطایی رخ داده است. لطفاً دوباره تلاش کنید.",
        "❌ خطا! لطفاً دوباره امتحان کنید.",
        "🔴 خطایی رخ داد. در صورت تکرار با پشتیبانی تماس بگیرید.",
        "💔 متأسفانه عملیات با خطا مواجه شد.",
        "⚠️ خطا! لطفاً اطلاعات را بررسی کنید.",
    ]

    # ==========================================
    # دسته‌بندی پیام‌های در حال پردازش
    # ==========================================
    PROCESSING = [
        "⏳ در حال پردازش... لطفاً منتظر بمانید.",
        "🔄 در حال انجام عملیات...",
        "⏳ لطفاً صبر کنید...",
        "⚙️ در حال پردازش درخواست شما...",
        "🔄 عملیات در حال انجام است...",
    ]

    # ==========================================
    # دسته‌بندی پیام‌های خداحافظی
    # ==========================================
    FAREWELLS = [
        "👋 خداحافظ! روز خوبی داشته باشید.",
        "😊 خداحافظ! به امید دیدار دوباره.",
        "🌟 خداحافظ! منتظر شما هستیم.",
        "🌸 خداحافظ! موفق و پیروز باشید.",
        "🌺 خداحافظ! خوشحال بودیم که بودید.",
    ]

    # ==========================================
    # متدهای عمومی
    # ==========================================

    @classmethod
    def get_random_greeting(cls) -> str:
        """
        دریافت یک پیام خوش‌آمدگویی تصادفی.

        Returns:
            str: پیام خوش‌آمدگویی.
        """
        return random.choice(cls.GREETINGS)

    @classmethod
    def get_random_welcome_back(cls) -> str:
        """
        دریافت یک پیام خوش‌آمدگویی مجدد تصادفی.

        Returns:
            str: پیام خوش‌آمدگویی مجدد.
        """
        return random.choice(cls.WELCOME_BACK)

    @classmethod
    def get_random_form_completed(cls) -> str:
        """
        دریافت یک پیام تأیید فرم تصادفی.

        Returns:
            str: پیام تأیید فرم.
        """
        return random.choice(cls.FORM_COMPLETED)

    @classmethod
    def get_random_order_completed(cls) -> str:
        """
        دریافت یک پیام تأیید سفارش تصادفی.

        Returns:
            str: پیام تأیید سفارش.
        """
        return random.choice(cls.ORDER_COMPLETED)

    @classmethod
    def get_random_payment_success(cls) -> str:
        """
        دریافت یک پیام پرداخت موفق تصادفی.

        Returns:
            str: پیام پرداخت موفق.
        """
        return random.choice(cls.PAYMENT_SUCCESS)

    @classmethod
    def get_random_payment_failed(cls) -> str:
        """
        دریافت یک پیام پرداخت ناموفق تصادفی.

        Returns:
            str: پیام پرداخت ناموفق.
        """
        return random.choice(cls.PAYMENT_FAILED)

    @classmethod
    def get_random_cancellation(cls) -> str:
        """
        دریافت یک پیام لغو عملیات تصادفی.

        Returns:
            str: پیام لغو عملیات.
        """
        return random.choice(cls.CANCELLATION)

    @classmethod
    def get_random_error(cls) -> str:
        """
        دریافت یک پیام خطا تصادفی.

        Returns:
            str: پیام خطا.
        """
        return random.choice(cls.ERRORS)

    @classmethod
    def get_random_processing(cls) -> str:
        """
        دریافت یک پیام در حال پردازش تصادفی.

        Returns:
            str: پیام در حال پردازش.
        """
        return random.choice(cls.PROCESSING)

    @classmethod
    def get_random_farewell(cls) -> str:
        """
        دریافت یک پیام خداحافظی تصادفی.

        Returns:
            str: پیام خداحافظی.
        """
        return random.choice(cls.FAREWELLS)

    @classmethod
    def get_message(cls, category: str) -> str:
        """
        دریافت یک پیام تصادفی از دسته‌بندی مشخص.

        Args:
            category: نام دسته‌بندی (greeting, welcome_back, form_completed, ...).

        Returns:
            str: پیام تصادفی از دسته‌بندی.

        Raises:
            ValueError: اگر دسته‌بندی وجود نداشته باشد.
        """
        category_map = {
            "greeting": cls.GREETINGS,
            "welcome_back": cls.WELCOME_BACK,
            "form_completed": cls.FORM_COMPLETED,
            "order_completed": cls.ORDER_COMPLETED,
            "payment_success": cls.PAYMENT_SUCCESS,
            "payment_failed": cls.PAYMENT_FAILED,
            "cancellation": cls.CANCELLATION,
            "error": cls.ERRORS,
            "processing": cls.PROCESSING,
            "farewell": cls.FAREWELLS,
        }

        pool = category_map.get(category)
        if not pool:
            raise ValueError(f"دسته‌بندی '{category}' وجود ندارد.")

        return random.choice(pool)

    @classmethod
    def get_custom_message(cls, category: str, messages: List[str]) -> str:
        """
        دریافت یک پیام تصادفی از لیست سفارشی.

        Args:
            category: نام دسته‌بندی برای ذخیره (اختیاری).
            messages: لیست پیام‌های سفارشی.

        Returns:
            str: پیام تصادفی از لیست.
        """
        if not messages:
            return ""

        # اگر دسته‌بندی معتبر است، به مجموعه اضافه می‌کنیم
        if hasattr(cls, category.upper()):
            setattr(cls, category.upper(), messages)

        return random.choice(messages)

    @classmethod
    def add_messages(cls, category: str, messages: List[str]) -> None:
        """
        افزودن پیام‌های جدید به یک دسته‌بندی موجود.

        Args:
            category: نام دسته‌بندی.
            messages: لیست پیام‌های جدید.

        Raises:
            ValueError: اگر دسته‌بندی وجود نداشته باشد.
        """
        attr_name = category.upper()
        if not hasattr(cls, attr_name):
            raise ValueError(f"دسته‌بندی '{category}' وجود ندارد.")

        current = getattr(cls, attr_name)
        if isinstance(current, list):
            setattr(cls, attr_name, current + messages)

    @classmethod
    def get_all_categories(cls) -> List[str]:
        """
        دریافت لیست تمام دسته‌بندی‌های موجود.

        Returns:
            List[str]: لیست نام دسته‌بندی‌ها.
        """
        categories = [
            "greeting",
            "welcome_back",
            "form_completed",
            "order_completed",
            "payment_success",
            "payment_failed",
            "cancellation",
            "error",
            "processing",
            "farewell",
        ]
        return categories

    @classmethod
    def get_category_size(cls, category: str) -> int:
        """
        دریافت تعداد پیام‌های موجود در یک دسته‌بندی.

        Args:
            category: نام دسته‌بندی.

        Returns:
            int: تعداد پیام‌ها.

        Raises:
            ValueError: اگر دسته‌بندی وجود نداشته باشد.
        """
        attr_name = category.upper()
        if not hasattr(cls, attr_name):
            raise ValueError(f"دسته‌بندی '{category}' وجود ندارد.")

        return len(getattr(cls, attr_name))