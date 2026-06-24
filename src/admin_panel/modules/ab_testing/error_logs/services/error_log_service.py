# src/admin_panel/modules/error_logs/services/error_log_service.py
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from my_bot.core.exceptions import NotFoundError, DatabaseError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.error_log_repository import ErrorLogRepository
from my_bot.domain.entities.error_log import ErrorLog

logger = get_logger(__name__)


class ErrorLogService:
    """Service for managing error logs in admin panel."""

    def __init__(self, error_log_repo: ErrorLogRepository) -> None:
        self.error_log_repo = error_log_repo

    async def list_errors(
        self,
        page: int = 1,
        page_size: int = 20,
        level: Optional[str] = None,
        source: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated list of error logs with optional filters.
        Returns dict with 'items' (list of error dicts) and 'total'.
        """
        try:
            offset = (page - 1) * page_size
            items, total = await self.error_log_repo.find_filtered(
                level=level,
                source=source,
                date_from=date_from,
                date_to=date_to,
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
            logger.error(f"Error listing error logs: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve error logs.") from e

    async def get_error(self, error_id: int) -> Optional[Dict[str, Any]]:
        """Get a single error log by ID."""
        try:
            error = await self.error_log_repo.find_by_id(error_id)
            if not error:
                return None
            return self._to_dict(error)
        except Exception as e:
            logger.error(f"Error getting error log {error_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve error log.") from e

    async def log_error(
        self,
        level: str,
        message: str,
        source: Optional[str] = None,
        traceback: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Log a new error to the database."""
        try:
            error = ErrorLog(
                level=level.upper(),
                message=message,
                source=source,
                traceback=traceback,
                context=context or {},
                user_id=user_id,
                created_at=datetime.now(),
            )
            saved = await self.error_log_repo.save(error)
            logger.info(f"Error logged: {saved.id} - {level} - {message[:50]}")
            return self._to_dict(saved)
        except Exception as e:
            logger.error(f"Error logging error: {e}", exc_info=True)
            raise DatabaseError("Failed to log error.") from e

    async def clear_all_errors(self) -> int:
        """Clear all error logs. Returns count of deleted errors."""
        try:
            count = await self.error_log_repo.delete_all()
            logger.info(f"All error logs cleared. {count} errors deleted.")
            return count
        except Exception as e:
            logger.error(f"Error clearing all errors: {e}", exc_info=True)
            raise DatabaseError("Failed to clear error logs.") from e

    async def clear_errors_older_than(self, days: int) -> int:
        """Clear error logs older than a certain number of days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            count = await self.error_log_repo.delete_older_than(cutoff_date)
            logger.info(f"Errors older than {days} days cleared. {count} errors deleted.")
            return count
        except Exception as e:
            logger.error(f"Error clearing errors older than {days} days: {e}", exc_info=True)
            raise DatabaseError("Failed to clear old error logs.") from e

    async def get_stats(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get statistics about error logs.
        Returns counts by level, source, and total.
        """
        try:
            return await self.error_log_repo.get_stats(
                date_from=date_from,
                date_to=date_to,
            )
        except Exception as e:
            logger.error(f"Error getting error stats: {e}", exc_info=True)
            raise DatabaseError("Failed to get error statistics.") from e

    async def get_level_counts(self) -> Dict[str, int]:
        """Get counts of errors by level."""
        try:
            return await self.error_log_repo.count_by_level()
        except Exception as e:
            logger.error(f"Error getting level counts: {e}", exc_info=True)
            raise DatabaseError("Failed to get level counts.") from e

    @staticmethod
    def _to_dict(error: ErrorLog) -> Dict[str, Any]:
        """Convert ErrorLog entity to dict."""
        return {
            "id": error.id,
            "level": error.level,
            "message": error.message,
            "source": error.source,
            "traceback": error.traceback,
            "context": error.context,
            "user_id": error.user_id,
            "created_at": error.created_at.isoformat() if error.created_at else None,
        }