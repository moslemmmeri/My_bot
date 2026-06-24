# my_bot_project/src/my_bot/shared/i18n/__init__.py
"""
ماژول چندزبانی (Internationalization - I18n).

این ماژول شامل ابزارهای مدیریت چندزبانی در پروژه است:
- LocaleManager: مدیریت زبان و بارگذاری ترجمه‌ها
- LanguageDetector: تشخیص زبان کاربر
- Translations: فایل‌های ترجمه (JSON)
"""

from my_bot.shared.i18n.locale_manager import LocaleManager
from my_bot.shared.i18n.language_detector import LanguageDetector

__all__ = [
    "LocaleManager",
    "LanguageDetector",
]