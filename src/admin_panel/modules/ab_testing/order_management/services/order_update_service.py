# src/admin_panel/modules/order_management/services/order_update_service.py
from typing import Optional, Dict, Any
from datetime import datetime

from my_bot.core.exceptions import NotFoundError, DatabaseError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.entities.order import Order
from my_bot.application.dtos.order_dto import OrderDTO
from my_bot.application.services.order.order_status_update import OrderStatusUpdateService

logger = get_logger(__name__)


class OrderUpdateService:
    """Service for updating orders in admin panel."""

    def __init__(
        self,
        order_repo: OrderRepository,
        status_update_service: OrderStatusUpdateService,
    ) -> None:
        self.order_repo = order_repo
        self.status_update_service = status_update_service

    async def get_order_for_edit(self, order_id: int) -> Optional[OrderDTO]:
        """Retrieve order details for editing."""
        try:
            order = await self.order_repo.find_by_id(order_id)
            if not order:
                raise NotFoundError(f"Order {order_id} not found")
            return OrderDTO.from_entity(order)
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve order for editing.") from e

    async def update_order_status(
        self,
        order_id: int,
        new_status: str,
        admin_id: int,
        reason: Optional[str] = None,
    ) -> OrderDTO:
        """Update the status of an order."""
        try:
            # Validate status
            valid_statuses = ["pending", "paid", "shipped", "delivered", "cancelled", "failed"]
            if new_status not in valid_statuses:
                raise ValidationError(f"Invalid status: {new_status}")

            # Perform status update
            updated_order = await self.status_update_service.update_status(
                order_id=order_id,
                new_status=new_status,
                updated_by=admin_id,
                reason=reason,
            )
            logger.info(f"Order {order_id} status updated to {new_status} by admin {admin_id}")
            return OrderDTO.from_entity(updated_order)
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error updating order {order_id} status: {e}", exc_info=True)
            raise DatabaseError("Failed to update order status.") from e

    async def update_order_fields(
        self,
        order_id: int,
        admin_id: int,
        **fields,
    ) -> OrderDTO:
        """Update arbitrary fields of an order (e.g., total_amount, shipping_address)."""
        try:
            order = await self.order_repo.find_by_id(order_id)
            if not order:
                raise NotFoundError(f"Order {order_id} not found")

            # Apply updates
            updated = False
            for key, value in fields.items():
                if hasattr(order, key) and getattr(order, key) != value:
                    setattr(order, key, value)
                    updated = True

            if not updated:
                return OrderDTO.from_entity(order)

            # Save changes
            await self.order_repo.save(order)
            logger.info(f"Order {order_id} fields updated by admin {admin_id}")
            return OrderDTO.from_entity(order)
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating order {order_id} fields: {e}", exc_info=True)
            raise DatabaseError("Failed to update order fields.") from e