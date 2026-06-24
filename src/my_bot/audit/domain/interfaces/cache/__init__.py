# my_bot_project/src/my_bot/domain/interfaces/cache/__init__.py
"""
ماژول اینترفیس‌های کش (Cache Interfaces).

این ماژول شامل اینترفیس‌های مربوط به سیستم کش است که برای ذخیره‌سازی
موقت داده‌ها در لایه‌های مختلف استفاده می‌شود.
"""

from my_bot.domain.interfaces.cache.cache_interface import CacheInterface

__all__ = [
    "CacheInterface",
]