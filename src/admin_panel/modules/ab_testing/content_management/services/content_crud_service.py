# src/admin_panel/modules/content_management/services/content_crud_service.py
from typing import Optional, List, Dict, Any
from datetime import datetime

from my_bot.core.exceptions import NotFoundError, DatabaseError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.content_repository import ContentRepository
from my_bot.domain.entities.content import Content

logger = get_logger(__name__)


class ContentCRUDService:
    """Service for CRUD operations on content."""

    def __init__(self, content_repo: ContentRepository) -> None:
        self.content_repo = content_repo

    async def list_content(
        self,
        page: int = 1,
        page_size: int = 20,
        content_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated list of content items with optional filters.
        Returns dict with 'items' (list of content dicts) and 'total'.
        """
        try:
            offset = (page - 1) * page_size
            items, total = await self.content_repo.find_filtered(
                content_type=content_type,
                status=status,
                search=search,
                limit=page_size,
                offset=offset,
            )
            return {
                "items": [self._to_dict(item) for item in items],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.error(f"Error listing content: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve content list.") from e

    async def get_content(self, content_id: int) -> Optional[Dict[str, Any]]:
        """Get a single content item by ID."""
        try:
            content = await self.content_repo.find_by_id(content_id)
            if not content:
                return None
            return self._to_dict(content)
        except Exception as e:
            logger.error(f"Error getting content {content_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve content.") from e

    async def create_content(
        self,
        content_type: str,
        title: str,
        body: str,
        status: str = "draft",
        created_by: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new content item."""
        try:
            content = Content(
                type=content_type,
                title=title,
                body=body,
                status=status,
                created_by=created_by,
                metadata=metadata or {},
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            saved = await self.content_repo.save(content)
            logger.info(f"Content created: {saved.id} by {created_by}")
            return self._to_dict(saved)
        except Exception as e:
            logger.error(f"Error creating content: {e}", exc_info=True)
            raise DatabaseError("Failed to create content.") from e

    async def update_content(
        self,
        content_id: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        updated_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update an existing content item."""
        try:
            content = await self.content_repo.find_by_id(content_id)
            if not content:
                raise NotFoundError(f"Content {content_id} not found")

            if title is not None:
                content.title = title
            if body is not None:
                content.body = body
            if content_type is not None:
                content.type = content_type
            if metadata is not None:
                content.metadata = metadata
            content.updated_at = datetime.now()
            if updated_by:
                content.updated_by = updated_by

            saved = await self.content_repo.save(content)
            logger.info(f"Content {content_id} updated by {updated_by}")
            return self._to_dict(saved)
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating content {content_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to update content.") from e

    async def update_status(self, content_id: int, status: str) -> Dict[str, Any]:
        """Update the status of a content item."""
        valid_statuses = ["draft", "published", "archived"]
        if status not in valid_statuses:
            raise ValidationError(f"Invalid status: {status}")

        try:
            content = await self.content_repo.find_by_id(content_id)
            if not content:
                raise NotFoundError(f"Content {content_id} not found")

            content.status = status
            content.updated_at = datetime.now()
            saved = await self.content_repo.save(content)
            logger.info(f"Content {content_id} status updated to {status}")
            return self._to_dict(saved)
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error updating status for content {content_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to update content status.") from e

    async def delete_content(self, content_id: int) -> bool:
        """Delete a content item by ID."""
        try:
            content = await self.content_repo.find_by_id(content_id)
            if not content:
                raise NotFoundError(f"Content {content_id} not found")

            await self.content_repo.delete(content_id)
            logger.info(f"Content {content_id} deleted")
            return True
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting content {content_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to delete content.") from e

    @staticmethod
    def _to_dict(content: Content) -> Dict[str, Any]:
        """Convert Content entity to dict."""
        return {
            "id": content.id,
            "type": content.type,
            "title": content.title,
            "body": content.body,
            "status": content.status,
            "metadata": content.metadata,
            "created_by": content.created_by,
            "updated_by": getattr(content, "updated_by", None),
            "created_at": content.created_at.isoformat() if content.created_at else None,
            "updated_at": content.updated_at.isoformat() if content.updated_at else None,
        }