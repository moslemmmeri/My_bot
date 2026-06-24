# src/admin_panel/modules/order_management/validators/order_validator.py
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator, ValidationError as PydanticValidationError

from my_bot.core.exceptions import ValidationError
from my_bot.core.logger import get_logger

logger = get_logger(__name__)


class OrderStatusUpdateSchema(BaseModel):
    """Schema for validating order status update data."""
    new_status: str
    reason: Optional[str] = None
    admin_id: int

    @validator('new_status')
    def validate_status(cls, v: str) -> str:
        valid_statuses = ["pending", "paid", "shipped", "delivered", "cancelled", "failed"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid_statuses}")
        return v

    @validator('reason', always=True)
    def validate_reason(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        # If status is cancelled or failed, reason is required
        status = values.get('new_status')
        if status in ["cancelled", "failed"] and not v:
            raise ValueError("Reason is required when cancelling or failing an order")
        return v


class OrderFieldsUpdateSchema(BaseModel):
    """Schema for validating order field updates."""
    total_amount: Optional[float] = None
    shipping_address: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None

    @validator('total_amount')
    def validate_total_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Total amount cannot be negative")
        return v


class OrderSearchFilterSchema(BaseModel):
    """Schema for validating order search/filter parameters."""
    status: Optional[str] = None
    user_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_term: Optional[str] = None
    page: int = 1
    page_size: int = 20

    @validator('status')
    def validate_status_filter(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ["pending", "paid", "shipped", "delivered", "cancelled", "failed"]:
            raise ValueError(f"Invalid status filter: {v}")
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

    @validator('date_from', 'date_to')
    def validate_dates(cls, v: Optional[datetime], values: Dict[str, Any]) -> Optional[datetime]:
        if v and v.tzinfo is None:
            # Assume naive datetime is UTC, or we could localize
            pass
        return v


class OrderValidator:
    """Validator for order-related operations in admin panel."""

    @staticmethod
    def validate_status_update(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for status update. Returns validated data or raises ValidationError."""
        try:
            schema = OrderStatusUpdateSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Order status update validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_field_update(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for field update. Returns validated data or raises ValidationError."""
        try:
            schema = OrderFieldsUpdateSchema(**data)
            return {k: v for k, v in schema.dict().items() if v is not None}
        except PydanticValidationError as e:
            logger.warning(f"Order field update validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_search_filter(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate search/filter parameters. Returns validated data or raises ValidationError."""
        try:
            schema = OrderSearchFilterSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Order search filter validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_order_id(order_id: int) -> int:
        """Validate order ID is positive integer."""
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValidationError("Order ID must be a positive integer")
        return order_id