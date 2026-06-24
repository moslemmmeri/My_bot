# my_bot_project/src/my_bot/application/__init__.py
"""
ماژول Application (لایه کاربرد).

این ماژول شامل منطق بیزینس و موارد استفاده (Use Cases) سیستم است.
لایه کاربرد به‌عنوان پل ارتباطی بین لایه دامنه (Domain) و لایه ارائه (Presentation)
عمل می‌کند و مسئولیت هماهنگی عملیات مختلف را بر عهده دارد.

اجزای اصلی:
- Services: سرویس‌های اصلی سیستم (User, Order, Payment, Form, Broadcast, Ticket, Coupon, Analytics)
- DTOs: اشیاء انتقال داده برای تبادل اطلاعات بین لایه‌ها
- Use Cases: موارد استفاده (سناریوهای خاص) سیستم
"""

# ----------------------------------------------
# Import Services
# ----------------------------------------------
from my_bot.application.services.user.user_registration import UserRegistrationService
from my_bot.application.services.user.user_profile import UserProfileService
from my_bot.application.services.user.user_level_upgrade import UserLevelUpgradeService

from my_bot.application.services.order.order_creation import OrderCreationService
from my_bot.application.services.order.order_status_update import OrderStatusUpdateService
from my_bot.application.services.order.order_history import OrderHistoryService

from my_bot.application.services.payment.payment_gateway import PaymentGatewayService
from my_bot.application.services.payment.payment_verification import PaymentVerificationService
from my_bot.application.services.payment.payment_webhook import PaymentWebhookService

from my_bot.application.services.form.form_builder import FormBuilderService
from my_bot.application.services.form.form_submission import FormSubmissionService
from my_bot.application.services.form.form_analytics import FormAnalyticsService

from my_bot.application.services.broadcast.broadcast_sender import BroadcastSenderService
from my_bot.application.services.broadcast.broadcast_filter import BroadcastFilterService
from my_bot.application.services.broadcast.broadcast_scheduler import BroadcastSchedulerService

from my_bot.application.services.ticket.ticket_creation import TicketCreationService
from my_bot.application.services.ticket.ticket_assignment import TicketAssignmentService
from my_bot.application.services.ticket.ticket_resolution import TicketResolutionService

from my_bot.application.services.coupon.coupon_generation import CouponGenerationService
from my_bot.application.services.coupon.coupon_validation import CouponValidationService

from my_bot.application.services.analytics.user_behavior import UserBehaviorAnalyticsService
from my_bot.application.services.analytics.order_statistics import OrderStatisticsService
from my_bot.application.services.analytics.ab_testing import ABTestingService

# ----------------------------------------------
# Import DTOs
# ----------------------------------------------
from my_bot.application.dtos.user_dto import (
    UserCreateDTO,
    UserUpdateDTO,
    UserResponseDTO,
    UserProfileDTO,
)
from my_bot.application.dtos.order_dto import (
    OrderCreateDTO,
    OrderUpdateDTO,
    OrderResponseDTO,
    OrderItemDTO,
)
from my_bot.application.dtos.payment_dto import (
    PaymentCreateDTO,
    PaymentUpdateDTO,
    PaymentResponseDTO,
    PaymentCallbackDTO,
)
from my_bot.application.dtos.coupon_dto import (
    CouponCreateDTO,
    CouponUpdateDTO,
    CouponResponseDTO,
    CouponValidateDTO,
)
from my_bot.application.dtos.form_dto import (
    FormCreateDTO,
    FormUpdateDTO,
    FormResponseDTO,
    FormSubmitDTO,
)
from my_bot.application.dtos.broadcast_dto import (
    BroadcastCreateDTO,
    BroadcastUpdateDTO,
    BroadcastResponseDTO,
    BroadcastFilterDTO,
)

# ----------------------------------------------
# Import Use Cases
# ----------------------------------------------
from my_bot.application.use_cases.user.register_user import RegisterUserUseCase
from my_bot.application.use_cases.user.update_profile import UpdateProfileUseCase

from my_bot.application.use_cases.order.create_order import CreateOrderUseCase
from my_bot.application.use_cases.order.cancel_order import CancelOrderUseCase

from my_bot.application.use_cases.payment.initiate_payment import InitiatePaymentUseCase
from my_bot.application.use_cases.payment.confirm_payment import ConfirmPaymentUseCase

# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # Services
    "UserRegistrationService",
    "UserProfileService",
    "UserLevelUpgradeService",
    "OrderCreationService",
    "OrderStatusUpdateService",
    "OrderHistoryService",
    "PaymentGatewayService",
    "PaymentVerificationService",
    "PaymentWebhookService",
    "FormBuilderService",
    "FormSubmissionService",
    "FormAnalyticsService",
    "BroadcastSenderService",
    "BroadcastFilterService",
    "BroadcastSchedulerService",
    "TicketCreationService",
    "TicketAssignmentService",
    "TicketResolutionService",
    "CouponGenerationService",
    "CouponValidationService",
    "UserBehaviorAnalyticsService",
    "OrderStatisticsService",
    "ABTestingService",

    # DTOs
    "UserCreateDTO",
    "UserUpdateDTO",
    "UserResponseDTO",
    "UserProfileDTO",
    "OrderCreateDTO",
    "OrderUpdateDTO",
    "OrderResponseDTO",
    "OrderItemDTO",
    "PaymentCreateDTO",
    "PaymentUpdateDTO",
    "PaymentResponseDTO",
    "PaymentCallbackDTO",
    "CouponCreateDTO",
    "CouponUpdateDTO",
    "CouponResponseDTO",
    "CouponValidateDTO",
    "FormCreateDTO",
    "FormUpdateDTO",
    "FormResponseDTO",
    "FormSubmitDTO",
    "BroadcastCreateDTO",
    "BroadcastUpdateDTO",
    "BroadcastResponseDTO",
    "BroadcastFilterDTO",

    # Use Cases
    "RegisterUserUseCase",
    "UpdateProfileUseCase",
    "CreateOrderUseCase",
    "CancelOrderUseCase",
    "InitiatePaymentUseCase",
    "ConfirmPaymentUseCase",
]