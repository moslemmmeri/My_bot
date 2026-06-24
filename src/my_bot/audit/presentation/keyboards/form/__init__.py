# my_bot_project/src/my_bot/presentation/keyboards/form/__init__.py
"""
ماژول کیبوردهای فرم (Form Keyboards).

این ماژول شامل کیبوردهای مربوط به فرم‌های پویا است:
- form_choice: کیبورد انتخاب فرم
- form_navigation: کیبورد ناوبری در فرم (مراحل قبلی/بعدی، لغو)
"""

from my_bot.presentation.keyboards.form.form_choice import get_form_choice_keyboard
from my_bot.presentation.keyboards.form.form_navigation import get_form_navigation_keyboard

__all__ = [
    "get_form_choice_keyboard",
    "get_form_navigation_keyboard",
]