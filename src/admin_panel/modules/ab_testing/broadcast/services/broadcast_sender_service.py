# src/admin_panel/modules/broadcast/services/broadcast_sender_service.py
import asyncio
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

from aiogram import Bot
from aiogram.exceptions import (
    TelegramRetryAfter,
    TelegramForbiddenError,
    TelegramBadRequest,
    TelegramNetworkError,
    TelegramServerError,
)

from my_bot.core.exceptions import DatabaseError, ValidationError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.core.config import Config
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.broadcast_repository import BroadcastRepository
from my_bot.application.services.broadcast.broadcast_sender import BroadcastSender as AppBroadcastSender
from my_bot.presentation.handlers.broadcast.broadcast_handlers import BroadcastHandlers

logger = get_logger(__name__)


@dataclass
class BroadcastResult:
    """Result of a broadcast send operation."""
    total: int = 0
    sent: int = 0
    failed: int = 0
    failed_users: List[int] = field(default_factory=list)
    duration: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "sent": self.sent,
            "failed": self.failed,
            "failed_users": self.failed_users[:10],  # Only first 10 for display
            "duration": round(self.duration, 2),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


class BroadcastSenderService:
    """Service for sending broadcast messages to users."""

    def __init__(
        self,
        bot: Bot,
        config: Optional[Config] = None,
        user_repo: Optional[UserRepository] = None,
        broadcast_repo: Optional[BroadcastRepository] = None,
    ) -> None:
        self.bot = bot
        self.config = config or Config.from_env()
        self.user_repo = user_repo
        self.broadcast_repo = broadcast_repo
        self._rate_limit_delay = 0.05  # 50ms delay between messages to avoid rate limiting
        self._max_retries = 3
        self._batch_size = 50  # Number of users to fetch at once

    async def send_broadcast(
        self,
        message_text: str,
        filters: Dict[str, Any],
        admin_id: int,
        message_type: str = "text",
        media_file_id: Optional[str] = None,
        caption: Optional[str] = None,
        parse_mode: str = "Markdown",
    ) -> BroadcastResult:
        """
        Send a broadcast message to users matching the filters.
        """
        if not message_text and not media_file_id:
            raise ValidationError("Message text or media is required.")

        result = BroadcastResult()
        result.start_time = datetime.now()

        try:
            # Get recipients based on filters
            recipients = await self._get_recipients(filters)
            total_users = len(recipients)
            result.total = total_users

            if total_users == 0:
                logger.warning("No recipients found for broadcast")
                result.end_time = datetime.now()
                return result

            logger.info(f"Sending broadcast to {total_users} users by admin {admin_id}")

            # Send messages in batches
            sent_count = 0
            failed_count = 0
            failed_users = []

            for i in range(0, total_users, self._batch_size):
                batch = recipients[i:i + self._batch_size]
                tasks = []
                for user_id in batch:
                    if message_type == "text":
                        tasks.append(self._send_text_message(user_id, message_text, parse_mode))
                    elif message_type == "photo":
                        tasks.append(self._send_photo_message(user_id, media_file_id, caption or message_text))
                    elif message_type == "video":
                        tasks.append(self._send_video_message(user_id, media_file_id, caption or message_text))
                    elif message_type == "document":
                        tasks.append(self._send_document_message(user_id, media_file_id, caption or message_text))
                    else:
                        tasks.append(self._send_text_message(user_id, message_text, parse_mode))

                # Wait for all messages in batch
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for idx, res in enumerate(results):
                    user_id = batch[idx]
                    if isinstance(res, Exception):
                        failed_count += 1
                        failed_users.append(user_id)
                        logger.warning(f"Failed to send to user {user_id}: {res}")
                    else:
                        sent_count += 1

                # Update progress
                result.sent = sent_count
                result.failed = failed_count
                result.failed_users = failed_users

                # Save progress periodically (every 10 batches)
                if i > 0 and i % (self._batch_size * 10) == 0:
                    await self._save_progress(admin_id, result, sent_count + failed_count)

                # Rate limiting delay between batches
                if i + self._batch_size < total_users:
                    await asyncio.sleep(self._rate_limit_delay * self._batch_size)

            # Finalize
            result.sent = sent_count
            result.failed = failed_count
            result.failed_users = failed_users
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()

            # Save final result
            await self._save_broadcast_result(admin_id, result)

            logger.info(
                f"Broadcast completed: {sent_count} sent, {failed_count} failed "
                f"out of {total_users} users"
            )

            return result

        except Exception as e:
            logger.error(f"Error sending broadcast: {e}", exc_info=True)
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            raise DatabaseError(f"Failed to send broadcast: {str(e)}") from e

    async def _get_recipients(self, filters: Dict[str, Any]) -> List[int]:
        """Get list of user IDs matching the filters."""
        if not self.user_repo:
            raise DatabaseError("User repository not available")

        try:
            # Apply filters
            query = {}
            if filters.get("is_active") is not None:
                query["is_active"] = filters["is_active"]
            if filters.get("level"):
                query["level"] = filters["level"]
            if filters.get("user_type"):
                query["user_type"] = filters["user_type"]
            if filters.get("date_from"):
                query["created_at__gte"] = filters["date_from"]
            if filters.get("date_to"):
                query["created_at__lte"] = filters["date_to"]

            # Get users (in a real implementation, use pagination to avoid memory issues)
            users = await self.user_repo.find_filtered(**query)
            return [user.telegram_id for user in users]
        except Exception as e:
            logger.error(f"Error getting recipients: {e}", exc_info=True)
            raise DatabaseError("Failed to get recipients.") from e

    async def _send_text_message(
        self,
        user_id: int,
        text: str,
        parse_mode: str = "Markdown",
    ) -> bool:
        """Send a text message with retry logic."""
        for attempt in range(self._max_retries):
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    parse_mode=parse_mode,
                )
                return True
            except TelegramRetryAfter as e:
                wait_time = e.retry_after + 1
                logger.warning(f"Rate limited for user {user_id}, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
            except (TelegramNetworkError, TelegramServerError) as e:
                if attempt < self._max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5
                    logger.warning(f"Network error, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    raise
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                logger.warning(f"Cannot send to user {user_id}: {e}")
                return False
        return False

    async def _send_photo_message(
        self,
        user_id: int,
        photo_file_id: str,
        caption: str,
    ) -> bool:
        """Send a photo message with retry logic."""
        for attempt in range(self._max_retries):
            try:
                await self.bot.send_photo(
                    chat_id=user_id,
                    photo=photo_file_id,
                    caption=caption,
                    parse_mode="Markdown",
                )
                return True
            except TelegramRetryAfter as e:
                wait_time = e.retry_after + 1
                await asyncio.sleep(wait_time)
            except (TelegramNetworkError, TelegramServerError) as e:
                if attempt < self._max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5
                    await asyncio.sleep(wait_time)
                else:
                    raise
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                logger.warning(f"Cannot send photo to user {user_id}: {e}")
                return False
        return False

    async def _send_video_message(
        self,
        user_id: int,
        video_file_id: str,
        caption: str,
    ) -> bool:
        """Send a video message with retry logic."""
        for attempt in range(self._max_retries):
            try:
                await self.bot.send_video(
                    chat_id=user_id,
                    video=video_file_id,
                    caption=caption,
                    parse_mode="Markdown",
                )
                return True
            except TelegramRetryAfter as e:
                wait_time = e.retry_after + 1
                await asyncio.sleep(wait_time)
            except (TelegramNetworkError, TelegramServerError) as e:
                if attempt < self._max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5
                    await asyncio.sleep(wait_time)
                else:
                    raise
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                logger.warning(f"Cannot send video to user {user_id}: {e}")
                return False
        return False

    async def _send_document_message(
        self,
        user_id: int,
        document_file_id: str,
        caption: str,
    ) -> bool:
        """Send a document message with retry logic."""
        for attempt in range(self._max_retries):
            try:
                await self.bot.send_document(
                    chat_id=user_id,
                    document=document_file_id,
                    caption=caption,
                    parse_mode="Markdown",
                )
                return True
            except TelegramRetryAfter as e:
                wait_time = e.retry_after + 1
                await asyncio.sleep(wait_time)
            except (TelegramNetworkError, TelegramServerError) as e:
                if attempt < self._max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5
                    await asyncio.sleep(wait_time)
                else:
                    raise
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                logger.warning(f"Cannot send document to user {user_id}: {e}")
                return False
        return False

    async def _save_progress(
        self,
        admin_id: int,
        result: BroadcastResult,
        processed: int,
    ) -> None:
        """Save intermediate progress to database."""
        if not self.broadcast_repo:
            return
        try:
            await self.broadcast_repo.update_progress(
                admin_id=admin_id,
                processed=processed,
                sent=result.sent,
                failed=result.failed,
            )
        except Exception as e:
            logger.warning(f"Failed to save broadcast progress: {e}")

    async def _save_broadcast_result(
        self,
        admin_id: int,
        result: BroadcastResult,
    ) -> None:
        """Save final broadcast result to database."""
        if not self.broadcast_repo:
            return
        try:
            await self.broadcast_repo.save_broadcast_log(
                admin_id=admin_id,
                total=result.total,
                sent=result.sent,
                failed=result.failed,
                failed_users=result.failed_users,
                duration=result.duration,
            )
        except Exception as e:
            logger.error(f"Failed to save broadcast result: {e}")

    async def count_recipients(self, filters: Dict[str, Any]) -> int:
        """Count number of recipients matching the filters."""
        if not self.user_repo:
            raise DatabaseError("User repository not available")
        try:
            query = {}
            if filters.get("is_active") is not None:
                query["is_active"] = filters["is_active"]
            if filters.get("level"):
                query["level"] = filters["level"]
            if filters.get("user_type"):
                query["user_type"] = filters["user_type"]
            if filters.get("date_from"):
                query["created_at__gte"] = filters["date_from"]
            if filters.get("date_to"):
                query["created_at__lte"] = filters["date_to"]
            return await self.user_repo.count_filtered(**query)
        except Exception as e:
            logger.error(f"Error counting recipients: {e}", exc_info=True)
            raise DatabaseError("Failed to count recipients.") from e