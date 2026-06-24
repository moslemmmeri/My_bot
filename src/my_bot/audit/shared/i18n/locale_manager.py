# my_bot_project/src/my_bot/shared/i18n/locale_manager.py
"""
مدیریت چندزبانی (Locale Manager).

این ماژول شامل کلاس `LocaleManager` است که مسئولیت مدیریت زبان،
بارگذاری فایل‌های ترجمه، تغییر زبان و دسترسی به پیام‌های ترجمه‌شده
را بر عهده دارد.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from functools import lru_cache

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.validation_errors import ValidationError

logger = get_logger(__name__)


class LocaleManager:
    """
    مدیریت چندزبانی با پشتیبانی از کش ترجمه‌ها.

    این کلاس با بارگذاری فایل‌های JSON ترجمه از دایرکتوری مشخص،
    امکان دسترسی به پیام‌های ترجمه‌شده را فراهم می‌کند.

    Attributes:
        default_language: زبان پیش‌فرض (پیش‌فرض: 'fa').
        supported_languages: لیست زبان‌های پشتیبانی‌شده.
        translations_path: مسیر دایرکتوری فایل‌های ترجمه.
        _translations: کش ترجمه‌ها (زبان -> دیکشنری).
        _current_language: زبان فعلی.
        _cache_size: حداکثر تعداد زبان‌های کش‌شده.
    """

    def __init__(
        self,
        default_language: str = "fa",
        translations_path: Optional[Union[str, Path]] = None,
        supported_languages: Optional[List[str]] = None,
        cache_size: int = 10,
    ) -> None:
        """
        مقداردهی اولیه LocaleManager.

        Args:
            default_language: زبان پیش‌فرض (پیش‌فرض: 'fa').
            translations_path: مسیر دایرکتوری فایل‌های ترجمه.
            supported_languages: لیست زبان‌های پشتیبانی‌شده.
            cache_size: حداکثر تعداد زبان‌های کش‌شده (پیش‌فرض: ۱۰).
        """
        self.default_language = default_language
        self.supported_languages = supported_languages or ["fa", "en"]
        self._cache_size = cache_size
        self._current_language = default_language

        # تنظیم مسیر ترجمه‌ها
        if translations_path is None:
            # مسیر پیش‌فرض: src/my_bot/shared/i18n/translations/
            base_dir = Path(__file__).parent.parent.parent.parent
            translations_path = base_dir / "shared" / "i18n" / "translations"
        elif isinstance(translations_path, str):
            translations_path = Path(translations_path)

        self.translations_path = translations_path

        # کش ترجمه‌ها با استفاده از LRU Cache
        self._translations: Dict[str, Dict[str, str]] = {}

        # بارگذاری ترجمه‌های پیش‌فرض
        self._load_all_translations()

        logger.info(
            f"LocaleManager initialized: default_language={default_language}, "
            f"supported={self.supported_languages}, translations_path={translations_path}"
        )

    def _load_all_translations(self) -> None:
        """
        بارگذاری تمام فایل‌های ترجمه از دایرکتوری مشخص‌شده.
        """
        if not self.translations_path.exists():
            logger.warning(f"Translations directory not found: {self.translations_path}")
            # ایجاد دایرکتوری در صورت نیاز
            try:
                self.translations_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created translations directory: {self.translations_path}")
                # ایجاد فایل‌های ترجمه پیش‌فرض
                self._create_default_translations()
            except Exception as e:
                logger.error(f"Failed to create translations directory: {e}")

        # بارگذاری فایل‌های ترجمه برای هر زبان
        for lang in self.supported_languages:
            self._load_translation(lang)

        # اطمینان از وجود زبان پیش‌فرض
        if self.default_language not in self._translations:
            self._translations[self.default_language] = {}
            logger.warning(f"Default language '{self.default_language}' not found in translations.")

        logger.info(
            f"Loaded translations for {len(self._translations)} languages: "
            f"{list(self._translations.keys())}"
        )

    def _load_translation(self, language: str) -> None:
        """
        بارگذاری ترجمه‌های یک زبان خاص.

        Args:
            language: کد زبان (مثلاً 'fa' یا 'en').
        """
        lang_file = self.translations_path / f"{language}.json"

        try:
            if lang_file.exists():
                with open(lang_file, "r", encoding="utf-8") as f:
                    translations = json.load(f)
                self._translations[language] = translations
                logger.debug(f"Loaded translations for language: {language}")
            else:
                # ایجاد فایل خالی برای زبان
                self._translations[language] = {}
                self._save_translation(language)
                logger.info(f"Created empty translation file for: {language}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in translation file {lang_file}: {e}")
            self._translations[language] = {}
        except Exception as e:
            logger.error(f"Error loading translations for {language}: {e}")
            self._translations[language] = {}

    def _create_default_translations(self) -> None:
        """
        ایجاد فایل‌های ترجمه پیش‌فرض در صورت عدم وجود.
        """
        default_translations = {
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

        for lang, translations in default_translations.items():
            lang_file = self.translations_path / f"{lang}.json"
            if not lang_file.exists():
                try:
                    with open(lang_file, "w", encoding="utf-8") as f:
                        json.dump(translations, f, ensure_ascii=False, indent=2)
                    logger.info(f"Created default translation file: {lang_file}")
                except Exception as e:
                    logger.error(f"Failed to create translation file {lang_file}: {e}")

    def _save_translation(self, language: str) -> None:
        """
        ذخیره ترجمه‌های یک زبان در فایل.

        Args:
            language: کد زبان.
        """
        lang_file = self.translations_path / f"{language}.json"
        try:
            translations = self._translations.get(language, {})
            with open(lang_file, "w", encoding="utf-8") as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved translations for {language} to {lang_file}")
        except Exception as e:
            logger.error(f"Failed to save translations for {language}: {e}")

    def get_translation(self, key: str, language: Optional[str] = None) -> str:
        """
        دریافت یک ترجمه برای کلید مشخص.

        Args:
            key: کلید ترجمه (با فرمت 'section.key').
            language: کد زبان (اختیاری، در صورت None از زبان فعلی استفاده می‌شود).

        Returns:
            str: متن ترجمه‌شده، یا خود کلید در صورت عدم وجود ترجمه.

        Example:
            locale_manager.get_translation("welcome", "fa")
            # خروجی: "خوش آمدید {name} 👋"
        """
        lang = language or self._current_language

        # اگر زبان پشتیبانی نمی‌شود، به زبان پیش‌فرض برگرد
        if lang not in self.supported_languages:
            lang = self.default_language

        # جستجوی ترجمه در زبان مورد نظر
        translations = self._translations.get(lang, {})
        if key in translations:
            return translations[key]

        # اگر در زبان فعلی پیدا نشد، در زبان پیش‌فرض جستجو کن
        if lang != self.default_language:
            default_translations = self._translations.get(self.default_language, {})
            if key in default_translations:
                return default_translations[key]

        # اگر ترجمه پیدا نشد، کلید را برگردان
        logger.debug(f"Translation key not found: '{key}' for language '{lang}'")
        return key

    def get_translation_with_params(
        self,
        key: str,
        language: Optional[str] = None,
        **params,
    ) -> str:
        """
        دریافت ترجمه با جایگزینی پارامترها.

        Args:
            key: کلید ترجمه.
            language: کد زبان (اختیاری).
            **params: پارامترهای جایگزینی (مثلاً name='علی').

        Returns:
            str: متن ترجمه‌شده با جایگزینی پارامترها.

        Example:
            locale_manager.get_translation_with_params(
                "welcome", name="علی"
            )
            # خروجی: "خوش آمدید علی 👋"
        """
        text = self.get_translation(key, language)

        # جایگزینی پارامترها
        for param, value in params.items():
            text = text.replace(f"{{{param}}}", str(value))

        return text

    def get_current_language(self) -> str:
        """
        دریافت زبان فعلی.

        Returns:
            str: کد زبان فعلی.
        """
        return self._current_language

    def set_current_language(self, language: str) -> None:
        """
        تنظیم زبان فعلی.

        Args:
            language: کد زبان (باید در supported_languages باشد).

        Raises:
            ValidationError: اگر زبان پشتیبانی نشود.
        """
        if language not in self.supported_languages:
            raise ValidationError(
                message=f"زبان '{language}' پشتیبانی نمی‌شود.",
                context={"language": language, "supported": self.supported_languages},
            )

        if language != self._current_language:
            self._current_language = language
            logger.debug(f"Current language set to: {language}")

    def get_supported_languages(self) -> List[str]:
        """
        دریافت لیست زبان‌های پشتیبانی‌شده.

        Returns:
            List[str]: لیست کدهای زبان.
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

    def get_all_translations(self, language: Optional[str] = None) -> Dict[str, str]:
        """
        دریافت تمام ترجمه‌های یک زبان.

        Args:
            language: کد زبان (اختیاری، در صورت None از زبان فعلی استفاده می‌شود).

        Returns:
            Dict[str, str]: دیکشنری تمام ترجمه‌ها.
        """
        lang = language or self._current_language
        return self._translations.get(lang, {}).copy()

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

        if language not in self._translations:
            self._translations[language] = {}

        self._translations[language][key] = value
        self._save_translation(language)
        logger.debug(f"Translation added: '{key}' = '{value}' for '{language}'")

    def remove_translation(self, key: str, language: str) -> bool:
        """
        حذف یک ترجمه.

        Args:
            key: کلید ترجمه.
            language: کد زبان.

        Returns:
            bool: True در صورت حذف موفق، False در صورت عدم وجود.

        Raises:
            ValidationError: اگر زبان پشتیبانی نشود.
        """
        if language not in self.supported_languages:
            raise ValidationError(
                message=f"زبان '{language}' پشتیبانی نمی‌شود.",
                context={"language": language, "supported": self.supported_languages},
            )

        if language not in self._translations:
            return False

        if key not in self._translations[language]:
            return False

        del self._translations[language][key]
        self._save_translation(language)
        logger.debug(f"Translation removed: '{key}' for '{language}'")
        return True

    def reload_translations(self) -> None:
        """
        بارگذاری مجدد ترجمه‌ها از فایل‌ها (برای استفاده در زمان توسعه یا تغییر فایل‌ها).
        """
        self._translations.clear()
        self._load_all_translations()
        logger.info("Translations reloaded.")

    def has_key(self, key: str, language: Optional[str] = None) -> bool:
        """
        بررسی وجود یک کلید ترجمه.

        Args:
            key: کلید ترجمه.
            language: کد زبان (اختیاری، در صورت None از زبان فعلی استفاده می‌شود).

        Returns:
            bool: True اگر کلید وجود داشته باشد.
        """
        lang = language or self._current_language
        translations = self._translations.get(lang, {})
        return key in translations

    def get_language_display_name(self, language: str) -> str:
        """
        دریافت نام نمایشی زبان (نام کامل).

        Args:
            language: کد زبان.

        Returns:
            str: نام کامل زبان.
        """
        names = {
            "fa": "فارسی",
            "en": "English (US)",
        }
        return names.get(language, language)

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل LocaleManager به دیکشنری (برای سریال‌سازی).

        Returns:
            Dict[str, Any]: دیکشنری شامل اطلاعات LocaleManager.
        """
        return {
            "default_language": self.default_language,
            "current_language": self._current_language,
            "supported_languages": self.supported_languages,
            "translations_path": str(self.translations_path),
            "loaded_languages": list(self._translations.keys()),
            "translations_count": {
                lang: len(translations)
                for lang, translations in self._translations.items()
            },
        }

    def __str__(self) -> str:
        """
        نمایش رشته‌ای LocaleManager.
        """
        return (
            f"LocaleManager(default={self.default_language}, "
            f"current={self._current_language}, "
            f"languages={list(self._translations.keys())})"
        )


# ==========================================
# تابع کمکی برای ایجاد نمونه سراسری
# ==========================================

_global_locale_manager: Optional[LocaleManager] = None


def get_global_locale_manager() -> Optional[LocaleManager]:
    """
    دریافت نمونه سراسری LocaleManager.

    Returns:
        Optional[LocaleManager]: نمونه سراسری یا None.
    """
    return _global_locale_manager


def set_global_locale_manager(manager: LocaleManager) -> None:
    """
    تنظیم نمونه سراسری LocaleManager.

    Args:
        manager: نمونه LocaleManager.
    """
    global _global_locale_manager
    _global_locale_manager = manager
    logger.info("Global LocaleManager set.")