# src/admin_panel/modules/feature_management/validators/feature_validator.py
from typing import Optional, Dict, Any
from pydantic import BaseModel, validator, ValidationError as PydanticValidationError

from my_bot.core.exceptions import ValidationError
from my_bot.core.logger import get_logger

logger = get_logger(__name__)


class FeatureCreateSchema(BaseModel):
    """Schema for validating feature creation data."""
    name: str
    description: Optional[str] = None
    is_enabled: bool = False
    created_by: Optional[int] = None

    @validator('name')
    def validate_name(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Feature name cannot be empty.")
        name = v.strip()
        if len(name) < 3:
            raise ValueError("Feature name must be at least 3 characters.")
        if len(name) > 50:
            raise ValueError("Feature name too long (max 50 characters).")
        if not name.replace('_', '').isalnum():
            raise ValueError("Feature name can only contain letters, numbers, and underscores.")
        return name

    @validator('description')
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 500:
            raise ValueError("Description too long (max 500 characters).")
        return v.strip() if v else None


class FeatureUpdateSchema(BaseModel):
    """Schema for validating feature update data."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None

    @validator('name')
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v or len(v.strip()) == 0:
                raise ValueError("Feature name cannot be empty.")
            name = v.strip()
            if len(name) < 3:
                raise ValueError("Feature name must be at least 3 characters.")
            if len(name) > 50:
                raise ValueError("Feature name too long (max 50 characters).")
            if not name.replace('_', '').isalnum():
                raise ValueError("Feature name can only contain letters, numbers, and underscores.")
            return name
        return v

    @validator('description')
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 500:
            raise ValueError("Description too long (max 500 characters).")
        return v.strip() if v else None


class FeatureFilterSchema(BaseModel):
    """Schema for validating feature filter parameters."""
    search: Optional[str] = None
    is_enabled: Optional[bool] = None
    page: int = 1
    page_size: int = 20

    @validator('page')
    def validate_page(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Page must be >= 1.")
        return v

    @validator('page_size')
    def validate_page_size(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("Page size must be between 1 and 100.")
        return v


class FeatureValidator:
    """Validator for feature-related operations in admin panel."""

    @staticmethod
    def validate_create(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for creating a feature."""
        try:
            schema = FeatureCreateSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Feature creation validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_update(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for updating a feature."""
        try:
            schema = FeatureUpdateSchema(**data)
            return {k: v for k, v in schema.dict().items() if v is not None}
        except PydanticValidationError as e:
            logger.warning(f"Feature update validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_filter(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate filter parameters for listing features."""
        try:
            schema = FeatureFilterSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Feature filter validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_feature_id(feature_id: int) -> int:
        """Validate feature ID is positive integer."""
        if not isinstance(feature_id, int) or feature_id <= 0:
            raise ValidationError("Feature ID must be a positive integer.")
        return feature_id

    @staticmethod
    def validate_feature_name(name: str) -> str:
        """Validate feature name is valid."""
        if not name or len(name.strip()) == 0:
            raise ValidationError("Feature name cannot be empty.")
        name = name.strip()
        if len(name) < 3:
            raise ValidationError("Feature name must be at least 3 characters.")
        if len(name) > 50:
            raise ValidationError("Feature name too long (max 50 characters).")
        if not name.replace('_', '').isalnum():
            raise ValidationError("Feature name can only contain letters, numbers, and underscores.")
        return name