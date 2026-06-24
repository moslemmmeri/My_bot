# my_bot_project/src/my_bot/presentation/web_api/schemas/webhook_schemas.py
"""
Schemaهای وب‌هوک (Webhook Schemas).

این ماژول شامل مدل‌های Pydantic برای اعتبارسنجی و سریال‌سازی
داده‌های وب‌هوک دریافتی از سرویس‌های خارجی (مانند درگاه پرداخت،
تلگرام و ...) است.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator


class WebhookRequestSchema(BaseModel):
    """
    Schema کلی برای درخواست وب‌هوک.

    Attributes:
        event: نوع رویداد (مثلاً 'payment.success', 'order.created').
        source: منبع وب‌هوک (مثلاً 'zarinpal', 'telegram').
        data: داده‌های اصلی وب‌هوک.
        timestamp: زمان رویداد (اختیاری).
        signature: امضای دیجیتال برای اعتبارسنجی (اختیاری).
        metadata: داده‌های اضافی (اختیاری).
    """
    event: str = Field(..., description="نوع رویداد")
    source: str = Field(..., description="منبع وب‌هوک")
    data: Dict[str, Any] = Field(..., description="داده‌های اصلی وب‌هوک")
    timestamp: Optional[datetime] = Field(
        None,
        description="زمان رویداد (فرمت ISO 8601)"
    )
    signature: Optional[str] = Field(
        None,
        description="امضای دیجیتال برای اعتبارسنجی"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="داده‌های اضافی"
    )

    @validator("event")
    def validate_event(cls, v: str) -> str:
        """اعتبارسنجی نوع رویداد (نباید خالی باشد)."""
        if not v or not v.strip():
            raise ValueError("نوع رویداد نمی‌تواند خالی باشد.")
        return v.strip()

    @validator("source")
    def validate_source(cls, v: str) -> str:
        """اعتبارسنجی منبع (نباید خالی باشد)."""
        if not v or not v.strip():
            raise ValueError("منبع وب‌هوک نمی‌تواند خالی باشد.")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "event": "payment.success",
                "source": "zarinpal",
                "data": {
                    "transaction_id": "A123456789",
                    "amount": 100000,
                    "ref_id": "7890",
                },
                "timestamp": "2024-12-25T14:30:00",
                "signature": "abc123def456",
                "metadata": {"ip": "192.168.1.1"},
            }
        }


class WebhookResponseSchema(BaseModel):
    """
    Schema پاسخ به درخواست وب‌هوک.

    Attributes:
        status: وضعیت پردازش ('success', 'failed', 'pending').
        message: پیام توضیحی.
        data: داده‌های بازگشتی (اختیاری).
        error: اطلاعات خطا (در صورت وجود).
    """
    status: str = Field(
        ...,
        description="وضعیت پردازش (success, failed, pending)"
    )
    message: str = Field(
        ...,
        description="پیام توضیحی"
    )
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="داده‌های بازگشتی"
    )
    error: Optional[Dict[str, str]] = Field(
        None,
        description="اطلاعات خطا (در صورت وجود)"
    )

    @validator("status")
    def validate_status(cls, v: str) -> str:
        """اعتبارسنجی وضعیت (فقط مقادیر مجاز)."""
        allowed = {"success", "failed", "pending"}
        if v not in allowed:
            raise ValueError(f"وضعیت باید یکی از {allowed} باشد.")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Webhook processed successfully.",
                "data": {"processed_id": 12345},
                "error": None,
            }
        }


class WebhookStatusSchema(BaseModel):
    """
    Schema وضعیت وب‌هوک برای گزارش‌گیری.

    Attributes:
        webhook_url: آدرس وب‌هوک ثبت‌شده.
        is_active: فعال بودن وب‌هوک.
        last_success: زمان آخرین موفقیت.
        last_error: زمان آخرین خطا.
        error_count: تعداد خطاها.
        total_calls: تعداد کل فراخوانی‌ها.
        pending_count: تعداد درخواست‌های در انتظار.
    """
    webhook_url: Optional[str] = Field(
        None,
        description="آدرس وب‌هوک ثبت‌شده"
    )
    is_active: bool = Field(
        False,
        description="فعال بودن وب‌هوک"
    )
    last_success: Optional[datetime] = Field(
        None,
        description="زمان آخرین موفقیت"
    )
    last_error: Optional[datetime] = Field(
        None,
        description="زمان آخرین خطا"
    )
    error_count: int = Field(
        0,
        description="تعداد خطاها"
    )
    total_calls: int = Field(
        0,
        description="تعداد کل فراخوانی‌ها"
    )
    pending_count: int = Field(
        0,
        description="تعداد درخواست‌های در انتظار"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "webhook_url": "https://example.com/webhook",
                "is_active": True,
                "last_success": "2024-12-25T14:30:00",
                "last_error": None,
                "error_count": 0,
                "total_calls": 150,
                "pending_count": 2,
            }
        }


class PaymentWebhookSchema(WebhookRequestSchema):
    """
    Schema اختصاصی برای وب‌هوک پرداخت.

    Attributes:
        transaction_id: شناسه تراکنش.
        amount: مبلغ پرداختی.
        status: وضعیت پرداخت (success, failed, refunded).
        ref_id: کد رهگیری (اختیاری).
        card_pan: شماره کارت (ماسک شده) (اختیاری).
    """
    transaction_id: str = Field(..., description="شناسه تراکنش")
    amount: float = Field(..., description="مبلغ پرداختی")
    status: str = Field(..., description="وضعیت پرداخت")
    ref_id: Optional[str] = Field(None, description="کد رهگیری")
    card_pan: Optional[str] = Field(None, description="شماره کارت (ماسک شده)")

    @validator("status")
    def validate_payment_status(cls, v: str) -> str:
        """اعتبارسنجی وضعیت پرداخت."""
        allowed = {"success", "failed", "refunded", "pending"}
        if v not in allowed:
            raise ValueError(f"وضعیت پرداخت باید یکی از {allowed} باشد.")
        return v

    @validator("amount")
    def validate_amount(cls, v: float) -> float:
        """اعتبارسنجی مبلغ (باید مثبت باشد)."""
        if v <= 0:
            raise ValueError("مبلغ پرداخت باید مثبت باشد.")
        return v


class TelegramWebhookSchema(WebhookRequestSchema):
    """
    Schema اختصاصی برای وب‌هوک تلگرام.

    Attributes:
        update_id: شناسه به‌روزرسانی.
        message: پیام (اختیاری).
        callback_query: کالبک (اختیاری).
        inline_query: کوئری اینلاین (اختیاری).
        # سایر فیلدهای تلگرام
    """
    update_id: int = Field(..., description="شناسه به‌روزرسانی")
    message: Optional[Dict[str, Any]] = Field(None, description="پیام")
    callback_query: Optional[Dict[str, Any]] = Field(None, description="کالبک")
    inline_query: Optional[Dict[str, Any]] = Field(None, description="کوئری اینلاین")
    # می‌توان فیلدهای دیگر را نیز اضافه کرد

    @validator("update_id")
    def validate_update_id(cls, v: int) -> int:
        """اعتبارسنجی شناسه به‌روزرسانی (باید مثبت باشد)."""
        if v <= 0:
            raise ValueError("شناسه به‌روزرسانی باید مثبت باشد.")
        return v