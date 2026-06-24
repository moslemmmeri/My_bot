# src/admin_panel/modules/coupons/validators/coupon_validator.py
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from pydantic import BaseModel, validator, ValidationError as PydanticValidationError

from my_bot.core.exceptions import ValidationError
from my_bot.core.logger import get_logger

logger = get_logger(__name__)


class CouponCreateSchema(BaseModel):
    """Schema for validating coupon creation data."""
    code: str
    discount_type: str
    discount_value: float
    usage_limit: int = 0
    expires_at: Optional[str] = None
    created_by: Optional[int] = None
    description: Optional[str] = None
    min_order_amount: Optional[float] = None
    applicable_to: Optional[List[int]] = None

    @validator('code')
    def validate_code(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Coupon code cannot be empty")
        code = v.strip().upper()
        if len(code) < 3:
            raise ValueError("Coupon code must be at least 3 characters")
        if not code.replace('_', '').isalnum():
            raise ValueError("Coupon code can only contain letters, numbers, and underscores")
        return code

    @validator('discount_type')
    def validate_discount_type(cls, v: str) -> str:
        valid_types = ["percentage", "fixed"]
        if v not in valid_types:
            raise ValueError(f"Invalid discount type: {v}. Valid: {valid_types}")
        return v

    @validator('discount_value')
    def validate_discount_value(cls, v: float, values: Dict[str, Any]) -> float:
        if v <= 0:
            raise ValueError("Discount value must be greater than 0")
        discount_type = values.get('discount_type')
        if discount_type == 'percentage' and v > 100:
            raise ValueError("Percentage discount cannot exceed 100%")
        return v

    @validator('usage_limit')
    def validate_usage_limit(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Usage limit cannot be negative")
        return v

    @validator('expires_at')
    def validate_expires_at(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                # Try to parse as date
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid expiry date format. Use YYYY-MM-DD")
        return v

    @validator('min_order_amount')
    def validate_min_order_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Minimum order amount cannot be negative")
        return v

    @validator('applicable_to')
    def validate_applicable_to(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None:
            for uid in v:
                if not isinstance(uid, int) or uid <= 0:
                    raise ValueError("Applicable to must contain positive integers")
        return v


class CouponUpdateSchema(BaseModel):
    """Schema for validating coupon field updates."""
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    usage_limit: Optional[int] = None
    expires_at: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    min_order_amount: Optional[float] = None
    applicable_to: Optional[List[int]] = None

    @validator('code')
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v or len(v.strip()) == 0:
                raise ValueError("Coupon code cannot be empty")
            code = v.strip().upper()
            if len(code) < 3:
                raise ValueError("Coupon code must be at least 3 characters")
            if not code.replace('_', '').isalnum():
                raise ValueError("Coupon code can only contain letters, numbers, and underscores")
            return code
        return v

    @validator('discount_type')
    def validate_discount_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_types = ["percentage", "fixed"]
            if v not in valid_types:
                raise ValueError(f"Invalid discount type: {v}. Valid: {valid_types}")
        return v

    @validator('discount_value')
    def validate_discount_value(cls, v: Optional[float], values: Dict[str, Any]) -> Optional[float]:
        if v is not None:
            if v <= 0:
                raise ValueError("Discount value must be greater than 0")
            discount_type = values.get('discount_type')
            if discount_type == 'percentage' and v > 100:
                raise ValueError("Percentage discount cannot exceed 100%")
        return v

    @validator('usage_limit')
    def validate_usage_limit(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Usage limit cannot be negative")
        return v

    @validator('expires_at')
    def validate_expires_at(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid expiry date format. Use YYYY-MM-DD")
        return v

    @validator('status')
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_statuses = ["active", "inactive", "expired", "used"]
            if v not in valid_statuses:
                raise ValueError(f"Invalid status: {v}. Valid: {valid_statuses}")
        return v

    @validator('min_order_amount')
    def validate_min_order_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Minimum order amount cannot be negative")
        return v


class CouponFilterSchema(BaseModel):
    """Schema for validating coupon filter parameters."""
    status: Optional[str] = None
    coupon_type: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 20

    @validator('status')
    def validate_status_filter(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_statuses = ["active", "inactive", "expired", "used"]
            if v not in valid_statuses:
                raise ValueError(f"Invalid status filter: {v}")
        return v

    @validator('coupon_type')
    def validate_coupon_type_filter(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_types = ["percentage", "fixed"]
            if v not in valid_types:
                raise ValueError(f"Invalid coupon type filter: {v}")
        return v

    @validator('page')
    def validate_page(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Page must be >= 1")
        return v

    @validator('page_size')
    def validate_page_size(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("Page size must be between 1 and 100")
        return v


class CouponApplySchema(BaseModel):
    """Schema for validating coupon application."""
    code: str
    user_id: int
    order_amount: float

    @validator('code')
    def validate_code(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Coupon code cannot be empty")
        return v.strip().upper()

    @validator('user_id')
    def validate_user_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("User ID must be positive")
        return v

    @validator('order_amount')
    def validate_order_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Order amount must be greater than 0")
        return v


class CouponValidator:
    """Validator for coupon-related operations in admin panel."""

    @staticmethod
    def validate_create(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for creating a coupon."""
        try:
            schema = CouponCreateSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Coupon creation validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_update(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for updating a coupon."""
        try:
            schema = CouponUpdateSchema(**data)
            return {k: v for k, v in schema.dict().items() if v is not None}
        except PydanticValidationError as e:
            logger.warning(f"Coupon update validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_filter(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate filter parameters for listing coupons."""
        try:
            schema = CouponFilterSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Coupon filter validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_apply(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for applying a coupon."""
        try:
            schema = CouponApplySchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Coupon application validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_coupon_id(coupon_id: int) -> int:
        """Validate coupon ID is positive integer."""
        if not isinstance(coupon_id, int) or coupon_id <= 0:
            raise ValidationError("Coupon ID must be a positive integer")
        return coupon_id

    @staticmethod
    def validate_expiry_date(expiry_str: str) -> date:
        """Parse and validate expiry date string."""
        try:
            return datetime.strptime(expiry_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("Invalid expiry date format. Use YYYY-MM-DD")