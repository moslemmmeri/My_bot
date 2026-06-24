# src/admin_panel/modules/broadcast/validators/broadcast_validator.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator, ValidationError as PydanticValidationError

from my_bot.core.exceptions import ValidationError
from my_bot.core.logger import get_logger

logger = get_logger(__name__)


class BroadcastCreateSchema(BaseModel):
    """Schema for validating broadcast creation data."""
    message_text: str
    message_type: str = "text"
    media_file_id: Optional[str] = None
    caption: Optional[str] = None
    parse_mode: str = "Markdown"
    filters: Dict[str, Any] = {}
    schedule_time: Optional[datetime] = None
    admin_id: int

    @validator('message_text')
    def validate_message_text(cls, v: str, values: Dict[str, Any]) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Message text cannot be empty")
        if len(v) > 4096:
            raise ValueError("Message text too long (max 4096 characters)")
        return v.strip()

    @validator('message_type')
    def validate_message_type(cls, v: str) -> str:
        valid_types = ["text", "photo", "video", "document", "animation"]
        if v not in valid_types:
            raise ValueError(f"Invalid message type: {v}. Valid: {valid_types}")
        return v

    @validator('media_file_id')
    def validate_media_file_id(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        msg_type = values.get('message_type')
        if msg_type != "text" and not v:
            raise ValueError(f"Media file ID is required for message type: {msg_type}")
        if v and len(v) < 10:
            raise ValueError("Invalid media file ID format")
        return v

    @validator('parse_mode')
    def validate_parse_mode(cls, v: str) -> str:
        valid_modes = ["Markdown", "HTML", "None"]
        if v not in valid_modes:
            raise ValueError(f"Invalid parse mode: {v}. Valid: {valid_modes}")
        return v

    @validator('schedule_time')
    def validate_schedule_time(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v:
            if v <= datetime.now():
                raise ValueError("Schedule time must be in the future")
        return v

    @validator('filters')
    def validate_filters(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        # Validate filter keys
        valid_filter_keys = [
            "level", "is_active", "user_type", "date_from", "date_to",
            "last_active_days", "min_points", "max_points", "has_ordered",
            "user_ids"
        ]
        for key in v.keys():
            if key not in valid_filter_keys:
                raise ValueError(f"Invalid filter key: {key}. Valid: {valid_filter_keys}")
        
        # Validate level values
        if "level" in v:
            valid_levels = ["gold", "silver", "bronze", "normal"]
            if v["level"] not in valid_levels:
                raise ValueError(f"Invalid level: {v['level']}. Valid: {valid_levels}")
        
        # Validate is_active
        if "is_active" in v:
            if not isinstance(v["is_active"], bool):
                raise ValueError("is_active must be boolean")
        
        # Validate user_ids
        if "user_ids" in v:
            if not isinstance(v["user_ids"], list):
                raise ValueError("user_ids must be a list")
            for uid in v["user_ids"]:
                if not isinstance(uid, int) or uid <= 0:
                    raise ValueError("user_ids must contain positive integers")
        
        return v


class BroadcastFilterSchema(BaseModel):
    """Schema for validating broadcast filter data."""
    level: Optional[str] = None
    is_active: Optional[bool] = None
    user_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    last_active_days: Optional[int] = None
    min_points: Optional[int] = None
    max_points: Optional[int] = None
    has_ordered: Optional[bool] = None
    user_ids: Optional[List[int]] = None

    @validator('level')
    def validate_level(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_levels = ["gold", "silver", "bronze", "normal"]
            if v not in valid_levels:
                raise ValueError(f"Invalid level: {v}. Valid: {valid_levels}")
        return v

    @validator('last_active_days')
    def validate_last_active_days(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v <= 0 or v > 365:
                raise ValueError("last_active_days must be between 1 and 365")
        return v

    @validator('min_points', 'max_points')
    def validate_points(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v < 0:
                raise ValueError("Points cannot be negative")
        return v

    @validator('date_from', 'date_to')
    def validate_dates(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v


class BroadcastScheduleSchema(BaseModel):
    """Schema for validating broadcast schedule data."""
    broadcast_id: int
    schedule_time: datetime
    status: str = "scheduled"

    @validator('schedule_time')
    def validate_schedule_time(cls, v: datetime) -> datetime:
        if v <= datetime.now():
            raise ValueError("Schedule time must be in the future")
        return v

    @validator('status')
    def validate_status(cls, v: str) -> str:
        valid_statuses = ["scheduled", "pending", "sent", "failed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Valid: {valid_statuses}")
        return v


class BroadcastValidator:
    """Validator for broadcast-related operations in admin panel."""

    @staticmethod
    def validate_broadcast_create(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for creating a broadcast. Returns validated data or raises ValidationError."""
        try:
            schema = BroadcastCreateSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Broadcast creation validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_filters(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate filter data. Returns validated data or raises ValidationError."""
        try:
            schema = BroadcastFilterSchema(**data)
            return {k: v for k, v in schema.dict().items() if v is not None}
        except PydanticValidationError as e:
            logger.warning(f"Broadcast filter validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_schedule(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate schedule data. Returns validated data or raises ValidationError."""
        try:
            schema = BroadcastScheduleSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Broadcast schedule validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_message_text(text: str) -> str:
        """Validate message text length and content."""
        if not text or len(text.strip()) == 0:
            raise ValidationError("Message text cannot be empty")
        if len(text) > 4096:
            raise ValidationError("Message text too long (max 4096 characters)")
        return text.strip()

    @staticmethod
    def validate_broadcast_id(broadcast_id: int) -> int:
        """Validate broadcast ID is positive integer."""
        if not isinstance(broadcast_id, int) or broadcast_id <= 0:
            raise ValidationError("Broadcast ID must be a positive integer")
        return broadcast_id