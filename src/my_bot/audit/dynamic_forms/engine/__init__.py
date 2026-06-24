# my_bot_project/src/my_bot/dynamic_forms/engine/__init__.py
"""
ماژول موتور فرم‌های پویا (Dynamic Forms Engine).

این ماژول شامل اجزای اصلی موتور فرم‌سازی پویا است:
- FormRenderer: رندر کردن فرم‌ها در خروجی‌های مختلف (تلگرام، HTML، JSON)
- FormValidator: اعتبارسنجی داده‌های ورودی بر اساس قوانین فیلدها
- FormStateManager: مدیریت وضعیت فرم در حین پر کردن (ذخیره پیشرفت، بازیابی و ...)
"""

from my_bot.dynamic_forms.engine.form_renderer import FormRenderer
from my_bot.dynamic_forms.engine.form_validator import FormValidator
from my_bot.dynamic_forms.engine.form_state_manager import FormStateManager

__all__ = [
    "FormRenderer",
    "FormValidator",
    "FormStateManager",
]