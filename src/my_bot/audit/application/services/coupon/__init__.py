# my_bot_project/src/my_bot/application/services/coupon/__init__.py
"""
ماژول سرویس‌های کوپن تخفیف (Coupon Services).

این ماژول شامل سرویس‌های مربوط به مدیریت کوپن‌های تخفیف در سیستم است:
- CouponGenerationService: تولید و مدیریت کوپن‌های جدید
- CouponValidationService: اعتبارسنجی و اعمال کوپن‌ها
"""

from my_bot.application.services.coupon.coupon_generation import CouponGenerationService
from my_bot.application.services.coupon.coupon_validation import CouponValidationService

__all__ = [
    "CouponGenerationService",
    "CouponValidationService",
]