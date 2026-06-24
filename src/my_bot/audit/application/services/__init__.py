# my_bot_project/src/my_bot/application/services/__init__.py
"""
ماژول سرویس‌های لایه کاربرد (Application Services).

این ماژول شامل تمام سرویس‌های اصلی سیستم است که منطق بیزینس را پیاده‌سازی می‌کنند.
هر سرویس مسئولیت یک حوزه خاص از سیستم را بر عهده دارد و از لایه دامنه
برای دسترسی به موجودیت‌ها و اینترفیس‌ها استفاده می‌کند.

سرویس‌های موجود:
- User Services: مدیریت کاربران (ثبت‌نام، پروفایل، ارتقاء سطح)
- Order Services: مدیریت سفارشات (ایجاد، به‌روزرسانی وضعیت، تاریخچه)
- Payment Services: مدیریت پرداخت (درگاه، تأیید، وب‌هوک)
- Form Services: مدیریت فرم‌ها (ساخت، ارسال، تحلیل)
- Broadcast Services: ارسال گروهی (ارسال، فیلتر، زمان‌بندی)
- Ticket Services: مدیریت تیکت‌ها (ایجاد، تخصیص، حل)
- Coupon Services: مدیریت کوپن‌ها (تولید، اعتبارسنجی)
- Analytics Services: تحلیل داده‌ها (رفتار کاربر، آمار سفارشات، تست A/B)
"""

# ----------------------------------------------
# Import User Services
# ----------------------------------------------
from my_bot.application.services.user.user_registration import UserRegistrationService
from my_bot.application.services.user.user_profile import UserProfileService
from my_bot.application.services.user.user_level_upgrade import UserLevelUpgradeService

# ----------------------------------------------
# Import Order Services
# ----------------------------------------------
from my_bot.application.services.order.order_creation import OrderCreationService
from my_bot.application.services.order.order_status_update import OrderStatusUpdateService
from my_bot.application.services.order.order_history import OrderHistoryService

# ----------------------------------------------
# Import Payment Services
# ----------------------------------------------
from my_bot.application.services.payment.payment_gateway import PaymentGatewayService
from my_bot.application.services.payment.payment_verification import PaymentVerificationService
from my_bot.application.services.payment.payment_webhook import PaymentWebhookService

# ----------------------------------------------
# Import Form Services
# ----------------------------------------------
from my_bot.application.services.form.form_builder import FormBuilderService
from my_bot.application.services.form.form_submission import FormSubmissionService
from my_bot.application.services.form.form_analytics import FormAnalyticsService

# ----------------------------------------------
# Import Broadcast Services
# ----------------------------------------------
from my_bot.application.services.broadcast.broadcast_sender import BroadcastSenderService
from my_bot.application.services.broadcast.broadcast_filter import BroadcastFilterService
from my_bot.application.services.broadcast.broadcast_scheduler import BroadcastSchedulerService

# ----------------------------------------------
# Import Ticket Services
# ----------------------------------------------
from my_bot.application.services.ticket.ticket_creation import TicketCreationService
from my_bot.application.services.ticket.ticket_assignment import TicketAssignmentService
from my_bot.application.services.ticket.ticket_resolution import TicketResolutionService

# ----------------------------------------------
# Import Coupon Services
# ----------------------------------------------
from my_bot.application.services.coupon.coupon_generation import CouponGenerationService
from my_bot.application.services.coupon.coupon_validation import CouponValidationService

# ----------------------------------------------
# Import Analytics Services
# ----------------------------------------------
from my_bot.application.services.analytics.user_behavior import UserBehaviorAnalyticsService
from my_bot.application.services.analytics.order_statistics import OrderStatisticsService
from my_bot.application.services.analytics.ab_testing import ABTestingService


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # User Services
    "UserRegistrationService",
    "UserProfileService",
    "UserLevelUpgradeService",

    # Order Services
    "OrderCreationService",
    "OrderStatusUpdateService",
    "OrderHistoryService",

    # Payment Services
    "PaymentGatewayService",
    "PaymentVerificationService",
    "PaymentWebhookService",

    # Form Services
    "FormBuilderService",
    "FormSubmissionService",
    "FormAnalyticsService",

    # Broadcast Services
    "BroadcastSenderService",
    "BroadcastFilterService",
    "BroadcastSchedulerService",

    # Ticket Services
    "TicketCreationService",
    "TicketAssignmentService",
    "TicketResolutionService",

    # Coupon Services
    "CouponGenerationService",
    "CouponValidationService",

    # Analytics Services
    "UserBehaviorAnalyticsService",
    "OrderStatisticsService",
    "ABTestingService",
]