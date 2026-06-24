# my_bot_project/src/my_bot/audit/__init__.py
"""
ماژول حسابرسی (Audit).

این ماژول شامل ابزارهای ثبت و مدیریت لاگ‌های حسابرسی برای پیگیری
فعالیت‌های کاربران، تغییرات داده‌ها و رویدادهای امنیتی است.

اجزای اصلی:
- AuditLogger: ثبت رویدادهای حسابرسی
- AuditRepository: ذخیره‌سازی و بازیابی لاگ‌های حسابرسی
- AuditMiddleware: میدلور ثبت خودکار رویدادها
"""

from my_bot.audit.audit_logger import AuditLogger
from my_bot.audit.audit_repository import AuditRepository
from my_bot.audit.audit_middleware import AuditMiddleware

__all__ = [
    "AuditLogger",
    "AuditRepository",
    "AuditMiddleware",
]