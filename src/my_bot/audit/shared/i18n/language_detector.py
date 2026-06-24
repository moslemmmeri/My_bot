# my_bot_project/src/my_bot/shared/i18n/language_detector.py
"""
تشخیص زبان کاربر (Language Detector).

این ماژول شامل کلاس `LanguageDetector` است که زبان کاربر را با استفاده
از روش‌های مختلف (مانند language_code تلگرام، اطلاعات پروفایل کاربر،
و زبان‌های ذخیره‌شده در دیتابیس) تشخیص می‌دهد.
"""

import re
from typing import Optional, Dict, Any, List, Set
from collections import Counter

from my_bot.core.logger.logger_setup import get_logger
from my_bot.shared.i18n.locale_manager import LocaleManager

logger = get_logger(__name__)


class LanguageDetector:
    """
    تشخیص زبان کاربر با استفاده از روش‌های مختلف.

    این کلاس با استفاده از زبان تلگرام، اطلاعات کاربر و تنظیمات سیستمی،
    بهترین زبان را برای کاربر تشخیص می‌دهد.

    Attributes:
        locale_manager: نمونه LocaleManager برای دسترسی به زبان‌های پشتیبانی‌شده.
        default_language: زبان پیش‌فرض در صورت عدم تشخیص.
        priority: اولویت روش‌های تشخیص ('user_preference', 'telegram', 'database', 'default').
        _user_languages: کش زبان کاربران (user_id -> language).
    """

    def __init__(
        self,
        locale_manager: LocaleManager,
        default_language: Optional[str] = None,
        priority: List[str] = None,
    ) -> None:
        """
        مقداردهی اولیه LanguageDetector.

        Args:
            locale_manager: نمونه LocaleManager.
            default_language: زبان پیش‌فرض (در صورت None از locale_manager استفاده می‌شود).
            priority: اولویت روش‌های تشخیص ('user_preference', 'telegram', 'database', 'default').
        """
        self.locale_manager = locale_manager
        self.default_language = default_language or locale_manager.default_language
        self._user_languages: Dict[int, str] = {}
        self._telegram_languages: Dict[int, str] = {}
        self._database_languages: Dict[int, str] = {}

        # اولویت پیش‌فرض
        self.priority = priority or [
            "user_preference",
            "telegram",
            "database",
            "default",
        ]

        logger.info(
            f"LanguageDetector initialized: default_language={self.default_language}, "
            f"priority={self.priority}"
        )

    def detect_language(
        self,
        user_id: Optional[int] = None,
        telegram_language_code: Optional[str] = None,
        user_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        تشخیص زبان کاربر.

        Args:
            user_id: شناسه کاربر (اختیاری).
            telegram_language_code: زبان تلگرام (اختیاری).
            user_data: اطلاعات کاربر شامل زبان ذخیره‌شده (اختیاری).

        Returns:
            str: کد زبان تشخیص‌داده‌شده.

        Example:
            language = detector.detect_language(
                user_id=12345,
                telegram_language_code="en-US",
                user_data={"language": "fa"}
            )
            # خروجی: "fa" (چون زبان کاربر در دیتابیس ذخیره شده است)
        """
        languages = {}

        # ۱. زبان ذخیره‌شده کاربر در دیتابیس (user_data)
        if user_data and user_data.get("language"):
            lang = self._normalize_language(user_data["language"])
            if self._is_supported(lang):
                languages["database"] = lang

        # ۲. زبان تلگرام کاربر
        if telegram_language_code:
            lang = self._normalize_language(telegram_language_code)
            if self._is_supported(lang):
                languages["telegram"] = lang

        # ۳. زبان ذخیره‌شده در کش (user_preference)
        if user_id and user_id in self._user_languages:
            lang = self._user_languages[user_id]
            if self._is_supported(lang):
                languages["user_preference"] = lang

        # ۴. زبان ذخیره‌شده در دیتابیس (از کش)
        if user_id and user_id in self._database_languages:
            lang = self._database_languages[user_id]
            if self._is_supported(lang):
                languages["database"] = lang

        # انتخاب زبان بر اساس اولویت
        for method in self.priority:
            if method in languages:
                detected = languages[method]
                logger.debug(
                    f"Language detected for user {user_id}: "
                    f"{detected} (method: {method})"
                )
                return detected

        # زبان پیش‌فرض
        logger.debug(f"No language detected for user {user_id}. Using default: {self.default_language}")
        return self.default_language

    def detect_from_telegram(self, language_code: Optional[str]) -> str:
        """
        تشخیص زبان از کد زبان تلگرام.

        Args:
            language_code: کد زبان تلگرام (مثلاً 'en-US', 'fa').

        Returns:
            str: کد زبان تشخیص‌داده‌شده.

        Example:
            detector.detect_from_telegram("en-US")  # "en"
            detector.detect_from_telegram("fa")    # "fa"
        """
        if not language_code:
            return self.default_language

        lang = self._normalize_language(language_code)
        if self._is_supported(lang):
            return lang

        # اگر زبان پشتیبانی نمی‌شود، به زبان پیش‌فرض برگرد
        return self.default_language

    def detect_from_user_data(self, user_data: Dict[str, Any]) -> str:
        """
        تشخیص زبان از اطلاعات کاربر.

        Args:
            user_data: دیکشنری اطلاعات کاربر.

        Returns:
            str: کد زبان تشخیص‌داده‌شده.

        Example:
            detector.detect_from_user_data({"language": "fa", "country": "IR"})
            # خروجی: "fa"
        """
        # بررسی فیلد language
        if "language" in user_data and user_data["language"]:
            lang = self._normalize_language(user_data["language"])
            if self._is_supported(lang):
                return lang

        # بررسی فیلد locale
        if "locale" in user_data and user_data["locale"]:
            lang = self._normalize_language(user_data["locale"])
            if self._is_supported(lang):
                return lang

        # بررسی فیلد country
        if "country" in user_data and user_data["country"]:
            # می‌توانیم از کد کشور برای تشخیص زبان استفاده کنیم
            country_lang = self._get_language_by_country(user_data["country"])
            if country_lang:
                return country_lang

        # بررسی فیلد timezone
        if "timezone" in user_data and user_data["timezone"]:
            # می‌توانیم از منطقه زمانی برای تشخیص زبان استفاده کنیم
            tz_lang = self._get_language_by_timezone(user_data["timezone"])
            if tz_lang:
                return tz_lang

        return self.default_language

    def set_user_language(self, user_id: int, language: str) -> None:
        """
        تنظیم زبان یک کاربر (ذخیره در کش).

        Args:
            user_id: شناسه کاربر.
            language: کد زبان.
        """
        lang = self._normalize_language(language)
        if self._is_supported(lang):
            self._user_languages[user_id] = lang
            logger.debug(f"User {user_id} language set to: {lang}")
        else:
            logger.warning(f"Unsupported language '{language}' for user {user_id}")

    def set_database_language(self, user_id: int, language: str) -> None:
        """
        تنظیم زبان ذخیره‌شده در دیتابیس برای یک کاربر.

        Args:
            user_id: شناسه کاربر.
            language: کد زبان.
        """
        lang = self._normalize_language(language)
        if self._is_supported(lang):
            self._database_languages[user_id] = lang
            logger.debug(f"User {user_id} database language set to: {lang}")
        else:
            logger.warning(f"Unsupported database language '{language}' for user {user_id}")

    def get_user_language(self, user_id: int) -> Optional[str]:
        """
        دریافت زبان یک کاربر (از کش).

        Args:
            user_id: شناسه کاربر.

        Returns:
            Optional[str]: کد زبان یا None.
        """
        return self._user_languages.get(user_id)

    def remove_user_language(self, user_id: int) -> None:
        """
        حذف زبان یک کاربر از کش.

        Args:
            user_id: شناسه کاربر.
        """
        if user_id in self._user_languages:
            del self._user_languages[user_id]
            logger.debug(f"User {user_id} language removed from cache.")

    def _normalize_language(self, language: str) -> str:
        """
        نرمال‌سازی کد زبان (تبدیل به حروف کوچک و گرفتن دو حرف اول).

        Args:
            language: کد زبان.

        Returns:
            str: کد زبان نرمال‌سازی‌شده.

        Example:
            _normalize_language("en-US")  # "en"
            _normalize_language("FA")     # "fa"
        """
        if not language:
            return ""

        # حذف فضاها و تبدیل به حروف کوچک
        lang = language.strip().lower()

        # گرفتن دو حرف اول (برای زبان‌های با زیرمجموعه مثل en-US)
        # اما اگر طول آن کمتر از ۲ بود، همان را برگردان
        if len(lang) >= 2 and "-" in lang:
            lang = lang.split("-")[0]
        elif len(lang) >= 2 and "_" in lang:
            lang = lang.split("_")[0]

        return lang[:2] if len(lang) >= 2 else lang

    def _is_supported(self, language: str) -> bool:
        """
        بررسی اینکه آیا زبان پشتیبانی می‌شود.

        Args:
            language: کد زبان.

        Returns:
            bool: True اگر زبان پشتیبانی شود.
        """
        if not language:
            return False
        return language in self.locale_manager.get_supported_languages()

    def _get_language_by_country(self, country_code: str) -> Optional[str]:
        """
        دریافت زبان پیش‌فرض بر اساس کد کشور.

        Args:
            country_code: کد کشور (با فرمت ISO 3166-1 alpha-2).

        Returns:
            Optional[str]: کد زبان یا None.
        """
        country_map = {
            "IR": "fa",
            "AF": "fa",
            "US": "en",
            "GB": "en",
            "CA": "en",
            "AU": "en",
            "DE": "de",
            "FR": "fr",
            "ES": "es",
            "IT": "it",
            "TR": "tr",
            "RU": "ru",
            "CN": "zh",
            "JP": "ja",
            "KR": "ko",
            "AE": "ar",
            "SA": "ar",
            "EG": "ar",
            "IL": "he",
            "IN": "hi",
            "PK": "ur",
            "NL": "nl",
            "SE": "sv",
            "NO": "no",
            "DK": "da",
            "FI": "fi",
            "GR": "el",
            "PT": "pt",
            "BR": "pt",
            "MX": "es",
        }
        return country_map.get(country_code.upper())

    def _get_language_by_timezone(self, timezone: str) -> Optional[str]:
        """
        دریافت زبان پیش‌فرض بر اساس منطقه زمانی.

        Args:
            timezone: نام منطقه زمانی.

        Returns:
            Optional[str]: کد زبان یا None.
        """
        timezone_map = {
            "Asia/Tehran": "fa",
            "Asia/Dubai": "ar",
            "Asia/Tokyo": "ja",
            "Asia/Shanghai": "zh",
            "Asia/Seoul": "ko",
            "Asia/Kolkata": "hi",
            "Asia/Karachi": "ur",
            "Europe/London": "en",
            "Europe/Paris": "fr",
            "Europe/Berlin": "de",
            "Europe/Moscow": "ru",
            "Europe/Istanbul": "tr",
            "Europe/Rome": "it",
            "Europe/Madrid": "es",
            "America/New_York": "en",
            "America/Los_Angeles": "en",
            "America/Chicago": "en",
            "America/Toronto": "en",
            "America/Sao_Paulo": "pt",
            "America/Mexico_City": "es",
            "Australia/Sydney": "en",
            "Australia/Melbourne": "en",
            "Africa/Cairo": "ar",
            "Africa/Johannesburg": "en",
            "UTC": "en",
        }
        return timezone_map.get(timezone)

    def get_most_frequent_language(self, languages: List[str]) -> str:
        """
        دریافت پرتکرارترین زبان از لیست.

        Args:
            languages: لیست کدهای زبان.

        Returns:
            str: پرتکرارترین زبان یا زبان پیش‌فرض.

        Example:
            detector.get_most_frequent_language(["fa", "en", "fa", "en", "fa"])
            # خروجی: "fa"
        """
        if not languages:
            return self.default_language

        # فیلتر کردن زبان‌های پشتیبانی‌شده
        supported = [lang for lang in languages if self._is_supported(lang)]

        if not supported:
            return self.default_language

        # شمارش تکرارها
        counter = Counter(supported)
        most_common = counter.most_common(1)
        return most_common[0][0] if most_common else self.default_language

    def get_language_confidence(self, user_id: Optional[int] = None) -> Dict[str, float]:
        """
        دریافت میزان اطمینان برای هر زبان.

        Args:
            user_id: شناسه کاربر (اختیاری).

        Returns:
            Dict[str, float]: دیکشنری کد زبان به میزان اطمینان (۰ تا ۱).
        """
        confidence: Dict[str, float] = {}

        # اگر user_id وجود دارد و زبانش در کش است، اطمینان بالایی دارد
        if user_id and user_id in self._user_languages:
            confidence[self._user_languages[user_id]] = 1.0

        # زبان‌های پیش‌فرض با اطمینان متوسط
        if self.default_language not in confidence:
            confidence[self.default_language] = 0.5

        # زبان‌های پشتیبانی‌شده با اطمینان پایین
        for lang in self.locale_manager.get_supported_languages():
            if lang not in confidence:
                confidence[lang] = 0.1

        return confidence

    def detect_from_text(self, text: str) -> str:
        """
        تشخیص زبان از متن (با استفاده از الگوهای ساده).

        توجه: این یک تشخیص ساده است و برای تشخیص دقیق باید از کتابخانه‌های تخصصی
        مثل `langdetect` استفاده کنید.

        Args:
            text: متن برای تشخیص زبان.

        Returns:
            str: کد زبان تشخیص‌داده‌شده.
        """
        if not text or not text.strip():
            return self.default_language

        # الگوهای ساده برای تشخیص زبان فارسی
        persian_patterns = [
            r'[آ-ی]',  # کاراکترهای فارسی
            r'سلام', r'خوب', r'چطور', r'باشه', r'ممنون',
            r'بله', r'خیر', r'نه', r'آره',
            r'متشکرم', r'خواهش', r'ببخشید',
        ]

        english_patterns = [
            r'[a-zA-Z]',  # کاراکترهای انگلیسی
            r'hello', r'hi', r'thanks', r'yes', r'no',
            r'please', r'sorry', r'okay', r'ok',
        ]

        text_lower = text.lower()

        # امتیازدهی
        persian_score = 0
        english_score = 0

        # بررسی الگوهای فارسی
        for pattern in persian_patterns:
            if re.search(pattern, text_lower):
                persian_score += 1

        # بررسی الگوهای انگلیسی
        for pattern in english_patterns:
            if re.search(pattern, text_lower):
                english_score += 1

        # اگر امتیاز فارسی بالاتر باشد، فارسی
        if persian_score > english_score:
            return "fa"

        # اگر امتیاز انگلیسی بالاتر باشد، انگلیسی
        if english_score > persian_score:
            return "en"

        # اگر مساوی بود، زبان پیش‌فرض
        return self.default_language

    def detect_from_message(self, message: str) -> str:
        """
        تشخیص زبان از پیام (با استفاده از کتابخانه langdetect در صورت وجود).

        Args:
            message: متن پیام.

        Returns:
            str: کد زبان تشخیص‌داده‌شده.
        """
        try:
            # تلاش برای استفاده از کتابخانه langdetect
            from langdetect import detect

            lang = detect(message)
            lang = self._normalize_language(lang)

            if self._is_supported(lang):
                return lang

        except ImportError:
            logger.debug("langdetect library not available. Using fallback.")
            return self.detect_from_text(message)

        except Exception as e:
            logger.warning(f"Error detecting language with langdetect: {e}")
            return self.detect_from_text(message)

        return self.detect_from_text(message)

    def get_supported_languages(self) -> List[str]:
        """
        دریافت لیست زبان‌های پشتیبانی‌شده.

        Returns:
            List[str]: لیست کدهای زبان.
        """
        return self.locale_manager.get_supported_languages()

    def get_language_name(self, language: str) -> str:
        """
        دریافت نام نمایشی زبان.

        Args:
            language: کد زبان.

        Returns:
            str: نام نمایشی زبان.
        """
        return self.locale_manager.get_language_name(language)

    def clear_cache(self) -> None:
        """
        پاک کردن کش زبان‌ها.
        """
        self._user_languages.clear()
        self._telegram_languages.clear()
        self._database_languages.clear()
        logger.info("Language detector cache cleared.")