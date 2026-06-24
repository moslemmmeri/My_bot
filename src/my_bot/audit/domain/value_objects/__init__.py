# my_bot_project/src/my_bot/domain/value_objects/__init__.py
"""
ماژول ارزش‌مقدارها (Value Objects).

این ماژول شامل کلاس‌های ارزشی است که موجودیت‌های دامنه را تشکیل می‌دهند.
ارزش‌مقدارها هویت مستقل ندارند و بر اساس مقدارشان تعیین می‌شوند.
آنها غیرقابل تغییر (Immutable) هستند و قوانین اعتبارسنجی خاص خود را دارند.

ارزش‌مقدارهای موجود:
- Email: آدرس ایمیل با اعتبارسنجی فرمت
- Phone: شماره تلفن با فرمت بین‌المللی
- Money: مبلغ پولی با واحد پول
- RateLimit: محدودیت نرخ درخواست با پنجره زمانی
- FormField: یک فیلد در فرم با نوع و قوانین خاص
- UserLevel: سطح کاربری بر اساس امتیاز
"""

# ----------------------------------------------
# Import Value Objects
# ----------------------------------------------
from my_bot.domain.value_objects.email import Email
from my_bot.domain.value_objects.phone import Phone
from my_bot.domain.value_objects.money import Money
from my_bot.domain.value_objects.rate_limit import RateLimit
from my_bot.domain.value_objects.form_field import FormField
from my_bot.domain.value_objects.user_level import UserLevel

# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    "Email",
    "Phone",
    "Money",
    "RateLimit",
    "FormField",
    "UserLevel",
]