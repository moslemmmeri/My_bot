# my_bot_project/src/my_bot/infrastructure/cache/__init__.py
"""
ماژول کش (Cache Infrastructure).

این ماژول شامل پیاده‌سازی‌های مختلف سیستم کش با قابلیت Fallback خودکار است.
با استفاده از این ماژول می‌توان از Redis به‌عنوان کش اصلی و در صورت عدم دسترسی،
به‌صورت خودکار به Local Cache (حافظه داخلی) Fallback کرد.

اجزای اصلی:
- CacheManager: مدیر مرکزی کش با قابلیت Fallback خودکار
- RedisAdapter: آداپتور Redis با پشتیبانی از Connection Pool
- LocalAdapter: آداپتور کش محلی (در حافظه) با TTL و محدودیت اندازه
- CacheFallback: مکانیزم Fallback خودکار بین Redis و Local
"""

# ----------------------------------------------
# Import Cache Components
# ----------------------------------------------
from my_bot.infrastructure.cache.cache_manager import CacheManager
from my_bot.infrastructure.cache.redis_adapter import RedisAdapter
from my_bot.infrastructure.cache.local_adapter import LocalAdapter
from my_bot.infrastructure.cache.cache_fallback import CacheFallback

# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    "CacheManager",
    "RedisAdapter",
    "LocalAdapter",
    "CacheFallback",
]