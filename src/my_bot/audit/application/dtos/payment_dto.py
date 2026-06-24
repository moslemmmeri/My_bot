# my_bot_project/src/my_bot/application/dtos/payment_dto.py
"""
DTOهای مربوط به پرداخت (Payment DTOs).

این ماژول شامل اشیاء انتقال داده (Data Transfer Objects) برای مدیریت
تراکنش‌های پرداخت در سیستم است. تمام DTOها از Pydantic برای اعتبارسنجی داده‌ها
استفاده می‌کنند و شامل نوع‌دهی کامل (Type Hints) هستند.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from my_bot.core.constants.payment_statuses import PaymentStatus


class PaymentCreateDTO(BaseModel):
    """
    DTO برای ایجاد پرداخت جدید.

    Attributes:
        user_id: شناسه کاربر پرداخت‌کننده (اجباری).
        order_id: شناسه سفارش مرتبط (اختیاری).
        amount: مبلغ پرداختی (اجباری، باید مثبت باشد).
        currency: واحد پول (پیش‌فرض: IRR).
        gateway: نام درگاه پرداخت (پیش‌فرض: mock).
        description: توضیحات پرداخت (اختیاری).
        callback_url: آدرس بازگشت پس از پرداخت (اختیاری).
        metadata: داده‌های اضافی (اختیاری).
    """
    user_id: int = Field(..., gt=0, description="شناسه کاربر پرداخت‌کننده")
    order_id: Optional[str] = Field(None, description="شناسه سفارش مرتبط")
    amount: float = Field(..., gt=0, description="مبلغ پرداختی")
    currency: str = Field("IRR", max_length=3, description="واحد پول")
    gateway: str = Field("mock", description="نام درگاه پرداخت")
    description: Optional[str] = Field(None, max_length=500, description="توضیحات پرداخت")
    callback_url: Optional[str] = Field(None, description="آدرس بازگشت پس از پرداخت")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        """اعتبارسنجی مبلغ پرداخت (باید مثبت باشد)."""
        if v <= 0:
            raise ValueError("مبلغ پرداخت باید مثبت باشد.")
        return v


class PaymentUpdateDTO(BaseModel):
    """
    DTO برای به‌روزرسانی پرداخت.

    Attributes:
        status: وضعیت جدید پرداخت (اختیاری).
        transaction_id: شناسه تراکنش در درگاه (اختیاری).
        tracking_code: کد رهگیری جدید (اختیاری).
        reference_id: شناسه مرجع جدید (اختیاری).
        error_message: پیام خطا (اختیاری).
        metadata: داده‌های اضافی جدید (اختیاری).
    """
    status: Optional[PaymentStatus] = Field(None, description="وضعیت جدید پرداخت")
    transaction_id: Optional[str] = Field(None, max_length=100, description="شناسه تراکنش در درگاه")
    tracking_code: Optional[str] = Field(None, max_length=100, description="کد رهگیری")
    reference_id: Optional[str] = Field(None, max_length=100, description="شناسه مرجع")
    error_message: Optional[str] = Field(None, max_length=500, description="پیام خطا")
    metadata: Optional[Dict[str, Any]] = Field(None, description="داده‌های اضافی جدید")


class PaymentResponseDTO(BaseModel):
    """
    DTO برای پاسخ اطلاعات پرداخت.

    Attributes:
        id: شناسه تراکنش.
        user_id: شناسه کاربر.
        order_id: شناسه سفارش (اختیاری).
        amount: مبلغ پرداختی.
        currency: واحد پول.
        status: وضعیت پرداخت.
        gateway: نام درگاه پرداخت.
        transaction_id: شناسه تراکنش در درگاه (اختیاری).
        tracking_code: کد رهگیری (اختیاری).
        reference_id: شناسه مرجع (اختیاری).
        paid_at: زمان پرداخت موفق (اختیاری).
        error_message: پیام خطا (اختیاری).
        created_at: زمان ایجاد.
        updated_at: زمان آخرین به‌روزرسانی.
        metadata: داده‌های اضافی.
    """
    id: Optional[int] = Field(None, description="شناسه تراکنش")
    user_id: int = Field(..., description="شناسه کاربر")
    order_id: Optional[str] = Field(None, description="شناسه سفارش")
    amount: float = Field(..., description="مبلغ پرداختی")
    currency: str = Field("IRR", description="واحد پول")
    status: PaymentStatus = Field(PaymentStatus.PENDING, description="وضعیت پرداخت")
    gateway: str = Field("mock", description="نام درگاه پرداخت")
    transaction_id: Optional[str] = Field(None, description="شناسه تراکنش در درگاه")
    tracking_code: Optional[str] = Field(None, description="کد رهگیری")
    reference_id: Optional[str] = Field(None, description="شناسه مرجع")
    paid_at: Optional[datetime] = Field(None, description="زمان پرداخت موفق")
    error_message: Optional[str] = Field(None, description="پیام خطا")
    created_at: datetime = Field(default_factory=datetime.now, description="زمان ایجاد")
    updated_at: datetime = Field(default_factory=datetime.now, description="زمان آخرین به‌روزرسانی")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, payment) -> "PaymentResponseDTO":
        """
        ساخت DTO از موجودیت پرداخت.

        Args:
            payment: موجودیت Payment.

        Returns:
            PaymentResponseDTO: DTO ساخته‌شده.
        """
        return cls(
            id=payment.id,
            user_id=payment.user_id,
            order_id=payment.order_id,
            amount=float(payment.amount.amount),
            currency=payment.amount.currency,
            status=payment.status,
            gateway=payment.gateway,
            transaction_id=payment.transaction_id,
            tracking_code=payment.tracking_code,
            reference_id=payment.reference_id,
            paid_at=payment.paid_at,
            error_message=payment.error_message,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            metadata=payment.metadata,
        )

    def get_formatted_amount(self) -> str:
        """
        دریافت مبلغ به‌صورت فرمت‌شده.

        Returns:
            str: مبلغ فرمت‌شده با واحد پول.
        """
        if self.currency == "IRR":
            toman = self.amount / 10
            return f"{toman:,.0f} تومان"
        return f"{self.amount:,.2f} {self.currency}"

    def is_success(self) -> bool:
        """بررسی موفق بودن پرداخت."""
        return self.status == PaymentStatus.SUCCESS

    def is_failed(self) -> bool:
        """بررسی ناموفق بودن پرداخت."""
        return self.status.is_failed()

    def is_pending(self) -> bool:
        """بررسی در انتظار بودن پرداخت."""
        return self.status.is_pending()


class PaymentCallbackDTO(BaseModel):
    """
    DTO برای داده‌های بازگشتی از درگاه پرداخت.

    Attributes:
        transaction_id: شناسه تراکنش در درگاه (اجباری).
        reference_id: شناسه مرجع (اختیاری).
        tracking_code: کد رهگیری (اختیاری).
        status: وضعیت پرداخت از دید درگاه (اختیاری).
        metadata: داده‌های خام دریافتی (اختیاری).
    """
    transaction_id: str = Field(..., description="شناسه تراکنش در درگاه")
    reference_id: Optional[str] = Field(None, description="شناسه مرجع")
    tracking_code: Optional[str] = Field(None, description="کد رهگیری")
    status: str = Field("success", description="وضعیت پرداخت از دید درگاه")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های خام دریافتی")

    @field_validator("transaction_id")
    @classmethod
    def validate_transaction_id(cls, v: str) -> str:
        """اعتبارسنجی شناسه تراکنش."""
        if not v or not v.strip():
            raise ValueError("شناسه تراکنش نمی‌تواند خالی باشد.")
        return v.strip()


class PaymentWebhookDTO(BaseModel):
    """
    DTO برای پردازش وب‌هوک دریافتی از درگاه پرداخت.

    Attributes:
        gateway: نام درگاه پرداخت (اجباری).
        transaction_id: شناسه تراکنش (اجباری).
        event_type: نوع رویداد (اجباری).
        status: وضعیت پرداخت (اختیاری).
        amount: مبلغ پرداختی (اختیاری).
        currency: واحد پول (اختیاری).
        tracking_code: کد رهگیری (اختیاری).
        message: پیام (اختیاری).
        raw_data: داده‌های خام دریافتی (اجباری).
        success: وضعیت پردازش وب‌هوک (پیش‌فرض False).
        error: پیام خطا (اختیاری).
    """
    gateway: str = Field(..., description="نام درگاه پرداخت")
    transaction_id: str = Field(..., description="شناسه تراکنش")
    event_type: str = Field(..., description="نوع رویداد")
    status: Optional[str] = Field(None, description="وضعیت پرداخت")
    amount: Optional[float] = Field(None, description="مبلغ پرداختی")
    currency: str = Field("IRR", description="واحد پول")
    tracking_code: Optional[str] = Field(None, description="کد رهگیری")
    message: Optional[str] = Field(None, description="پیام")
    raw_data: Dict[str, Any] = Field(..., description="داده‌های خام دریافتی")
    success: bool = Field(False, description="وضعیت پردازش وب‌هوک")
    error: Optional[str] = Field(None, description="پیام خطا")

    @field_validator("transaction_id")
    @classmethod
    def validate_transaction_id(cls, v: str) -> str:
        """اعتبارسنجی شناسه تراکنش."""
        if not v or not v.strip():
            raise ValueError("شناسه تراکنش نمی‌تواند خالی باشد.")
        return v.strip()


class PaymentGatewayResponseDTO(BaseModel):
    """
    DTO برای پاسخ درگاه پرداخت.

    Attributes:
        success: آیا عملیات با موفقیت انجام شد.
        transaction_id: شناسه تراکنش در درگاه (اختیاری).
        payment_url: لینک پرداخت (اختیاری).
        message: پیام (اختیاری).
        tracking_code: کد رهگیری (اختیاری).
        reference_id: شناسه مرجع (اختیاری).
        gateway_data: داده‌های اضافی از درگاه (اختیاری).
    """
    success: bool = Field(..., description="آیا عملیات با موفقیت انجام شد")
    transaction_id: Optional[str] = Field(None, description="شناسه تراکنش در درگاه")
    payment_url: Optional[str] = Field(None, description="لینک پرداخت")
    message: Optional[str] = Field(None, description="پیام")
    tracking_code: Optional[str] = Field(None, description="کد رهگیری")
    reference_id: Optional[str] = Field(None, description="شناسه مرجع")
    gateway_data: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی از درگاه")

    class Config:
        from_attributes = True