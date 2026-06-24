# my_bot_project/src/my_bot/dynamic_forms/__init__.py
"""
ماژول فرم‌های پویا (Dynamic Forms).

این ماژول شامل موتور فرم‌ساز پویا است که امکان ایجاد، مدیریت و پردازش
فرم‌های پویا را در سیستم فراهم می‌کند. فرم‌ها می‌توانند شامل فیلدهای
با انواع مختلف، اعتبارسنجی‌ها، شرط‌ها و منطق‌های پیچیده باشند.

اجزای اصلی:
- Models: مدل‌های فرم (تعریف فرم، فیلدها)
- Engine: موتور پردازش فرم (رندر، اعتبارسنجی، مدیریت وضعیت)
- Handlers: هندلرهای تلگرام برای تعامل با فرم‌ها
"""

# ----------------------------------------------
# Import Models
# ----------------------------------------------
from my_bot.dynamic_forms.models.form_definition import FormDefinition
from my_bot.dynamic_forms.models.form_field import DynamicFormField

# ----------------------------------------------
# Import Engine
# ----------------------------------------------
from my_bot.dynamic_forms.engine.form_renderer import FormRenderer
from my_bot.dynamic_forms.engine.form_validator import FormValidator
from my_bot.dynamic_forms.engine.form_state_manager import FormStateManager

# ----------------------------------------------
# Import Handlers
# ----------------------------------------------
from my_bot.dynamic_forms.handlers.form_start import FormStartHandler
from my_bot.dynamic_forms.handlers.form_step import FormStepHandler
from my_bot.dynamic_forms.handlers.form_submit import FormSubmitHandler


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # Models
    "FormDefinition",
    "DynamicFormField",

    # Engine
    "FormRenderer",
    "FormValidator",
    "FormStateManager",

    # Handlers
    "FormStartHandler",
    "FormStepHandler",
    "FormSubmitHandler",
]