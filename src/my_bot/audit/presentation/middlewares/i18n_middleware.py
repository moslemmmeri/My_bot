# my_bot_project/src/my_bot/presentation/middlewares/i18n_middleware.py
"""
میدلور چندزبانی (I18n Middleware).

این میدلور مسئولیت تشخیص زبان کاربر، بارگذاری ترجمه‌های مناسب
و در دسترس قرار دادن آنها در context برای استفاده در هندلرها را بر عهده دارد.
پشتیبانی از زبان‌های فارسی و انگلیسی با قابلیت توسعه به زبان‌های دیگر.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Awaitable, Union
from functools import lru_cache

from aiogram import BaseMiddleware
from aiogram.types import Update, User
from aiogram.types import Message, CallbackQuery

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.validation_errors import ValidationError

logger = get_logger(__name__)


class I18nMiddleware(BaseMiddleware):
    """
    میدلور چندزبانی با پشتیبانی از کش ترجمه‌ها.

    این میدلور زبان کاربر را تشخیص داده، ترجمه‌های مربوطه را بارگذاری
    و یک شیء ترجمه در context قرار می‌دهد.

    Attributes:
        default_language: زبان پیش‌فرض (پیش‌فرض: 'fa').
        translations_path: مسیر دایرکتوری فایل‌های ترجمه.
        supported_languages: لیست زبان‌های پشتیبانی‌شده.
        _translations_cache: کش ترجمه‌ها برای افزایش سرعت.
        _user_languages: ذخیره زبان کاربران (اختیاری).
    """

    def __init__(
        self,
        default_language: str = "fa",
        translations_path: Optional[Union[str, Path]] = None,
        supported_languages: Optional[list[str]] = None,
        cache_size: int = 100,
    ) -> None:
        """
        مقداردهی اولیه میدلور.

        Args:
            default_language: زبان پیش‌فرض (پیش‌فرض: 'fa').
            translations_path: مسیر دایرکتوری فایل‌های ترجمه.
            supported_languages: لیست زبان‌های پشتیبانی‌شده.
            cache_size: حداکثر تعداد ترجمه‌های کش‌شده.
        """
        super().__init__()
        self.default_language = default_language
        self.supported_languages = supported_languages or ["fa", "en"]

        # تنظیم مسیر ترجمه‌ها
        if translations_path is None:
            # مسیر پیش‌فرض: src/my_bot/shared/i18n/translations/
            base_dir = Path(__file__).parent.parent.parent
            translations_path = base_dir / "shared" / "i18n" / "translations"
        elif isinstance(translations_path, str):
            translations_path = Path(translations_path)

        self.translations_path = translations_path

        # کش ترجمه‌ها
        self._translations_cache: Dict[str, Dict[str, str]] = {}
        self._cache_size = cache_size

        # ذخیره زبان کاربران (برای استفاده در جلسات بعدی)
        self._user_languages: Dict[int, str] = {}

        # بارگذاری ترجمه‌های پیش‌فرض
        self._load_translations()

        logger.info(
            f"I18nMiddleware initialized: default_language={default_language}, "
            f"supported={self.supported_languages}, translations_path={translations_path}"
        )

    def _load_translations(self) -> None:
        """
        بارگذاری تمام فایل‌های ترجمه از دایرکتوری مشخص‌شده.
        """
        if not self.translations_path.exists():
            logger.warning(f"Translations directory not found: {self.translations_path}")
            # ایجاد دایرکتوری در صورت نیاز
            try:
                self.translations_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created translations directory: {self.translations_path}")
            except Exception as e:
                logger.error(f"Failed to create translations directory: {e}")

        # بارگذاری فایل‌های ترجمه برای هر زبان
        for lang in self.supported_languages:
            lang_file = self.translations_path / f"{lang}.json"
            try:
                if lang_file.exists():
                    with open(lang_file, "r", encoding="utf-8") as f:
                        translations = json.load(f)
                    self._translations_cache[lang] = translations
                    logger.debug(f"Loaded translations for language: {lang}")
                else:
                    # ایجاد فایل خالی برای زبان
                    self._translations_cache[lang] = {}
                    logger.warning(f"Translation file not found: {lang_file}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in translation file {lang_file}: {e}")
                self._translations_cache[lang] = {}
            except Exception as e:
                logger.error(f"Error loading translations for {lang}: {e}")
                self._translations_cache[lang] = {}

        # اطمینان از وجود زبان پیش‌فرض
        if self.default_language not in self._translations_cache:
            self._translations_cache[self.default_language] = {}

        logger.info(
            f"Loaded translations for {len(self._translations_cache)} languages: "
            f"{list(self._translations_cache.keys())}"
        )

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        """
        پردازش ورودی و افزودن ترجمه به context.

        Args:
            handler: هندلر بعدی در زنجیره.
            event: رویداد دریافتی از تلگرام.
            data: داده‌های زمینه (Context Data).

        Returns:
            Any: نتیجه پردازش توسط هندلر بعدی.
        """
        # تشخیص زبان کاربر
        user = self._get_user_from_event(event)
        language = self._get_user_language(user)

        # ایجاد شیء ترجمه
        translator = self._create_translator(language)

        # افزودن به context
        data["i18n"] = translator
        data["language"] = language

        # ادامه پردازش
        return await handler(event, data)

    def _get_user_from_event(self, event: Update) -> Optional[User]:
        """
        استخراج کاربر از رویداد.

        Args:
            event: رویداد دریافتی.

        Returns:
            Optional[User]: کاربر یا None در صورت عدم وجود.
        """
        if event.message and event.message.from_user:
            return event.message.from_user
        if event.callback_query and event.callback_query.from_user:
            return event.callback_query.from_user
        if event.inline_query and event.inline_query.from_user:
            return event.inline_query.from_user
        if event.chosen_inline_result and event.chosen_inline_result.from_user:
            return event.chosen_inline_result.from_user
        return None

    def _get_user_language(self, user: Optional[User]) -> str:
        """
        تشخیص زبان کاربر.

        استراتژی تشخیص:
        1. زبان ذخیره‌شده برای کاربر (در صورت وجود)
        2. زبان کاربر تلگرام (language_code)
        3. زبان پیش‌فرض

        Args:
            user: کاربر (اختیاری).

        Returns:
            str: کد زبان (مثلاً 'fa' یا 'en').
        """
        if not user:
            return self.default_language

        user_id = user.id

        # بررسی زبان ذخیره‌شده برای کاربر
        if user_id in self._user_languages:
            stored_lang = self._user_languages[user_id]
            if stored_lang in self.supported_languages:
                return stored_lang

        # بررسی زبان کاربر تلگرام
        if hasattr(user, "language_code") and user.language_code:
            lang_code = user.language_code[:2].lower()
            if lang_code in self.supported_languages:
                # ذخیره برای استفاده بعدی
                self._user_languages[user_id] = lang_code
                return lang_code

            # زبان نزدیک (مثلاً 'en' برای 'en-US')
            if lang_code:
                # تلاش برای تطابق با زبان‌های پشتیبانی‌شده
                for supported in self.supported_languages:
                    if lang_code.startswith(supported):
                        self._user_languages[user_id] = supported
                        return supported

        # بازگشت به زبان پیش‌فرض
        return self.default_language

    def set_user_language(self, user_id: int, language: str) -> None:
        """
        تنظیم زبان برای یک کاربر خاص.

        Args:
            user_id: شناسه کاربر.
            language: کد زبان (مثلاً 'fa' یا 'en').

        Raises:
            ValidationError: اگر زبان پشتیبانی نشود.
        """
        if language not in self.supported_languages:
            raise ValidationError(
                message=f"زبان '{language}' پشتیبانی نمی‌شود.",
                context={"language": language, "supported": self.supported_languages},
            )

        self._user_languages[user_id] = language
        logger.debug(f"Language for user {user_id} set to {language}")

    def get_user_language(self, user_id: int) -> Optional[str]:
        """
        دریافت زبان یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Optional[str]: کد زبان یا None در صورت عدم وجود.
        """
        return self._user_languages.get(user_id)

    def _create_translator(self, language: str) -> "Translator":
        """
        ایجاد یک شیء ترجمه برای زبان مشخص.

        Args:
            language: کد زبان.

        Returns:
            Translator: شیء ترجمه.
        """
        # دریافت ترجمه‌های زبان (با Fallback به زبان پیش‌فرض)
        translations = self._translations_cache.get(language, {})
        default_translations = self._translations_cache.get(self.default_language, {})

        # ترکیب ترجمه‌ها (ترجمه‌های زبان اولویت دارند)
        merged_translations = default_translations.copy()
        merged_translations.update(translations)

        return Translator(
            language=language,
            translations=merged_translations,
            default_language=self.default_language,
        )

    def get_translation(self, key: str, language: Optional[str] = None) -> str:
        """
        دریافت یک ترجمه برای کلید مشخص.

        Args:
            key: کلید ترجمه (با فرمت 'section.key').
            language: کد زبان (اختیاری، در صورت None از زبان پیش‌فرض استفاده می‌شود).

        Returns:
            str: متن ترجمه‌شده.
        """
        lang = language or self.default_language
        translations = self._translations_cache.get(lang, {})
        default_translations = self._translations_cache.get(self.default_language, {})

        # جستجو در ترجمه‌های زبان
        if key in translations:
            return translations[key]

        # جستجو در ترجمه‌های پیش‌فرض
        if key in default_translations:
            return default_translations[key]

        # اگر ترجمه پیدا نشد، کلید را برگردان
        logger.warning(f"Translation key not found: {key} for language {lang}")
        return key

    def get_all_translations(self, language: Optional[str] = None) -> Dict[str, str]:
        """
        دریافت تمام ترجمه‌های یک زبان.

        Args:
            language: کد زبان (اختیاری).

        Returns:
            Dict[str, str]: دیکشنری تمام ترجمه‌ها.
        """
        lang = language or self.default_language
        translations = self._translations_cache.get(lang, {})
        default_translations = self._translations_cache.get(self.default_language, {})

        # ترکیب ترجمه‌ها
        merged = default_translations.copy()
        merged.update(translations)
        return merged

    async def reload_translations(self) -> None:
        """
        بارگذاری مجدد ترجمه‌ها (برای استفاده در زمان توسعه یا تغییر فایل‌ها).
        """
        self._translations_cache.clear()
        self._load_translations()
        logger.info("Translations reloaded")

    def add_translation(self, key: str, value: str, language: str) -> None:
        """
        افزودن یا به‌روزرسانی یک ترجمه.

        Args:
            key: کلید ترجمه.
            value: متن ترجمه‌شده.
            language: کد زبان.

        Raises:
            ValidationError: اگر زبان پشتیبانی نشود.
        """
        if language not in self.supported_languages:
            raise ValidationError(
                message=f"زبان '{language}' پشتیبانی نمی‌شود.",
                context={"language": language, "supported": self.supported_languages},
            )

        if language not in self._translations_cache:
            self._translations_cache[language] = {}

        self._translations_cache[language][key] = value

        # ذخیره در فایل (اختیاری)
        self._save_translation_file(language)

        logger.debug(f"Translation added: {key}={value} for {language}")

    def _save_translation_file(self, language: str) -> None:
        """
        ذخیره ترجمه‌های یک زبان در فایل.

        Args:
            language: کد زبان.
        """
        lang_file = self.translations_path / f"{language}.json"
        try:
            translations = self._translations_cache.get(language, {})
            with open(lang_file, "w", encoding="utf-8") as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved translations for {language} to {lang_file}")
        except Exception as e:
            logger.error(f"Failed to save translations for {language}: {e}")

    def get_supported_languages(self) -> list[str]:
        """
        دریافت لیست زبان‌های پشتیبانی‌شده.

        Returns:
            list[str]: لیست کدهای زبان.
        """
        return self.supported_languages.copy()

    def get_language_name(self, language: str) -> str:
        """
        دریافت نام نمایشی یک زبان.

        Args:
            language: کد زبان.

        Returns:
            str: نام نمایشی زبان.
        """
        names = {
            "fa": "فارسی",
            "en": "English",
        }
        return names.get(language, language)


class Translator:
    """
    کلاس ترجمه برای استفاده در هندلرها.

    این کلاس یک رابط ساده برای دسترسی به ترجمه‌ها فراهم می‌کند
    و امکان استفاده از placeholderها را نیز دارد.

    Attributes:
        language: کد زبان فعلی.
        translations: دیکشنری ترجمه‌ها.
        default_language: زبان پیش‌فرض.
    """

    def __init__(
        self,
        language: str,
        translations: Dict[str, str],
        default_language: str,
    ) -> None:
        """
        مقداردهی اولیه ترجمه.

        Args:
            language: کد زبان فعلی.
            translations: دیکشنری ترجمه‌ها.
            default_language: زبان پیش‌فرض.
        """
        self.language = language
        self._translations = translations
        self.default_language = default_language

    def gettext(self, key: str, **kwargs) -> str:
        """
        دریافت ترجمه با قابلیت جایگزینی placeholderها.

        Args:
            key: کلید ترجمه.
            **kwargs: placeholderها برای جایگزینی (مثلاً name='علی').

        Returns:
            str: متن ترجمه‌شده با جایگزینی placeholderها.

        Example:
            translator.gettext("welcome", name="علی")
            # اگر ترجمه "welcome": "خوش آمدید {name}" باشد، خروجی: "خوش آمدید علی"
        """
        # دریافت ترجمه
        text = self._translations.get(key, key)

        # جایگزینی placeholderها
        if kwargs:
            for placeholder, value in kwargs.items():
                text = text.replace(f"{{{placeholder}}}", str(value))

        return text

    def __call__(self, key: str, **kwargs) -> str:
        """
        امکان استفاده به‌صورت تابع.

        Args:
            key: کلید ترجمه.
            **kwargs: placeholderها.

        Returns:
            str: متن ترجمه‌شده.
        """
        return self.gettext(key, **kwargs)

    def __getitem__(self, key: str) -> str:
        """
        دسترسی به ترجمه با استفاده از براکت (مانند دیکشنری).

        Args:
            key: کلید ترجمه.

        Returns:
            str: متن ترجمه‌شده.
        """
        return self._translations.get(key, key)

    def get_language_name(self) -> str:
        """
        دریافت نام نمایشی زبان فعلی.

        Returns:
            str: نام نمایشی زبان.
        """
        names = {
            "fa": "فارسی",
            "en": "English",
        }
        return names.get(self.language, self.language)

    def has_key(self, key: str) -> bool:
        """
        بررسی وجود یک کلید ترجمه.

        Args:
            key: کلید ترجمه.

        Returns:
            bool: True اگر کلید وجود داشته باشد.
        """
        return key in self._translations

    def get_all_keys(self) -> list[str]:
        """
        دریافت تمام کلیدهای ترجمه.

        Returns:
            list[str]: لیست کلیدها.
        """
        return list(self._translations.keys())


# ----------------------------------------------
# تابع کمکی برای ایجاد ترجمه‌های پیش‌فرض
# ----------------------------------------------

def create_default_translations() -> Dict[str, Dict[str, str]]:
    """
    ایجاد ترجمه‌های پیش‌فرض برای زبان‌های فارسی و انگلیسی.

    Returns:
        Dict[str, Dict[str, str]]: دیکشنری ترجمه‌ها.
    """
    return {
        "fa": {
            # عمومی
            "welcome": "خوش آمدید {name} 👋",
            "welcome_back": "خوش برگشتید {name} 😊",
            "back": "بازگشت",
            "cancel": "انصراف",
            "confirm": "تأیید",
            "yes": "بله",
            "no": "خیر",
            "loading": "در حال بارگذاری...",
            "error": "خطا",
            "success": "موفق",
            "done": "انجام شد",

            # منوی اصلی
            "main_menu": "🏠 منوی اصلی",
            "forms": "📋 فرم‌ها",
            "profile": "👤 پروفایل",
            "contact_us": "📞 تماس با ما",
            "help": "❓ راهنما",
            "admin_panel": "⚙️ پنل مدیریت",

            # فرم‌ها
            "forms_list": "📋 لیست فرم‌ها",
            "start_form": "شروع فرم",
            "form_step": "مرحله {step} از {total}",
            "submit_form": "ارسال فرم",
            "form_submitted": "✅ فرم با موفقیت ارسال شد!",
            "form_cancelled": "❌ پر کردن فرم لغو شد.",

            # پروفایل
            "profile_info": "👤 اطلاعات پروفایل",
            "points": "⭐ امتیاز",
            "level": "🏅 سطح",
            "orders": "🛒 سفارشات",
            "no_orders": "هیچ سفارشی یافت نشد.",
            "edit_profile": "✏️ ویرایش پروفایل",

            # راهنما
            "help_menu": "❓ راهنمای کاربر",
            "faq": "❔ سوالات متداول",
            "full_guide": "📖 راهنمای کامل",

            # تماس
            "contact_info": "📞 اطلاعات تماس",

            # خطاها
            "permission_denied": "⛔ شما دسترسی به این بخش را ندارید.",
            "not_found": "⚠️ مورد درخواستی یافت نشد.",
            "invalid_input": "⚠️ ورودی نامعتبر است.",
            "rate_limit": "⏳ تعداد درخواست‌های شما بیش از حد مجاز است.",

            # پرداخت
            "payment": "💳 پرداخت",
            "payment_initiated": "پرداخت با موفقیت شروع شد.",
            "payment_success": "✅ پرداخت با موفقیت انجام شد!",
            "payment_failed": "❌ پرداخت ناموفق بود.",
            "payment_cancelled": "🚫 پرداخت لغو شد.",
            "coupon_applied": "✅ کد تخفیف اعمال شد!",
            "invalid_coupon": "⚠️ کد تخفیف نامعتبر است.",

            # وضعیت‌ها
            "status_pending": "⏳ در انتظار پرداخت",
            "status_paid": "✅ پرداخت شده",
            "status_processing": "🔄 در حال پردازش",
            "status_shipped": "🚚 ارسال شده",
            "status_delivered": "📦 تحویل داده شده",
            "status_canceled": "❌ لغو شده",
            "status_refunded": "💰 بازگشت وجه",
        },
        "en": {
            # General
            "welcome": "Welcome {name} 👋",
            "welcome_back": "Welcome back {name} 😊",
            "back": "Back",
            "cancel": "Cancel",
            "confirm": "Confirm",
            "yes": "Yes",
            "no": "No",
            "loading": "Loading...",
            "error": "Error",
            "success": "Success",
            "done": "Done",

            # Main Menu
            "main_menu": "🏠 Main Menu",
            "forms": "📋 Forms",
            "profile": "👤 Profile",
            "contact_us": "📞 Contact Us",
            "help": "❓ Help",
            "admin_panel": "⚙️ Admin Panel",

            # Forms
            "forms_list": "📋 Forms List",
            "start_form": "Start Form",
            "form_step": "Step {step} of {total}",
            "submit_form": "Submit Form",
            "form_submitted": "✅ Form submitted successfully!",
            "form_cancelled": "❌ Form cancelled.",

            # Profile
            "profile_info": "👤 Profile Information",
            "points": "⭐ Points",
            "level": "🏅 Level",
            "orders": "🛒 Orders",
            "no_orders": "No orders found.",
            "edit_profile": "✏️ Edit Profile",

            # Help
            "help_menu": "❓ User Guide",
            "faq": "❔ FAQ",
            "full_guide": "📖 Full Guide",

            # Contact
            "contact_info": "📞 Contact Information",

            # Errors
            "permission_denied": "⛔ You don't have permission to access this section.",
            "not_found": "⚠️ Item not found.",
            "invalid_input": "⚠️ Invalid input.",
            "rate_limit": "⏳ You have exceeded the rate limit.",

            # Payment
            "payment": "💳 Payment",
            "payment_initiated": "Payment initiated successfully.",
            "payment_success": "✅ Payment successful!",
            "payment_failed": "❌ Payment failed.",
            "payment_cancelled": "🚫 Payment cancelled.",
            "coupon_applied": "✅ Coupon applied successfully!",
            "invalid_coupon": "⚠️ Invalid coupon code.",

            # Statuses
            "status_pending": "⏳ Pending",
            "status_paid": "✅ Paid",
            "status_processing": "🔄 Processing",
            "status_shipped": "🚚 Shipped",
            "status_delivered": "📦 Delivered",
            "status_canceled": "❌ Canceled",
            "status_refunded": "💰 Refunded",
        },
    }