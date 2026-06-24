# my_bot_project/src/my_bot/presentation/__init__.py
"""
ماژول ارائه (Presentation).

این ماژول مسئولیت مدیریت ورودی‌های کاربر (از طریق تلگرام و Web API)
و نمایش خروجی‌ها را بر عهده دارد. لایه ارائه به‌عنوان پل ارتباطی بین
کاربر و لایه کاربرد (Application) عمل می‌کند.

اجزای اصلی:
- Handlers: مدیریت رویدادهای تلگرام (دستورات، دکمه‌ها، پیام‌ها)
- Keyboards: ساخت کیبوردهای شیشه‌ای (Inline Keyboard)
- Middlewares: میدلورهای پردازش درخواست (Rate Limiting, Logging, i18n)
- Web API: وب‌هوک و APIهای HTTP (برای اتصال به سرویس‌های خارجی)
"""

# ----------------------------------------------
# Import Handlers
# ----------------------------------------------
from my_bot.presentation.handlers.start.start_command import StartCommandHandler
from my_bot.presentation.handlers.start.greeting import GreetingHandler
from my_bot.presentation.handlers.user.profile_handler import ProfileHandler
from my_bot.presentation.handlers.user.order_history_handler import OrderHistoryHandler
from my_bot.presentation.handlers.user.help_handler import HelpHandler
from my_bot.presentation.handlers.form.form_list_handler import FormListHandler
from my_bot.presentation.handlers.form.form_start_handler import FormStartHandler
from my_bot.presentation.handlers.form.form_step_handler import FormStepHandler
from my_bot.presentation.handlers.form.form_submit_handler import FormSubmitHandler
from my_bot.presentation.handlers.payment.payment_initiate_handler import PaymentInitiateHandler
from my_bot.presentation.handlers.payment.payment_callback_handler import PaymentCallbackHandler
from my_bot.presentation.handlers.payment.coupon_apply_handler import CouponApplyHandler
from my_bot.presentation.handlers.admin.admin_panel_entry import AdminPanelEntryHandler
from my_bot.presentation.handlers.admin.admin_callbacks import AdminCallbacksHandler

# ----------------------------------------------
# Import Keyboards
# ----------------------------------------------
from my_bot.presentation.keyboards.common.main_menu import get_main_menu_keyboard
from my_bot.presentation.keyboards.common.back_buttons import get_back_button, get_back_to_main_button
from my_bot.presentation.keyboards.common.cancel_buttons import get_cancel_button
from my_bot.presentation.keyboards.user.user_menu import get_user_menu_keyboard
from my_bot.presentation.keyboards.user.user_actions import get_user_actions_keyboard
from my_bot.presentation.keyboards.form.form_choice import get_form_choice_keyboard
from my_bot.presentation.keyboards.form.form_navigation import get_form_navigation_keyboard
from my_bot.presentation.keyboards.admin.admin_keyboards import get_admin_main_keyboard

# ----------------------------------------------
# Import Middlewares
# ----------------------------------------------
from my_bot.presentation.middlewares.rate_limiter import RateLimiterMiddleware
from my_bot.presentation.middlewares.logging_middleware import LoggingMiddleware
from my_bot.presentation.middlewares.i18n_middleware import I18nMiddleware
from my_bot.presentation.middlewares.feature_flag_middleware import FeatureFlagMiddleware

# ----------------------------------------------
# Import Web API
# ----------------------------------------------
from my_bot.presentation.web_api.web_app import WebApp
from my_bot.presentation.web_api.routes.webhook import WebhookRouter
from my_bot.presentation.web_api.routes.health import HealthRouter
from my_bot.presentation.web_api.routes.metrics import MetricsRouter


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # Handlers
    "StartCommandHandler",
    "GreetingHandler",
    "ProfileHandler",
    "OrderHistoryHandler",
    "HelpHandler",
    "FormListHandler",
    "FormStartHandler",
    "FormStepHandler",
    "FormSubmitHandler",
    "PaymentInitiateHandler",
    "PaymentCallbackHandler",
    "CouponApplyHandler",
    "AdminPanelEntryHandler",
    "AdminCallbacksHandler",

    # Keyboards
    "get_main_menu_keyboard",
    "get_back_button",
    "get_back_to_main_button",
    "get_cancel_button",
    "get_user_menu_keyboard",
    "get_user_actions_keyboard",
    "get_form_choice_keyboard",
    "get_form_navigation_keyboard",
    "get_admin_main_keyboard",

    # Middlewares
    "RateLimiterMiddleware",
    "LoggingMiddleware",
    "I18nMiddleware",
    "FeatureFlagMiddleware",

    # Web API
    "WebApp",
    "WebhookRouter",
    "HealthRouter",
    "MetricsRouter",
]