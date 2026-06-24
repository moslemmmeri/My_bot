# src/my_bot/application/use_cases/order/create_order.py
from typing import List, Optional, Dict, Any
from datetime import datetime

from my_bot.core.exceptions import ValidationError, NotFoundError, DatabaseError
from my_bot.core.logger import get_logger
from my_bot.domain.entities.order import Order
from my_bot.domain.entities.user import User
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.coupon_repository import CouponRepository
from my_bot.domain.value_objects.money import Money
from my_bot.application.dtos.order_dto import OrderDTO, OrderItemDTO

logger = get_logger(__name__)


class CreateOrderUseCase:
    """
    Use case for creating a new order.

    This use case handles the entire order creation process including:
    - Validating user existence and status
    - Validating order items
    - Calculating total amount
    - Applying coupon discounts (if provided)
    - Creating and saving the order
    - Returning order details
    """

    def __init__(
        self,
        order_repo: OrderRepository,
        user_repo: UserRepository,
        coupon_repo: Optional[CouponRepository] = None,
    ) -> None:
        self.order_repo = order_repo
        self.user_repo = user_repo
        self.coupon_repo = coupon_repo

    async def execute(
        self,
        user_id: int,
        items: List[OrderItemDTO],
        coupon_code: Optional[str] = None,
        shipping_address: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> OrderDTO:
        """
        Execute the order creation use case.

        Args:
            user_id: ID of the user placing the order
            items: List of order items (product, quantity, price)
            coupon_code: Optional coupon code to apply discount
            shipping_address: Optional shipping address
            notes: Optional order notes

        Returns:
            OrderDTO: Created order details

        Raises:
            NotFoundError: If user not found or coupon invalid
            ValidationError: If input data is invalid
            DatabaseError: If database operation fails
        """
        # 1. Validate user
        user = await self._validate_user(user_id)

        # 2. Validate items
        if not items:
            raise ValidationError("Order must contain at least one item.")

        for item in items:
            if item.quantity <= 0:
                raise ValidationError(f"Invalid quantity for product: {item.product}")
            if item.price <= 0:
                raise ValidationError(f"Invalid price for product: {item.product}")

        # 3. Calculate subtotal
        subtotal = self._calculate_subtotal(items)

        # 4. Apply coupon (if provided)
        discount_amount = 0.0
        applied_coupon_id = None
        if coupon_code:
            coupon = await self.coupon_repo.find_by_code(coupon_code) if self.coupon_repo else None
            if not coupon:
                raise NotFoundError(f"Coupon '{coupon_code}' not found.")
            if coupon.status != "active":
                raise ValidationError(f"Coupon '{coupon_code}' is not active.")
            if coupon.expires_at and coupon.expires_at < datetime.now().date():
                raise ValidationError(f"Coupon '{coupon_code}' has expired.")
            if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
                raise ValidationError(f"Coupon '{coupon_code}' has reached its usage limit.")
            if coupon.min_order_amount and subtotal < coupon.min_order_amount:
                raise ValidationError(
                    f"Minimum order amount for coupon is {coupon.min_order_amount}."
                )

            # Calculate discount
            if coupon.discount_type == "percentage":
                discount_amount = (subtotal * coupon.discount_value) / 100
            else:  # fixed
                discount_amount = coupon.discount_value

            # Cap discount to subtotal
            discount_amount = min(discount_amount, subtotal)
            applied_coupon_id = coupon.id

        # 5. Calculate total
        total_amount = subtotal - discount_amount

        # 6. Create order
        order = Order(
            user_id=user_id,
            items=[item.dict() for item in items],
            subtotal=subtotal,
            discount_amount=discount_amount,
            coupon_id=applied_coupon_id,
            total_amount=total_amount,
            status="pending",
            shipping_address=shipping_address,
            notes=notes,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # 7. Save order
        try:
            saved_order = await self.order_repo.save(order)
            logger.info(f"Order created: {saved_order.id} for user {user_id}")
        except Exception as e:
            logger.error(f"Error creating order for user {user_id}: {e}", exc_info=True)
            raise DatabaseError(f"Failed to create order: {e}")

        # 8. Update coupon usage count
        if applied_coupon_id and self.coupon_repo:
            try:
                coupon = await self.coupon_repo.find_by_id(applied_coupon_id)
                if coupon:
                    coupon.used_count += 1
                    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
                        coupon.status = "used"
                    await self.coupon_repo.save(coupon)
            except Exception as e:
                logger.warning(f"Failed to update coupon usage count: {e}")

        # 9. Return DTO
        return OrderDTO.from_entity(saved_order)

    async def _validate_user(self, user_id: int) -> User:
        """Validate that the user exists and is active."""
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found.")
        if not user.is_active:
            raise ValidationError("User is not active and cannot place orders.")
        return user

    def _calculate_subtotal(self, items: List[OrderItemDTO]) -> float:
        """Calculate subtotal from order items."""
        return sum(item.quantity * item.price for item in items)


class OrderItemDTO:
    """Data Transfer Object for order items."""

    def __init__(self, product: str, quantity: int, price: float) -> None:
        self.product = product
        self.quantity = quantity
        self.price = price

    def dict(self) -> Dict[str, Any]:
        return {
            "product": self.product,
            "quantity": self.quantity,
            "price": self.price,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderItemDTO":
        return cls(
            product=data.get("product"),
            quantity=data.get("quantity"),
            price=data.get("price"),
        )