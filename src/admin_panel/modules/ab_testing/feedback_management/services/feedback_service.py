# src/admin_panel/modules/feedback_management/services/feedback_service.py
from typing import Optional, List, Dict, Any
from datetime import datetime

from my_bot.core.exceptions import NotFoundError, DatabaseError, ValidationError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.feedback_repository import FeedbackRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.entities.feedback import Feedback, FeedbackStatus

logger = get_logger(__name__)


class FeedbackService:
    """Service for managing feedback in admin panel."""

    def __init__(
        self,
        feedback_repo: FeedbackRepository,
        user_repo: UserRepository,
    ) -> None:
        self.feedback_repo = feedback_repo
        self.user_repo = user_repo

    async def list_feedback(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        rating: Optional[int] = None,
        user_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated list of feedback entries with optional filters.
        Returns dict with 'items' (list of feedback dicts) and 'total'.
        """
        try:
            offset = (page - 1) * page_size
            feedbacks, total = await self.feedback_repo.find_filtered(
                status=status,
                rating=rating,
                user_id=user_id,
                search=search,
                limit=page_size,
                offset=offset,
            )
            items = []
            for fb in feedbacks:
                user = await self.user_repo.find_by_id(fb.user_id)
                items.append({
                    "id": fb.id,
                    "user_id": fb.user_id,
                    "user_name": user.username if user else "نامشخص",
                    "rating": fb.rating,
                    "message": fb.message,
                    "status": fb.status.value if hasattr(fb.status, 'value') else fb.status,
                    "reply": getattr(fb, "reply", None),
                    "replied_at": getattr(fb, "replied_at", None),
                    "created_at": fb.created_at.isoformat() if fb.created_at else None,
                    "updated_at": fb.updated_at.isoformat() if fb.updated_at else None,
                })
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.error(f"Error listing feedback: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve feedback.") from e

    async def get_feedback(self, feedback_id: int) -> Optional[Dict[str, Any]]:
        """Get a single feedback by ID."""
        try:
            fb = await self.feedback_repo.find_by_id(feedback_id)
            if not fb:
                return None
            user = await self.user_repo.find_by_id(fb.user_id)
            return {
                "id": fb.id,
                "user_id": fb.user_id,
                "user_name": user.username if user else "نامشخص",
                "rating": fb.rating,
                "message": fb.message,
                "status": fb.status.value if hasattr(fb.status, 'value') else fb.status,
                "reply": getattr(fb, "reply", None),
                "replied_at": getattr(fb, "replied_at", None),
                "created_at": fb.created_at.isoformat() if fb.created_at else None,
                "updated_at": fb.updated_at.isoformat() if fb.updated_at else None,
            }
        except Exception as e:
            logger.error(f"Error getting feedback {feedback_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve feedback.") from e

    async def create_feedback(
        self,
        user_id: int,
        rating: int,
        message: str,
    ) -> Dict[str, Any]:
        """Create a new feedback (from user side)."""
        try:
            if rating < 1 or rating > 5:
                raise ValidationError("Rating must be between 1 and 5.")
            if not message or len(message.strip()) == 0:
                raise ValidationError("Message cannot be empty.")

            feedback = Feedback(
                user_id=user_id,
                rating=rating,
                message=message.strip(),
                status=FeedbackStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            saved = await self.feedback_repo.save(feedback)
            logger.info(f"Feedback created: {saved.id} by user {user_id}")
            user = await self.user_repo.find_by_id(user_id)
            return {
                "id": saved.id,
                "user_id": saved.user_id,
                "user_name": user.username if user else "نامشخص",
                "rating": saved.rating,
                "message": saved.message,
                "status": saved.status.value,
                "created_at": saved.created_at.isoformat(),
            }
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating feedback: {e}", exc_info=True)
            raise DatabaseError("Failed to create feedback.") from e

    async def reply_feedback(
        self,
        feedback_id: int,
        reply_text: str,
        admin_id: int,
    ) -> Dict[str, Any]:
        """Add a reply to feedback and update status."""
        try:
            fb = await self.feedback_repo.find_by_id(feedback_id)
            if not fb:
                raise NotFoundError(f"Feedback {feedback_id} not found.")

            if not reply_text or len(reply_text.strip()) == 0:
                raise ValidationError("Reply text cannot be empty.")

            fb.reply = reply_text.strip()
            fb.replied_at = datetime.now()
            fb.status = FeedbackStatus.REPLIED
            fb.updated_at = datetime.now()
            fb.updated_by = admin_id
            saved = await self.feedback_repo.save(fb)

            logger.info(f"Feedback {feedback_id} replied by admin {admin_id}")
            user = await self.user_repo.find_by_id(fb.user_id)
            return {
                "id": saved.id,
                "user_id": saved.user_id,
                "user_name": user.username if user else "نامشخص",
                "rating": saved.rating,
                "message": saved.message,
                "status": saved.status.value,
                "reply": saved.reply,
                "replied_at": saved.replied_at.isoformat() if saved.replied_at else None,
                "updated_at": saved.updated_at.isoformat() if saved.updated_at else None,
            }
        except ValidationError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error replying to feedback {feedback_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to reply to feedback.") from e

    async def update_status(
        self,
        feedback_id: int,
        status: str,
        admin_id: int,
    ) -> Dict[str, Any]:
        """Update the status of a feedback."""
        try:
            try:
                status_enum = FeedbackStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid status: {status}")

            fb = await self.feedback_repo.find_by_id(feedback_id)
            if not fb:
                raise NotFoundError(f"Feedback {feedback_id} not found.")

            fb.status = status_enum
            fb.updated_at = datetime.now()
            fb.updated_by = admin_id
            saved = await self.feedback_repo.save(fb)

            logger.info(f"Feedback {feedback_id} status changed to {status} by admin {admin_id}")
            user = await self.user_repo.find_by_id(fb.user_id)
            return {
                "id": saved.id,
                "user_id": saved.user_id,
                "user_name": user.username if user else "نامشخص",
                "rating": saved.rating,
                "message": saved.message,
                "status": saved.status.value,
                "reply": getattr(saved, "reply", None),
                "replied_at": getattr(saved, "replied_at", None),
                "updated_at": saved.updated_at.isoformat() if saved.updated_at else None,
            }
        except ValidationError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating status of feedback {feedback_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to update feedback status.") from e

    async def delete_feedback(self, feedback_id: int, admin_id: int) -> bool:
        """Delete a feedback entry."""
        try:
            fb = await self.feedback_repo.find_by_id(feedback_id)
            if not fb:
                raise NotFoundError(f"Feedback {feedback_id} not found.")

            await self.feedback_repo.delete(feedback_id)
            logger.info(f"Feedback {feedback_id} deleted by admin {admin_id}")
            return True
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting feedback {feedback_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to delete feedback.") from e

    async def get_feedback_stats(self) -> Dict[str, Any]:
        """Get statistics about feedback."""
        try:
            total = await self.feedback_repo.count()
            pending = await self.feedback_repo.count_by_status("pending")
            replied = await self.feedback_repo.count_by_status("replied")
            resolved = await self.feedback_repo.count_by_status("resolved")

            avg_rating = await self.feedback_repo.average_rating()
            rating_distribution = await self.feedback_repo.rating_distribution()

            return {
                "total": total,
                "pending": pending,
                "replied": replied,
                "resolved": resolved,
                "average_rating": round(avg_rating, 2) if avg_rating else 0,
                "rating_distribution": rating_distribution,
            }
        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}", exc_info=True)
            raise DatabaseError("Failed to get feedback statistics.") from e

    async def get_feedback_summary(self) -> Dict[str, Any]:
        """Get a quick summary of feedback (for dashboard)."""
        try:
            total = await self.feedback_repo.count()
            pending = await self.feedback_repo.count_by_status("pending")
            avg_rating = await self.feedback_repo.average_rating()
            latest = await self.feedback_repo.find_latest(limit=5)
            latest_items = []
            for fb in latest:
                user = await self.user_repo.find_by_id(fb.user_id)
                latest_items.append({
                    "id": fb.id,
                    "user_name": user.username if user else "نامشخص",
                    "rating": fb.rating,
                    "message": fb.message[:50] + "..." if len(fb.message) > 50 else fb.message,
                    "created_at": fb.created_at.isoformat() if fb.created_at else None,
                })
            return {
                "total": total,
                "pending": pending,
                "average_rating": round(avg_rating, 2) if avg_rating else 0,
                "latest": latest_items,
            }
        except Exception as e:
            logger.error(f"Error getting feedback summary: {e}", exc_info=True)
            raise DatabaseError("Failed to get feedback summary.") from e