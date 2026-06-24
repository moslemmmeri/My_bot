# src/admin_panel/modules/broadcast/services/broadcast_filter_service.py
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

from my_bot.core.exceptions import DatabaseError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository

logger = get_logger(__name__)


class BroadcastFilterService:
    """Service for filtering users for broadcast messages."""

    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        order_repo: Optional[OrderRepository] = None,
    ) -> None:
        self.user_repo = user_repo
        self.order_repo = order_repo

    async def count_recipients(self, filters: Dict[str, Any]) -> int:
        """
        Count number of recipients matching the filters.
        Filters can include:
        - level: user level (gold, silver, bronze, normal)
        - is_active: boolean
        - user_type: type of user
        - date_from: created after this date
        - date_to: created before this date
        - has_ordered: boolean (users who have placed orders)
        - min_points: minimum points
        - max_points: maximum points
        - last_active_days: users active within last N days
        - user_ids: list of specific user IDs
        """
        if not self.user_repo:
            raise DatabaseError("User repository not available")

        try:
            query = self._build_user_query(filters)
            return await self.user_repo.count_filtered(**query)
        except Exception as e:
            logger.error(f"Error counting recipients: {e}", exc_info=True)
            raise DatabaseError("Failed to count recipients.") from e

    async def get_recipients(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[int]:
        """
        Get list of user IDs matching the filters.
        """
        if not self.user_repo:
            raise DatabaseError("User repository not available")

        try:
            query = self._build_user_query(filters)
            users = await self.user_repo.find_filtered(
                limit=limit,
                offset=offset,
                **query
            )
            return [user.telegram_id for user in users]
        except Exception as e:
            logger.error(f"Error getting recipients: {e}", exc_info=True)
            raise DatabaseError("Failed to get recipients.") from e

    async def get_recipient_stats(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get statistics about recipients matching the filters.
        Returns counts by level, active status, etc.
        """
        if not self.user_repo:
            raise DatabaseError("User repository not available")

        try:
            query = self._build_user_query(filters)
            stats = await self.user_repo.get_filtered_stats(**query)
            return stats
        except Exception as e:
            logger.error(f"Error getting recipient stats: {e}", exc_info=True)
            raise DatabaseError("Failed to get recipient stats.") from e

    async def validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean filter parameters.
        Returns validated filters dict.
        """
        validated = {}

        # Level filter
        if filters.get("level"):
            valid_levels = ["gold", "silver", "bronze", "normal"]
            level = filters["level"]
            if level not in valid_levels:
                raise ValidationError(f"Invalid level: {level}. Valid: {valid_levels}")
            validated["level"] = level

        # Active status
        if filters.get("is_active") is not None:
            if not isinstance(filters["is_active"], bool):
                raise ValidationError("is_active must be boolean")
            validated["is_active"] = filters["is_active"]

        # User type
        if filters.get("user_type"):
            validated["user_type"] = filters["user_type"]

        # Date range
        if filters.get("date_from"):
            try:
                date_from = self._parse_date(filters["date_from"])
                validated["date_from"] = date_from
            except ValueError:
                raise ValidationError("Invalid date_from format. Use YYYY-MM-DD")

        if filters.get("date_to"):
            try:
                date_to = self._parse_date(filters["date_to"])
                validated["date_to"] = date_to
            except ValueError:
                raise ValidationError("Invalid date_to format. Use YYYY-MM-DD")

        # Last active days
        if filters.get("last_active_days"):
            try:
                days = int(filters["last_active_days"])
                if days <= 0:
                    raise ValidationError("last_active_days must be positive")
                validated["last_active_days"] = days
            except ValueError:
                raise ValidationError("last_active_days must be an integer")

        # Points range
        if filters.get("min_points") is not None:
            try:
                min_points = int(filters["min_points"])
                if min_points < 0:
                    raise ValidationError("min_points cannot be negative")
                validated["min_points"] = min_points
            except ValueError:
                raise ValidationError("min_points must be an integer")

        if filters.get("max_points") is not None:
            try:
                max_points = int(filters["max_points"])
                if max_points < 0:
                    raise ValidationError("max_points cannot be negative")
                validated["max_points"] = max_points
            except ValueError:
                raise ValidationError("max_points must be an integer")

        # Has ordered
        if filters.get("has_ordered") is not None:
            if not isinstance(filters["has_ordered"], bool):
                raise ValidationError("has_ordered must be boolean")
            validated["has_ordered"] = filters["has_ordered"]

        # User IDs
        if filters.get("user_ids"):
            if not isinstance(filters["user_ids"], list):
                raise ValidationError("user_ids must be a list")
            for uid in filters["user_ids"]:
                if not isinstance(uid, int):
                    raise ValidationError("user_ids must contain integers")
            validated["user_ids"] = filters["user_ids"]

        return validated

    def _build_user_query(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build the query dict for user repository."""
        query = {}

        # Apply validated filters
        if filters.get("level"):
            query["level"] = filters["level"]

        if filters.get("is_active") is not None:
            query["is_active"] = filters["is_active"]

        if filters.get("user_type"):
            query["user_type"] = filters["user_type"]

        if filters.get("date_from"):
            query["created_at__gte"] = filters["date_from"]

        if filters.get("date_to"):
            query["created_at__lte"] = filters["date_to"]

        if filters.get("last_active_days"):
            days = filters["last_active_days"]
            since_date = datetime.now() - timedelta(days=days)
            query["last_activity__gte"] = since_date

        if filters.get("min_points") is not None:
            query["points__gte"] = filters["min_points"]

        if filters.get("max_points") is not None:
            query["points__lte"] = filters["max_points"]

        if filters.get("user_ids"):
            query["telegram_id__in"] = filters["user_ids"]

        return query

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime."""
        if isinstance(date_str, datetime):
            return date_str

        # Try different formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%Y/%m/%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Could not parse date: {date_str}")

    async def get_available_filters(self) -> Dict[str, Any]:
        """
        Get available filter options and their possible values.
        Used for building filter UI.
        """
        return {
            "level": {
                "type": "choice",
                "options": ["gold", "silver", "bronze", "normal"],
                "label": "سطح کاربر",
            },
            "is_active": {
                "type": "boolean",
                "label": "فعال/غیرفعال",
            },
            "user_type": {
                "type": "choice",
                "options": ["regular", "premium", "vip"],
                "label": "نوع کاربر",
            },
            "date_from": {
                "type": "date",
                "label": "تاریخ از",
            },
            "date_to": {
                "type": "date",
                "label": "تاریخ تا",
            },
            "last_active_days": {
                "type": "integer",
                "label": "فعال در N روز اخیر",
                "range": [1, 365],
            },
            "min_points": {
                "type": "integer",
                "label": "حداقل امتیاز",
                "min": 0,
            },
            "max_points": {
                "type": "integer",
                "label": "حداکثر امتیاز",
                "min": 0,
            },
            "has_ordered": {
                "type": "boolean",
                "label": "دارای سفارش",
            },
        }

    async def get_filter_summary(self, filters: Dict[str, Any]) -> str:
        """
        Get a human-readable summary of applied filters.
        """
        if not filters:
            return "همه کاربران"

        labels = {
            "level": "سطح",
            "is_active": "وضعیت",
            "user_type": "نوع کاربر",
            "date_from": "تاریخ از",
            "date_to": "تاریخ تا",
            "last_active_days": "فعال در روزهای اخیر",
            "min_points": "حداقل امتیاز",
            "max_points": "حداکثر امتیاز",
            "has_ordered": "دارای سفارش",
        }

        level_labels = {
            "gold": "طلایی",
            "silver": "نقره‌ای",
            "bronze": "برنزی",
            "normal": "معمولی",
        }

        summaries = []
        for key, value in filters.items():
            label = labels.get(key, key)
            if key == "level":
                value = level_labels.get(value, value)
            elif key == "is_active":
                value = "فعال" if value else "غیرفعال"
            elif key == "has_ordered":
                value = "بله" if value else "خیر"
            elif key == "last_active_days":
                value = f"{value} روز اخیر"
            summaries.append(f"{label}: {value}")

        return " | ".join(summaries)