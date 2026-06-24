# my_bot_project/src/my_bot/application/use_cases/__init__.py
"""
ماژول موارد استفاده (Use Cases).

این ماژول شامل موارد استفاده (Use Cases) سیستم است که سناریوهای خاص
و عملیات‌های دقیق کسب‌وکار را encapsulate می‌کنند. هر Use Case
یک عملیات خاص را با ورودی و خروجی مشخص پیاده‌سازی می‌کند.

موارد استفاده موجود:
- User Use Cases: ثبت‌نام و به‌روزرسانی پروفایل کاربر
- Order Use Cases: ایجاد و لغو سفارش
- Payment Use Cases: شروع و تأیید پرداخت
"""

# ----------------------------------------------
# Import User Use Cases
# ----------------------------------------------
from my_bot.application.use_cases.user.register_user import RegisterUserUseCase
from my_bot.application.use_cases.user.update_profile import UpdateProfileUseCase

# ----------------------------------------------
# Import Order Use Cases
# ----------------------------------------------
from my_bot.application.use_cases.order.create_order import CreateOrderUseCase
from my_bot.application.use_cases.order.cancel_order import CancelOrderUseCase

# ----------------------------------------------
# Import Payment Use Cases
# ----------------------------------------------
from my_bot.application.use_cases.payment.initiate_payment import InitiatePaymentUseCase
from my_bot.application.use_cases.payment.confirm_payment import ConfirmPaymentUseCase


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # User Use Cases
    "RegisterUserUseCase",
    "UpdateProfileUseCase",

    # Order Use Cases
    "CreateOrderUseCase",
    "CancelOrderUseCase",

    # Payment Use Cases
    "InitiatePaymentUseCase",
    "ConfirmPaymentUseCase",
]