# my_bot_project/src/my_bot/infrastructure/database/migrations/__init__.py
"""
ماژول مهاجرت دیتابیس (Database Migrations).

این ماژول شامل اسکریپت‌های مهاجرت Alembic برای مدیریت تغییرات
ساختار دیتابیس به‌صورت نسخه‌بندی‌شده است.

امکانات:
- ایجاد و اجرای مهاجرت‌های جدید
- ارتقاء و بازگشت به نسخه‌های قبلی
- مدیریت تاریخچه تغییرات دیتابیس
- پشتیبانی از PostgreSQL و SQLite
"""

from pathlib import Path

# مسیر دایرکتوری مهاجرت‌ها
MIGRATIONS_DIR = Path(__file__).parent

# مسیر فایل alembic.ini
ALEMBIC_INI_PATH = MIGRATIONS_DIR / "alembic.ini"

# مسیر دایرکتوری نسخه‌ها
VERSIONS_DIR = MIGRATIONS_DIR / "versions"

__all__ = [
    "MIGRATIONS_DIR",
    "ALEMBIC_INI_PATH",
    "VERSIONS_DIR",
]