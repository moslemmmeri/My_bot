# my_bot_project/src/my_bot/application/dtos/__init__.py
"""
ماژول DTOهای لایه کاربرد (Application DTOs).

این ماژول شامل اشیاء انتقال داده (Data Transfer Objects) است که برای
تبادل اطلاعات بین لایه‌های مختلف استفاده می‌شوند. DTOها ساختار داده‌های
ورودی و خروجی سرویس‌ها را تعریف می‌کنند و از Pydantic برای اعتبارسنجی استفاده می‌کنند.

DTOهای موجود:
- User DTOs: مدیریت کاربران
- Order DTOs: مدیریت سفارشات
- Payment DTOs: مدیریت پرداخت
- Coupon DTOs: مدیریت کوپن‌ها
- Form DTOs: مدیریت فرم‌ها
- Broadcast DTOs: مدیریت ارسال گروهی
- Ticket DTOs: مدیریت تیکت‌ها
- ABTest DTOs: مدیریت تست‌های A/B
"""

# ----------------------------------------------
# Import User DTOs
# ----------------------------------------------
from my_bot.application.dtos.user_dto import (
    UserCreateDTO,
    UserUpdateDTO,
    UserResponseDTO,
    UserProfileDTO,
)

# ----------------------------------------------
# Import Order DTOs
# ----------------------------------------------
from my_bot.application.dtos.order_dto import (
    OrderCreateDTO,
    OrderUpdateDTO,
    OrderResponseDTO,
    OrderItemDTO,
)

# ----------------------------------------------
# Import Payment DTOs
# ----------------------------------------------
from my_bot.application.dtos.payment_dto import (
    PaymentCreateDTO,
    PaymentUpdateDTO,
    PaymentResponseDTO,
    PaymentCallbackDTO,
    PaymentWebhookDTO,
    PaymentGatewayResponseDTO,
)

# ----------------------------------------------
# Import Coupon DTOs
# ----------------------------------------------
from my_bot.application.dtos.coupon_dto import (
    CouponCreateDTO,
    CouponUpdateDTO,
    CouponResponseDTO,
    CouponValidateDTO,
)

# ----------------------------------------------
# Import Form DTOs
# ----------------------------------------------
from my_bot.application.dtos.form_dto import (
    FormCreateDTO,
    FormUpdateDTO,
    FormResponseDTO,
    FormSubmitDTO,
    FormAnalyticsDTO,
    FormFieldDTO,
)

# ----------------------------------------------
# Import Broadcast DTOs
# ----------------------------------------------
from my_bot.application.dtos.broadcast_dto import (
    BroadcastCreateDTO,
    BroadcastUpdateDTO,
    BroadcastResponseDTO,
    BroadcastFilterDTO,
)

# ----------------------------------------------
# Import Ticket DTOs
# ----------------------------------------------
from my_bot.application.dtos.ticket_dto import (
    TicketCreateDTO,
    TicketUpdateDTO,
    TicketResponseDTO,
    TicketMessageDTO,
)

# ----------------------------------------------
# Import ABTest DTOs
# ----------------------------------------------
from my_bot.application.dtos.ab_test_dto import (
    ABTestCreateDTO,
    ABTestUpdateDTO,
    ABTestResponseDTO,
    ABTestVariantDTO,
    ABTestResultDTO,
)


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # User DTOs
    "UserCreateDTO",
    "UserUpdateDTO",
    "UserResponseDTO",
    "UserProfileDTO",

    # Order DTOs
    "OrderCreateDTO",
    "OrderUpdateDTO",
    "OrderResponseDTO",
    "OrderItemDTO",

    # Payment DTOs
    "PaymentCreateDTO",
    "PaymentUpdateDTO",
    "PaymentResponseDTO",
    "PaymentCallbackDTO",
    "PaymentWebhookDTO",
    "PaymentGatewayResponseDTO",

    # Coupon DTOs
    "CouponCreateDTO",
    "CouponUpdateDTO",
    "CouponResponseDTO",
    "CouponValidateDTO",

    # Form DTOs
    "FormCreateDTO",
    "FormUpdateDTO",
    "FormResponseDTO",
    "FormSubmitDTO",
    "FormAnalyticsDTO",
    "FormFieldDTO",

    # Broadcast DTOs
    "BroadcastCreateDTO",
    "BroadcastUpdateDTO",
    "BroadcastResponseDTO",
    "BroadcastFilterDTO",

    # Ticket DTOs
    "TicketCreateDTO",
    "TicketUpdateDTO",
    "TicketResponseDTO",
    "TicketMessageDTO",

    # ABTest DTOs
    "ABTestCreateDTO",
    "ABTestUpdateDTO",
    "ABTestResponseDTO",
    "ABTestVariantDTO",
    "ABTestResultDTO",
]