# my_bot_project/src/my_bot/presentation/handlers/__init__.py
"""
ماژول هندلرهای تلگرام (Telegram Handlers).

این ماژول شامل تمام هندلرهای مربوط به پردازش رویدادهای تلگرام است.
هندلرها مسئولیت دریافت درخواست‌های کاربر، اعتبارسنجی، فراخوانی سرویس‌های
مناسب و ارسال پاسخ به کاربر را بر عهده دارند.

هندلرهای موجود:
- Start: مدیریت دستور /start و خوش‌آمدگویی
- User: مدیریت پروفایل، تاریخچه سفارشات و راهنما
- Form: مدیریت فرم‌های پویا (لیست، شروع، مرحله، ارسال)
- Payment: مدیریت پرداخت (شروع، بازگشت، اعمال کوپن)
- Admin: مدیریت پنل ادمین (ورود، پردازش دکمه‌ها)
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
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
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
]