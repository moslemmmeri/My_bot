# my_bot_project/src/my_bot/presentation/keyboards/__init__.py
"""
ماژول کیبوردهای شیشه‌ای (Inline Keyboards).

این ماژول شامل تمام کیبوردهای شیشه‌ای (Inline Keyboard) مورد استفاده در ربات است.
کیبوردها به‌صورت توابع سازنده (Factory Functions) پیاده‌سازی شده‌اند تا
امکان ساخت پویا و سفارشی‌سازی بر اساس داده‌های مختلف فراهم شود.

کیبوردهای موجود:
- Common: دکمه‌های عمومی (منوی اصلی، بازگشت، انصراف)
- User: دکمه‌های کاربری (منوی کاربر، اقدامات کاربر)
- Form: دکمه‌های فرم (انتخاب فرم، ناوبری فرم)
- Admin: دکمه‌های پنل مدیریت (منوی اصلی ادمین، کیبوردهای ماژول‌ها)
- Payment: دکمه‌های پرداخت (شروع پرداخت، نتیجه پرداخت)
- Help: دکمه‌های راهنما
- Order: دکمه‌های سفارش (فیلترها، اقدامات)
- Broadcast: دکمه‌های ارسال گروهی
- Coupon: دکمه‌های کوپن
- Ticket: دکمه‌های تیکت
"""

# ----------------------------------------------
# Import Common Keyboards
# ----------------------------------------------
from my_bot.presentation.keyboards.common.main_menu import get_main_menu_keyboard
from my_bot.presentation.keyboards.common.back_buttons import (
    get_back_button,
    get_back_to_main_button,
)
from my_bot.presentation.keyboards.common.cancel_buttons import get_cancel_button

# ----------------------------------------------
# Import User Keyboards
# ----------------------------------------------
from my_bot.presentation.keyboards.user.user_menu import get_user_menu_keyboard
from my_bot.presentation.keyboards.user.user_actions import get_user_actions_keyboard

# ----------------------------------------------
# Import Form Keyboards
# ----------------------------------------------
from my_bot.presentation.keyboards.form.form_choice import get_form_choice_keyboard
from my_bot.presentation.keyboards.form.form_navigation import get_form_navigation_keyboard

# ----------------------------------------------
# Import Admin Keyboards
# ----------------------------------------------
from my_bot.presentation.keyboards.admin.admin_keyboards import get_admin_main_keyboard

# ----------------------------------------------
# Import Payment Keyboards
# ----------------------------------------------
from my_bot.presentation.keyboards.payment.payment_keyboards import (
    get_payment_keyboard,
    get_payment_result_keyboard,
)
from my_bot.presentation.keyboards.payment.coupon_keyboards import get_coupon_keyboard

# ----------------------------------------------
# Import Help Keyboards
# ----------------------------------------------
from my_bot.presentation.keyboards.help.help_keyboards import get_help_menu_keyboard

# ----------------------------------------------
# Import Order Keyboards
# ----------------------------------------------
from my_bot.presentation.keyboards.order.order_filters import get_order_filters_keyboard
from my_bot.presentation.keyboards.order.order_actions import get_order_actions_keyboard

# ----------------------------------------------
# Import Broadcast Keyboards
# ----------------------------------------------
from my_bot.presentation.keyboards.broadcast.broadcast_keyboards import (
    get_broadcast_main_keyboard,
    get_broadcast_filter_keyboard,
    get_broadcast_status_keyboard,
)

# ----------------------------------------------
# Import Ticket Keyboards
# ----------------------------------------------
from my_bot.presentation.keyboards.ticket.ticket_keyboards import get_ticket_keyboard

# ----------------------------------------------
# Import Coupon Keyboards
# ----------------------------------------------
from my_bot.presentation.keyboards.coupon.coupon_keyboards import get_coupon_list_keyboard


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # Common
    "get_main_menu_keyboard",
    "get_back_button",
    "get_back_to_main_button",
    "get_cancel_button",

    # User
    "get_user_menu_keyboard",
    "get_user_actions_keyboard",

    # Form
    "get_form_choice_keyboard",
    "get_form_navigation_keyboard",

    # Admin
    "get_admin_main_keyboard",

    # Payment
    "get_payment_keyboard",
    "get_payment_result_keyboard",
    "get_coupon_keyboard",

    # Help
    "get_help_menu_keyboard",

    # Order
    "get_order_filters_keyboard",
    "get_order_actions_keyboard",

    # Broadcast
    "get_broadcast_main_keyboard",
    "get_broadcast_filter_keyboard",
    "get_broadcast_status_keyboard",

    # Ticket
    "get_ticket_keyboard",

    # Coupon
    "get_coupon_list_keyboard",
]