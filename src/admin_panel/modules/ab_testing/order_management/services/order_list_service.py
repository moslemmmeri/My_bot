# src/admin_panel/modules/order_management/services/order_list_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime

from my_bot.core.exceptions import DatabaseError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.application.dtos.order_dto import OrderDTO

logger = get_logger(__name__)


class OrderListService:
    """Service for listing orders in admin panel."""

    def __init__(self, order_repo: OrderRepository) -> None:
        self.order_repo = order_repo

    async def list_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search_term: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated list of orders with optional filters.
        Returns dict with 'items' (list of OrderDTO) and 'total' count.
        """
        try:
            offset = (page - 1) * page_size
            orders, total = await self.order_repo.find_filtered(
                status=status,
                user_id=user_id,
                date_from=date_from,
                date_to=date_to,
                search_term=search_term,
                limit=page_size,
                offset=offset,
            )
            return {
                "items": [OrderDTO.from_entity(order) for order in orders],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.error(f"Error listing orders: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve orders.") from e

    async def get_order_summary(self, order_id: int) -> Dict[str, Any]:
        """Get summary info for a single order (for confirmation dialogs)."""
        order = await self.order_repo.find_by_id(order_id)
        if not order:
            return {}
        return {
            "id": order.id,
            "user_name": order.user.username or "نامشخص",
            "total": order.total_amount,
            "status": order.status,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
        }