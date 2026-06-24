# src/admin_panel/modules/tickets/validators/ticket_validator.py
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, validator, ValidationError as PydanticValidationError

from my_bot.core.exceptions import ValidationError
from my_bot.core.logger import get_logger

logger = get_logger(__name__)


class TicketCreateSchema(BaseModel):
    """Schema for validating ticket creation data (from user side)."""
    user_id: int
    title: str
    body: str
    priority: str = "medium"

    @validator('user_id')
    def validate_user_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("User ID must be a positive integer")
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
        if len(v) > 5000:
            raise ValueError("Body too long (max 5000 characters)")
        return v.strip()

    @validator('priority')
    def validate_priority(cls, v: str) -> str:
        valid_priorities = ["low", "medium", "high", "critical"]
        if v not in valid_priorities:
            raise ValueError(f"Invalid priority: {v}. Valid: {valid_priorities}")
        return v


class TicketReplySchema(BaseModel):
    """Schema for validating ticket reply data."""
    ticket_id: int
    user_id: int
    text: str
    is_admin: bool = True

    @validator('ticket_id')
    def validate_ticket_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Ticket ID must be a positive integer")
        return v

    @validator('text')
    def validate_text(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Reply text cannot be empty")
        if len(v) > 4000:
            raise ValueError("Reply text too long (max 4000 characters)")
        return v.strip()


class TicketStatusUpdateSchema(BaseModel):
    """Schema for validating ticket status update."""
    ticket_id: int
    status: str
    updated_by: int

    @validator('status')
    def validate_status(cls, v: str) -> str:
        valid_statuses = ["open", "in_progress", "resolved", "closed"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Valid: {valid_statuses}")
        return v


class TicketPriorityUpdateSchema(BaseModel):
    """Schema for validating ticket priority update."""
    ticket_id: int
    priority: str
    updated_by: int

    @validator('priority')
    def validate_priority(cls, v: str) -> str:
        valid_priorities = ["low", "medium", "high", "critical"]
        if v not in valid_priorities:
            raise ValueError(f"Invalid priority: {v}. Valid: {valid_priorities}")
        return v


class TicketAssignmentSchema(BaseModel):
    """Schema for validating ticket assignment."""
    ticket_id: int
    assignee_id: int
    assigned_by: int

    @validator('assignee_id')
    def validate_assignee(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Assignee ID must be a positive integer")
        return v


class TicketFilterSchema(BaseModel):
    """Schema for validating ticket filter parameters."""
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None
    user_id: Optional[int] = None
    page: int = 1
    page_size: int = 20

    @validator('status')
    def validate_status_filter(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_statuses = ["open", "in_progress", "resolved", "closed"]
            if v not in valid_statuses:
                raise ValueError(f"Invalid status filter: {v}")
        return v

    @validator('priority')
    def validate_priority_filter(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_priorities = ["low", "medium", "high", "critical"]
            if v not in valid_priorities:
                raise ValueError(f"Invalid priority filter: {v}")
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


class TicketValidator:
    """Validator for ticket-related operations in admin panel."""

    @staticmethod
    def validate_ticket_create(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for creating a ticket."""
        try:
            schema = TicketCreateSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Ticket creation validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_ticket_reply(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for replying to a ticket."""
        try:
            schema = TicketReplySchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Ticket reply validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_status_update(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for updating ticket status."""
        try:
            schema = TicketStatusUpdateSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Ticket status update validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_priority_update(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for updating ticket priority."""
        try:
            schema = TicketPriorityUpdateSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Ticket priority update validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_assignment(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for assigning a ticket."""
        try:
            schema = TicketAssignmentSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Ticket assignment validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_filter(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate filter parameters for listing tickets."""
        try:
            schema = TicketFilterSchema(**data)
            return schema.dict()
        except PydanticValidationError as e:
            logger.warning(f"Ticket filter validation failed: {e}")
            errors = []
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'Invalid value')
                errors.append(f"{field}: {msg}")
            raise ValidationError("Validation error: " + "; ".join(errors))

    @staticmethod
    def validate_ticket_id(ticket_id: int) -> int:
        """Validate ticket ID is positive integer."""
        if not isinstance(ticket_id, int) or ticket_id <= 0:
            raise ValidationError("Ticket ID must be a positive integer")
        return ticket_id