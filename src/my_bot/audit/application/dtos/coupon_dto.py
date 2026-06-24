# my_bot_project/src/my_bot/application/dtos/coupon_dto.py
"""
DTOهای مربوط به کوپن تخفیف (Coupon DTOs).

این ماژول شامل اشیاء انتقال داده (Data Transfer Objects) برای مدیریت
کوپن‌های تخفیف در سیستم است. تمام DTOها از Pydantic برای اعتبارسنجی داده‌ها
استفاده می‌کنند و شامل نوع‌دهی کامل (Type Hints) هستند.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator

from my_bot.domain.entities.coupon import CouponType


class CouponCreateDTO(BaseModel):
    """
    DTO برای ایجاد کوپن جدید.

    Attributes:
        code: کد تخفیف (اختیاری، در صورت عدم ورود، خودکار تولید می‌شود).
        description: توضیحات کوپن (اختیاری).
        discount_type: نوع تخفیف (درصدی یا مبلغ ثابت).
        discount_value: مقدار تخفیف.
        currency: واحد پول (پیش‌فرض: IRR).
        min_order_amount: حداقل مبلغ سفارش (اختیاری).
        max_discount_amount: حداکثر مبلغ تخفیف (اختیاری).
        usage_limit: تعداد دفعات مجاز استفاده (اختیاری).
        user_usage_limit: حداکثر تعداد استفاده برای هر کاربر (پیش‌فرض ۱).
        valid_from: تاریخ شروع اعتبار (اختیاری، پیش‌فرض: زمان حال).
        valid_until: تاریخ پایان اعتبار (اختیاری).
        is_active: وضعیت فعال بودن (پیش‌فرض: True).
        applicable_products: لیست شناسه محصولات قابل اعمال (خالی یعنی همه).
        applicable_users: لیست شناسه کاربران مجاز (خالی یعنی همه).
        metadata: داده‌های اضافی (اختیاری).
    """
    code: Optional[str] = Field(None, max_length=50, description="کد تخفیف")
    description: Optional[str] = Field(None, max_length=500, description="توضیحات کوپن")
    discount_type: str = Field(..., description="نوع تخفیف (percentage یا fixed)")
    discount_value: float = Field(..., gt=0, description="مقدار تخفیف")
    currency: str = Field("IRR", max_length=3, description="واحد پول")
    min_order_amount: Optional[float] = Field(None, ge=0, description="حداقل مبلغ سفارش")
    max_discount_amount: Optional[float] = Field(None, ge=0, description="حداکثر مبلغ تخفیف")
    usage_limit: Optional[int] = Field(None, gt=0, description="تعداد دفعات مجاز استفاده")
    user_usage_limit: int = Field(1, gt=0, description="حداکثر تعداد استفاده برای هر کاربر")
    valid_from: Optional[datetime] = Field(None, description="تاریخ شروع اعتبار")
    valid_until: Optional[datetime] = Field(None, description="تاریخ پایان اعتبار")
    is_active: bool = Field(True, description="وضعیت فعال بودن")
    applicable_products: List[str] = Field(default_factory=list, description="لیست شناسه محصولات قابل اعمال")
    applicable_users: List[int] = Field(default_factory=list, description="لیست شناسه کاربران مجاز")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    @field_validator("discount_type")
    @classmethod
    def validate_discount_type(cls, v: str) -> str:
        """اعتبارسنجی نوع تخفیف."""
        if v not in ["percentage", "fixed"]:
            raise ValueError("نوع تخفیف باید 'percentage' یا 'fixed' باشد.")
        return v

    @field_validator("discount_value")
    @classmethod
    def validate_discount_value(cls, v: float, info) -> float:
        """اعتبارسنجی مقدار تخفیف."""
        discount_type = info.data.get("discount_type")
        if discount_type == "percentage" and v > 100:
            raise ValueError("تخفیف درصدی نمی‌تواند بیشتر از ۱۰۰ باشد.")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "CouponCreateDTO":
        """اعتبارسنجی تاریخ‌ها."""
        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("تاریخ شروع باید قبل از تاریخ پایان باشد.")
        return self


class CouponUpdateDTO(BaseModel):
    """
    DTO برای به‌روزرسانی کوپن.

    Attributes:
        code: کد جدید (اختیاری).
        description: توضیحات جدید (اختیاری).
        discount_type: نوع تخفیف جدید (اختیاری).
        discount_value: مقدار تخفیف جدید (اختیاری).
        currency: واحد پول جدید (اختیاری).
        min_order_amount: حداقل مبلغ سفارش جدید (اختیاری).
        max_discount_amount: حداکثر مبلغ تخفیف جدید (اختیاری).
        usage_limit: تعداد دفعات مجاز استفاده جدید (اختیاری).
        user_usage_limit: حداکثر تعداد استفاده برای هر کاربر جدید (اختیاری).
        valid_from: تاریخ شروع اعتبار جدید (اختیاری).
        valid_until: تاریخ پایان اعتبار جدید (اختیاری).
        is_active: وضعیت فعال بودن جدید (اختیاری).
        applicable_products: لیست محصولات قابل اعمال جدید (اختیاری).
        applicable_users: لیست کاربران مجاز جدید (اختیاری).
        metadata: داده‌های اضافی جدید (اختیاری).
    """
    code: Optional[str] = Field(None, max_length=50, description="کد جدید")
    description: Optional[str] = Field(None, max_length=500, description="توضیحات جدید")
    discount_type: Optional[str] = Field(None, description="نوع تخفیف جدید")
    discount_value: Optional[float] = Field(None, gt=0, description="مقدار تخفیف جدید")
    currency: Optional[str] = Field(None, max_length=3, description="واحد پول جدید")
    min_order_amount: Optional[float] = Field(None, ge=0, description="حداقل مبلغ سفارش جدید")
    max_discount_amount: Optional[float] = Field(None, ge=0, description="حداکثر مبلغ تخفیف جدید")
    usage_limit: Optional[int] = Field(None, gt=0, description="تعداد دفعات مجاز استفاده جدید")
    user_usage_limit: Optional[int] = Field(None, gt=0, description="حداکثر تعداد استفاده برای هر کاربر جدید")
    valid_from: Optional[datetime] = Field(None, description="تاریخ شروع اعتبار جدید")
    valid_until: Optional[datetime] = Field(None, description="تاریخ پایان اعتبار جدید")
    is_active: Optional[bool] = Field(None, description="وضعیت فعال بودن جدید")
    applicable_products: Optional[List[str]] = Field(None, description="لیست محصولات قابل اعمال جدید")
    applicable_users: Optional[List[int]] = Field(None, description="لیست کاربران مجاز جدید")
    metadata: Optional[Dict[str, Any]] = Field(None, description="داده‌های اضافی جدید")

    @field_validator("discount_type")
    @classmethod
    def validate_discount_type(cls, v: Optional[str]) -> Optional[str]:
        """اعتبارسنجی نوع تخفیف."""
        if v is not None and v not in ["percentage", "fixed"]:
            raise ValueError("نوع تخفیف باید 'percentage' یا 'fixed' باشد.")
        return v

    @field_validator("discount_value")
    @classmethod
    def validate_discount_value(cls, v: Optional[float], info) -> Optional[float]:
        """اعتبارسنجی مقدار تخفیف."""
        if v is not None:
            discount_type = info.data.get("discount_type")
            if discount_type == "percentage" and v > 100:
                raise ValueError("تخفیف درصدی نمی‌تواند بیشتر از ۱۰۰ باشد.")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "CouponUpdateDTO":
        """اعتبارسنجی تاریخ‌ها."""
        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("تاریخ شروع باید قبل از تاریخ پایان باشد.")
        return self


class CouponResponseDTO(BaseModel):
    """
    DTO برای پاسخ اطلاعات کوپن.

    Attributes:
        id: شناسه کوپن.
        code: کد تخفیف.
        description: توضیحات.
        discount_type: نوع تخفیف.
        discount_value: مقدار تخفیف.
        currency: واحد پول.
        min_order_amount: حداقل مبلغ سفارش.
        max_discount_amount: حداکثر مبلغ تخفیف.
        usage_limit: تعداد دفعات مجاز استفاده.
        usage_count: تعداد دفعات استفاده‌شده تاکنون.
        user_usage_limit: حداکثر تعداد استفاده برای هر کاربر.
        valid_from: تاریخ شروع اعتبار.
        valid_until: تاریخ پایان اعتبار.
        is_active: وضعیت فعال بودن.
        applicable_products: لیست محصولات قابل اعمال.
        applicable_users: لیست کاربران مجاز.
        created_at: زمان ایجاد.
        updated_at: زمان آخرین به‌روزرسانی.
        metadata: داده‌های اضافی.
    """
    id: Optional[int] = Field(None, description="شناسه کوپن")
    code: str = Field(..., description="کد تخفیف")
    description: Optional[str] = Field(None, description="توضیحات")
    discount_type: str = Field(..., description="نوع تخفیف")
    discount_value: float = Field(..., description="مقدار تخفیف")
    currency: str = Field("IRR", description="واحد پول")
    min_order_amount: Optional[float] = Field(None, description="حداقل مبلغ سفارش")
    max_discount_amount: Optional[float] = Field(None, description="حداکثر مبلغ تخفیف")
    usage_limit: Optional[int] = Field(None, description="تعداد دفعات مجاز استفاده")
    usage_count: int = Field(0, description="تعداد دفعات استفاده‌شده تاکنون")
    user_usage_limit: int = Field(1, description="حداکثر تعداد استفاده برای هر کاربر")
    valid_from: datetime = Field(default_factory=datetime.now, description="تاریخ شروع اعتبار")
    valid_until: Optional[datetime] = Field(None, description="تاریخ پایان اعتبار")
    is_active: bool = Field(True, description="وضعیت فعال بودن")
    applicable_products: List[str] = Field(default_factory=list, description="لیست محصولات قابل اعمال")
    applicable_users: List[int] = Field(default_factory=list, description="لیست کاربران مجاز")
    created_at: datetime = Field(default_factory=datetime.now, description="زمان ایجاد")
    updated_at: datetime = Field(default_factory=datetime.now, description="زمان آخرین به‌روزرسانی")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, coupon) -> "CouponResponseDTO":
        """
        ساخت DTO از موجودیت کوپن.

        Args:
            coupon: موجودیت Coupon.

        Returns:
            CouponResponseDTO: DTO ساخته‌شده.
        """
        return cls(
            id=coupon.id,
            code=coupon.code,
            description=coupon.description,
            discount_type=coupon.discount_type.value,
            discount_value=coupon.discount_value,
            currency=coupon.currency,
            min_order_amount=float(coupon.min_order_amount.amount) if coupon.min_order_amount else None,
            max_discount_amount=float(coupon.max_discount_amount.amount) if coupon.max_discount_amount else None,
            usage_limit=coupon.usage_limit,
            usage_count=coupon.usage_count,
            user_usage_limit=coupon.user_usage_limit,
            valid_from=coupon.valid_from,
            valid_until=coupon.valid_until,
            is_active=coupon.is_active,
            applicable_products=coupon.applicable_products,
            applicable_users=coupon.applicable_users,
            created_at=coupon.created_at,
            updated_at=coupon.updated_at,
            metadata=coupon.metadata,
        )

    def get_discount_display(self) -> str:
        """
        دریافت نمایش تخفیف به‌صورت متن.

        Returns:
            str: نمایش تخفیف (مثلاً "۲۰٪ تخفیف" یا "۱۰,۰۰۰ تومان تخفیف").
        """
        if self.discount_type == "percentage":
            return f"{self.discount_value}% تخفیف"
        else:
            if self.currency == "IRR":
                toman = self.discount_value / 10
                return f"{toman:,.0f} تومان تخفیف"
            return f"{self.discount_value:,.2f} {self.currency} تخفیف"

    def is_expired(self) -> bool:
        """بررسی انقضای کوپن."""
        if not self.valid_until:
            return False
        return datetime.now() > self.valid_until

    def is_usable(self) -> bool:
        """بررسی قابل استفاده بودن کوپن."""
        return self.is_active and not self.is_expired()


class CouponValidateDTO(BaseModel):
    """
    DTO برای نتیجه اعتبارسنجی کوپن.

    Attributes:
        is_valid: آیا کوپن معتبر است.
        discount_amount: مبلغ تخفیف قابل اعمال.
        message: پیام توضیحی.
        coupon: اطلاعات کوپن (در صورت معتبر بودن).
    """
    is_valid: bool = Field(..., description="آیا کوپن معتبر است")
    discount_amount: float = Field(0.0, description="مبلغ تخفیف قابل اعمال")
    message: str = Field("", description="پیام توضیحی")
    coupon: Optional[CouponResponseDTO] = Field(None, description="اطلاعات کوپن (در صورت معتبر بودن)")

    class Config:
        from_attributes = True

    @classmethod
    def from_validation(cls, is_valid: bool, discount_amount: float, message: str, coupon=None) -> "CouponValidateDTO":
        """
        ساخت DTO از نتیجه اعتبارسنجی.

        Args:
            is_valid: آیا کوپن معتبر است.
            discount_amount: مبلغ تخفیف.
            message: پیام.
            coupon: کوپن (اختیاری).

        Returns:
            CouponValidateDTO: DTO ساخته‌شده.
        """
        coupon_dto = CouponResponseDTO.from_entity(coupon) if coupon else None
        return cls(
            is_valid=is_valid,
            discount_amount=discount_amount,
            message=message,
            coupon=coupon_dto,
        )