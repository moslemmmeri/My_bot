# my_bot_project/src/my_bot/infrastructure/database/models/__init__.py
"""
ماژول مدل‌های SQLAlchemy.

این ماژول شامل تمام مدل‌های SQLAlchemy برای تعریف جداول دیتابیس است.
هر مدل معادل یک موجودیت در لایه دامنه است و نگاشت (Mapping) بین
لایه دامنه و دیتابیس را انجام می‌دهد.

مدل‌های موجود:
- UserModel: کاربران
- OrderModel: سفارشات
- OrderItemModel: آیتم‌های سفارش
- PaymentModel: تراکنش‌های پرداخت
- CouponModel: کوپن‌های تخفیف
- FormModel: فرم‌ها
- FormFieldModel: فیلدهای فرم
- FormResponseModel: پاسخ‌های فرم
- FormSubmissionLogModel: لاگ ارسال فرم
- TicketModel: تیکت‌های پشتیبانی
- TicketMessageModel: پیام‌های تیکت
- BroadcastModel: ارسال‌های گروهی
- FeedbackModel: بازخوردها
- ABTestModel: تست‌های A/B
- ABTestVariantModel: نسخه‌های تست A/B
- AuditLogModel: لاگ‌های حسابرسی
- FeatureFlagModel: فیچر فلاگ‌ها
- SettingModel: تنظیمات سیستم
"""

from sqlalchemy.ext.declarative import declarative_base

# ایجاد کلاس پایه برای مدل‌ها
Base = declarative_base()

# ----------------------------------------------
# Import all models to register them with Base
# ----------------------------------------------
from my_bot.infrastructure.database.models.user_model import UserModel
from my_bot.infrastructure.database.models.order_model import OrderModel
from my_bot.infrastructure.database.models.order_item_model import OrderItemModel
from my_bot.infrastructure.database.models.payment_model import PaymentModel
from my_bot.infrastructure.database.models.coupon_model import CouponModel
from my_bot.infrastructure.database.models.form_model import FormModel
from my_bot.infrastructure.database.models.form_field_model import FormFieldModel
from my_bot.infrastructure.database.models.form_response_model import FormResponseModel
from my_bot.infrastructure.database.models.form_submission_log_model import FormSubmissionLogModel
from my_bot.infrastructure.database.models.ticket_model import TicketModel
from my_bot.infrastructure.database.models.ticket_message_model import TicketMessageModel
from my_bot.infrastructure.database.models.broadcast_model import BroadcastModel
from my_bot.infrastructure.database.models.feedback_model import FeedbackModel
from my_bot.infrastructure.database.models.ab_test_model import ABTestModel
from my_bot.infrastructure.database.models.ab_test_variant_model import ABTestVariantModel
from my_bot.infrastructure.database.models.audit_log_model import AuditLogModel
from my_bot.infrastructure.database.models.feature_flag_model import FeatureFlagModel
from my_bot.infrastructure.database.models.setting_model import SettingModel


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    "Base",
    "UserModel",
    "OrderModel",
    "OrderItemModel",
    "PaymentModel",
    "CouponModel",
    "FormModel",
    "FormFieldModel",
    "FormResponseModel",
    "FormSubmissionLogModel",
    "TicketModel",
    "TicketMessageModel",
    "BroadcastModel",
    "FeedbackModel",
    "ABTestModel",
    "ABTestVariantModel",
    "AuditLogModel",
    "FeatureFlagModel",
    "SettingModel",
]