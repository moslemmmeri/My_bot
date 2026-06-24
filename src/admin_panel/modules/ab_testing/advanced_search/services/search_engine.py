# src/admin_panel/modules/advanced_search/services/search_engine.py
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from my_bot.core.exceptions import DatabaseError, ValidationError, NotFoundError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.content_repository import ContentRepository

logger = get_logger(__name__)


class SearchEngine:
    """Service for performing advanced searches across different entity types."""

    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        order_repo: Optional[OrderRepository] = None,
        content_repo: Optional[ContentRepository] = None,
    ) -> None:
        self.user_repo = user_repo
        self.order_repo = order_repo
        self.content_repo = content_repo

    async def search(
        self,
        query_type: str,
        query: str,
        page: int = 1,
        page_size: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform search based on query type.
        query_type: 'users', 'orders', 'content', 'general', 'all'
        """
        query = query.strip()
        if not query:
            raise ValidationError("Query cannot be empty")

        # Route based on query type
        if query_type == "users":
            return await self._search_users(query, page, page_size, filters or {})
        elif query_type == "orders":
            return await self._search_orders(query, page, page_size, filters or {})
        elif query_type == "content":
            return await self._search_content(query, page, page_size, filters or {})
        elif query_type == "all":
            return await self._search_all(query, page, page_size, filters or {})
        elif query_type == "general":
            return await self._search_general(query, page, page_size, filters or {})
        else:
            raise ValidationError(f"Invalid search type: {query_type}")

    async def _search_users(
        self,
        query: str,
        page: int,
        page_size: int,
        filters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Search for users by username, name, or ID."""
        if not self.user_repo:
            raise DatabaseError("User repository not available")

        try:
            offset = (page - 1) * page_size
            users, total = await self.user_repo.search(
                query=query,
                limit=page_size,
                offset=offset,
                filters=filters,
            )
            items = []
            for user in users:
                items.append({
                    "id": user.id,
                    "telegram_id": user.telegram_id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_active": user.is_active,
                    "level": getattr(user, "level", "normal"),
                    "points": getattr(user, "points", 0),
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                })
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.error(f"Error searching users: {e}", exc_info=True)
            raise DatabaseError("Failed to search users") from e

    async def _search_orders(
        self,
        query: str,
        page: int,
        page_size: int,
        filters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Search for orders by ID, user, or product."""
        if not self.order_repo:
            raise DatabaseError("Order repository not available")

        try:
            offset = (page - 1) * page_size
            orders, total = await self.order_repo.search(
                query=query,
                limit=page_size,
                offset=offset,
                filters=filters,
            )
            items = []
            for order in orders:
                items.append({
                    "id": order.id,
                    "user_id": order.user_id,
                    "username": getattr(order, "username", "نامشخص"),
                    "total_amount": order.total_amount,
                    "status": order.status,
                    "payment_status": getattr(order, "payment_status", "pending"),
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                })
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.error(f"Error searching orders: {e}", exc_info=True)
            raise DatabaseError("Failed to search orders") from e

    async def _search_content(
        self,
        query: str,
        page: int,
        page_size: int,
        filters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Search for content by title, body, or tags."""
        if not self.content_repo:
            raise DatabaseError("Content repository not available")

        try:
            offset = (page - 1) * page_size
            contents, total = await self.content_repo.search(
                query=query,
                limit=page_size,
                offset=offset,
                filters=filters,
            )
            items = []
            for content in contents:
                items.append({
                    "id": content.id,
                    "title": content.title,
                    "type": content.type,
                    "status": content.status,
                    "body_preview": content.body[:200] + "..." if len(content.body) > 200 else content.body,
                    "created_at": content.created_at.isoformat() if content.created_at else None,
                })
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.error(f"Error searching content: {e}", exc_info=True)
            raise DatabaseError("Failed to search content") from e

    async def _search_all(
        self,
        query: str,
        page: int,
        page_size: int,
        filters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Search across all entities and combine results."""
        try:
            # Run searches in parallel
            import asyncio
            user_task = self._search_users(query, 1, 5, filters)
            order_task = self._search_orders(query, 1, 5, filters)
            content_task = self._search_content(query, 1, 5, filters)

            results = await asyncio.gather(
                user_task, order_task, content_task,
                return_exceptions=True
            )

            combined_items = []
            total_count = 0
            user_items = []
            order_items = []
            content_items = []

            if not isinstance(results[0], Exception):
                user_items = results[0].get("items", [])
                total_count += results[0].get("total", 0)
            if not isinstance(results[1], Exception):
                order_items = results[1].get("items", [])
                total_count += results[1].get("total", 0)
            if not isinstance(results[2], Exception):
                content_items = results[2].get("items", [])
                total_count += results[2].get("total", 0)

            # Add type markers and combine
            for item in user_items:
                item["_search_type"] = "user"
                combined_items.append(item)
            for item in order_items:
                item["_search_type"] = "order"
                combined_items.append(item)
            for item in content_items:
                item["_search_type"] = "content"
                combined_items.append(item)

            # Paginate combined results
            offset = (page - 1) * page_size
            paginated_items = combined_items[offset:offset + page_size]

            return {
                "items": paginated_items,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "breakdown": {
                    "users": len(user_items),
                    "orders": len(order_items),
                    "content": len(content_items),
                }
            }
        except Exception as e:
            logger.error(f"Error in combined search: {e}", exc_info=True)
            raise DatabaseError("Failed to perform combined search") from e

    async def _search_general(
        self,
        query: str,
        page: int,
        page_size: int,
        filters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """General search with prioritized results."""
        # For general search, use combined search but prioritize users and orders
        result = await self._search_all(query, page, page_size, filters)

        # Add priority ranking (for UI display)
        priority_order = {"user": 1, "order": 2, "content": 3}
        items = result.get("items", [])
        for item in items:
            search_type = item.get("_search_type")
            item["_priority"] = priority_order.get(search_type, 9)

        # Sort by priority
        items.sort(key=lambda x: x.get("_priority", 9))
        result["items"] = items

        return result