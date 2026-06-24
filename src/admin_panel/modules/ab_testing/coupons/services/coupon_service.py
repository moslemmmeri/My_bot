# src/admin_panel/modules/coupons/services/coupon_service.py
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import random
import string

from my_bot.core.exceptions import NotFoundError, DatabaseError, ValidationError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.coupon_repository import CouponRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.entities.coupon import Coupon, CouponStatus, CouponType

logger = get_logger(__name__)


class CouponService:
    """Service for managing coupons in admin panel."""

    def __init__(
        self,
        coupon_repo: CouponRepository,
        user_repo: UserRepository,
    ) -> None:
        self.coupon_repo = coupon_repo
        self.user_repo = user_repo

    async def list_coupons(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        coupon_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated list of coupons with optional filters.
        Returns dict with 'items' (list of coupon dicts) and 'total'.
        """
        try:
            offset = (page - 1) * page_size
            coupons, total = await self.coupon_repo.find_filtered(
                status=status,
                coupon_type=coupon_type,
                search=search,
                limit=page_size,
                offset=offset,
            )
            return {
                "items": [self._to_dict(c) for c in coupons],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.error(f"Error listing coupons: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve coupons.") from e

    async def get_coupon(self, coupon_id: int) -> Optional[Dict[str, Any]]:
        """Get a single coupon by ID."""
        try:
            coupon = await self.coupon_repo.find_by_id(coupon_id)
            if not coupon:
                return None
            return self._to_dict(coupon)
        except Exception as e:
            logger.error(f"Error getting coupon {coupon_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve coupon.") from e

    async def get_coupon_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get a coupon by its code."""
        try:
            coupon = await self.coupon_repo.find_by_code(code)
            if not coupon:
                return None
            return self._to_dict(coupon)
        except Exception as e:
            logger.error(f"Error getting coupon by code {code}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve coupon.") from e

    async def create_coupon(
        self,
        code: str,
        discount_type: str,
        discount_value: float,
        usage_limit: int = 0,
        expires_at: Optional[str] = None,
        created_by: Optional[int] = None,
        description: Optional[str] = None,
        min_order_amount: Optional[float] = None,
        applicable_to: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Create a new coupon."""
        try:
            # Validate inputs
            if not code or len(code.strip()) == 0:
                raise ValidationError("Coupon code cannot be empty")
            code = code.strip().upper()

            # Check if code already exists
            existing = await self.coupon_repo.find_by_code(code)
            if existing:
                raise ValidationError(f"Coupon code '{code}' already exists.")

            # Validate discount type
            try:
                discount_type_enum = CouponType(discount_type)
            except ValueError:
                raise ValidationError(f"Invalid discount type: {discount_type}. Valid: percentage, fixed")

            # Validate discount value
            if discount_value <= 0:
                raise ValidationError("Discount value must be greater than 0.")
            if discount_type == "percentage" and discount_value > 100:
                raise ValidationError("Percentage discount cannot exceed 100%.")

            # Parse expiry date
            expiry_date = None
            if expires_at:
                try:
                    # Try to parse as date
                    expiry_date = datetime.strptime(expires_at, "%Y-%m-%d").date()
                except ValueError:
                    raise ValidationError("Invalid expiry date format. Use YYYY-MM-DD.")

            # Create coupon
            coupon = Coupon(
                code=code,
                discount_type=discount_type_enum,
                discount_value=discount_value,
                usage_limit=usage_limit if usage_limit > 0 else None,
                used_count=0,
                status=CouponStatus.ACTIVE,
                expires_at=expiry_date,
                created_by=created_by,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                description=description,
                min_order_amount=min_order_amount,
                applicable_to=applicable_to,
            )
            saved = await self.coupon_repo.save(coupon)
            logger.info(f"Coupon created: {saved.code} by {created_by}")
            return self._to_dict(saved)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating coupon: {e}", exc_info=True)
            raise DatabaseError("Failed to create coupon.") from e

    async def update_coupon_field(
        self,
        coupon_id: int,
        field: str,
        value: Any,
        updated_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update a specific field of a coupon."""
        try:
            coupon = await self.coupon_repo.find_by_id(coupon_id)
            if not coupon:
                raise NotFoundError(f"Coupon {coupon_id} not found")

            # Update based on field
            if field == "code":
                new_code = str(value).strip().upper()
                if not new_code:
                    raise ValidationError("Coupon code cannot be empty")
                # Check uniqueness
                existing = await self.coupon_repo.find_by_code(new_code)
                if existing and existing.id != coupon_id:
                    raise ValidationError(f"Coupon code '{new_code}' already exists.")
                coupon.code = new_code

            elif field == "discount_type":
                try:
                    coupon.discount_type = CouponType(value)
                except ValueError:
                    raise ValidationError(f"Invalid discount type: {value}. Valid: percentage, fixed")

            elif field == "discount_value":
                new_value = float(value)
                if new_value <= 0:
                    raise ValidationError("Discount value must be greater than 0.")
                if coupon.discount_type == CouponType.PERCENTAGE and new_value > 100:
                    raise ValidationError("Percentage discount cannot exceed 100%.")
                coupon.discount_value = new_value

            elif field == "usage_limit":
                new_limit = int(value)
                if new_limit < 0:
                    raise ValidationError("Usage limit cannot be negative.")
                coupon.usage_limit = new_limit if new_limit > 0 else None

            elif field == "expires_at":
                if value is None:
                    coupon.expires_at = None
                else:
                    try:
                        coupon.expires_at = datetime.strptime(str(value), "%Y-%m-%d").date()
                    except ValueError:
                        raise ValidationError("Invalid expiry date format. Use YYYY-MM-DD.")

            elif field == "status":
                try:
                    coupon.status = CouponStatus(value)
                except ValueError:
                    raise ValidationError(f"Invalid status: {value}. Valid: active, inactive, expired, used")

            elif field == "description":
                coupon.description = str(value) if value else None

            elif field == "min_order_amount":
                coupon.min_order_amount = float(value) if value is not None else None

            else:
                raise ValidationError(f"Field '{field}' is not editable.")

            coupon.updated_by = updated_by
            coupon.updated_at = datetime.now()
            saved = await self.coupon_repo.save(coupon)
            logger.info(f"Coupon {coupon_id} field '{field}' updated by {updated_by}")
            return self._to_dict(saved)
        except ValidationError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating coupon {coupon_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to update coupon.") from e

    async def delete_coupon(self, coupon_id: int, deleted_by: Optional[int] = None) -> bool:
        """Delete a coupon."""
        try:
            coupon = await self.coupon_repo.find_by_id(coupon_id)
            if not coupon:
                raise NotFoundError(f"Coupon {coupon_id} not found")

            await self.coupon_repo.delete(coupon_id)
            logger.info(f"Coupon {coupon_id} deleted by {deleted_by}")
            return True
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting coupon {coupon_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to delete coupon.") from e

    async def apply_coupon(
        self,
        code: str,
        user_id: int,
        order_amount: float,
    ) -> Dict[str, Any]:
        """
        Apply a coupon to an order.
        Returns discount amount and updated coupon info.
        """
        try:
            coupon = await self.coupon_repo.find_by_code(code)
            if not coupon:
                raise NotFoundError(f"Coupon '{code}' not found")

            # Validate coupon
            if coupon.status != CouponStatus.ACTIVE:
                raise ValidationError("Coupon is not active.")
            if coupon.expires_at and coupon.expires_at < date.today():
                raise ValidationError("Coupon has expired.")
            if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
                raise ValidationError("Coupon usage limit has been reached.")
            if coupon.min_order_amount and order_amount < coupon.min_order_amount:
                raise ValidationError(f"Minimum order amount is {coupon.min_order_amount}.")

            # Calculate discount
            if coupon.discount_type == CouponType.PERCENTAGE:
                discount_amount = (order_amount * coupon.discount_value) / 100
            else:  # fixed
                discount_amount = coupon.discount_value

            # Cap discount to order amount
            discount_amount = min(discount_amount, order_amount)

            # Increment usage
            coupon.used_count += 1
            if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
                coupon.status = CouponStatus.USED
            coupon.updated_at = datetime.now()
            saved = await self.coupon_repo.save(coupon)

            logger.info(f"Coupon '{code}' applied by user {user_id}, discount: {discount_amount}")
            return {
                "discount_amount": discount_amount,
                "coupon": self._to_dict(saved),
            }
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error applying coupon '{code}': {e}", exc_info=True)
            raise DatabaseError("Failed to apply coupon.") from e

    async def get_coupon_stats(self) -> Dict[str, Any]:
        """Get statistics about coupons."""
        try:
            total = await self.coupon_repo.count()
            active = await self.coupon_repo.count_by_status("active")
            inactive = await self.coupon_repo.count_by_status("inactive")
            expired = await self.coupon_repo.count_by_status("expired")
            used = await self.coupon_repo.count_by_status("used")

            total_usage = await self.coupon_repo.sum_used_count()
            total_discount = await self.coupon_repo.sum_discount_value_applied()

            return {
                "total": total,
                "active": active,
                "inactive": inactive,
                "expired": expired,
                "used": used,
                "total_usage": total_usage,
                "total_discount": total_discount,
            }
        except Exception as e:
            logger.error(f"Error getting coupon stats: {e}", exc_info=True)
            raise DatabaseError("Failed to get coupon statistics.") from e

    async def generate_unique_code(self, length: int = 8) -> str:
        """Generate a unique random coupon code."""
        chars = string.ascii_uppercase + string.digits
        for _ in range(10):  # Try up to 10 times
            code = ''.join(random.choices(chars, k=length))
            existing = await self.coupon_repo.find_by_code(code)
            if not existing:
                return code
        raise DatabaseError("Failed to generate unique coupon code.")

    @staticmethod
    def _to_dict(coupon: Coupon) -> Dict[str, Any]:
        """Convert Coupon entity to dict."""
        return {
            "id": coupon.id,
            "code": coupon.code,
            "discount_type": coupon.discount_type.value if hasattr(coupon.discount_type, 'value') else coupon.discount_type,
            "discount_value": coupon.discount_value,
            "usage_limit": coupon.usage_limit,
            "used_count": coupon.used_count,
            "status": coupon.status.value if hasattr(coupon.status, 'value') else coupon.status,
            "expires_at": coupon.expires_at.isoformat() if coupon.expires_at else None,
            "created_at": coupon.created_at.isoformat() if coupon.created_at else None,
            "updated_at": coupon.updated_at.isoformat() if coupon.updated_at else None,
            "created_by": coupon.created_by,
            "updated_by": getattr(coupon, "updated_by", None),
            "description": getattr(coupon, "description", None),
            "min_order_amount": getattr(coupon, "min_order_amount", None),
            "applicable_to": getattr(coupon, "applicable_to", None),
        }