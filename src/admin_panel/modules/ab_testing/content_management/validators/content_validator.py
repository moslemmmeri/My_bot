# src/admin_panel/modules/content_management/validators/content_validator.py
from typing import Optional, Dict, Any
from pydantic import BaseModel, validator, ValidationError as PydanticValidationError

from my_bot.core.exceptions import ValidationError
from my_bot.core.logger import get_logger

logger = get_logger(__name__)


class ContentCreateSchema(BaseModel):
    """Schema for validating content creation data."""
    content_type: str
    title: str
    body: str
    status: str = "draft"
    metadata: Optional[Dict[str, Any]] = None

    @validator('content_type')
    def validate_content_type(cls, v: str) -> str:
        allowed_types = ["article", "news", "page", "landing"]
        if v not in allowed_types:
            raise ValueError(f"Invalid content type: {v}. Allowed: {allowed_types}")
        return v

    @validator('title')
    def validate_title(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Title cannot be empty")
        if len(v) > 200:
            raise ValueError("Title too long (max 200 characters)")
        return v.strip()

    @validator('body')
    def validate_body(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Body cannot be empty")
        return v.strip()

    @validator('status')
    def validate_status(cls, v: str) -> str:
        allowed_statuses = ["draft", "published", "archived"]
        if v not in allowed_statuses:
            raise ValueError(f"Invalid status: {v}. Allowed: {allowed_statuses}")
        return v


class ContentUpdateSchema(BaseModel):
    """Schema for validating content update data."""
    title: Optional[str] = None
    body: Optional[str] = None
    content_type: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('content_type')
    def validate_content_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_types = ["article", "news", "page", "landing"]
            if v not in allowed_types:
                raise ValueError(f"Invalid content type: {v}. Allowed: {allowed_types}")
        return v

    @validator('title')
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v or len(v.strip()) == 0:
                raise ValueError("Title cannot be empty")
            if len(v) > 200:
                raise ValueError("Title too long (max 200 characters)")
            return v.strip()
        return v

    @validator('body')
    def validate_body(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v or len(v.strip()) == 0:
                raise ValueError("Body cannot be empty")
            return v.strip()
        return v

    @validator('status')
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_statuses = ["draft", "published", "archived"]
            if v not in allowed_statuses:
                raise ValueError(f"Invalid status: {v}. Allowed: {allowed_statuses}")
        return v


class ContentSearchFilterSchema(BaseModel):
    """Schema for validating content search/filter parameters."""
    content_type: Optional[str] = None
    status: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 20

    @validator('content_type')
    def validate_content_type_filter(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_types = ["article", "news", "page", "landing"]
            if v not in allowed_types:
                raise ValueError(f"Invalid content type filter: {v}")
        return v

    @validator('status')
    def validate_status_filter(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_statuses = ["draft", "published", "archived"]
            if v not in allowed_statuses:
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


class ContentValidator:
    """Validator for content-related operations in admin panel."""

    @staticmethod
    def validate_create(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for creating content. Returns validated data or raises ValidationError."""
        try:
            schema = ContentCreateSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Content creation validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_update(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for updating content. Returns validated data or raises ValidationError."""
        try:
            schema = ContentUpdateSchema(**data)
            return {k: v for k, v in schema.dict().items() if v is not None}
        except PydanticValidationError as e:
            logger.warning(f"Content update validation failed: {e}")
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
            schema = ContentSearchFilterSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Content search filter validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_content_id(content_id: int) -> int:
        """Validate content ID is positive integer."""
        if not isinstance(content_id, int) or content_id <= 0:
            raise ValidationError("Content ID must be a positive integer")
        return content_id