# src/admin_panel/modules/ab_testing/services/ab_test_service.py
from typing import Optional, List, Dict, Any
from datetime import datetime
import random
import string

from my_bot.core.exceptions import NotFoundError, DatabaseError, ValidationError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.ab_test_repository import ABTestRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.entities.ab_test import ABTest, ABTestVariant, ABTestStatus

logger = get_logger(__name__)


class ABTestService:
    """Service for managing A/B tests in admin panel."""

    def __init__(
        self,
        ab_test_repo: ABTestRepository,
        user_repo: UserRepository,
    ) -> None:
        self.ab_test_repo = ab_test_repo
        self.user_repo = user_repo

    async def list_tests(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated list of A/B tests with optional filters.
        Returns dict with 'items' (list of test dicts) and 'total'.
        """
        try:
            offset = (page - 1) * page_size
            tests, total = await self.ab_test_repo.find_filtered(
                status=status,
                search=search,
                limit=page_size,
                offset=offset,
            )
            items = []
            for test in tests:
                variants = await self.ab_test_repo.get_variants(test.id)
                items.append({
                    "id": test.id,
                    "name": test.name,
                    "description": test.description,
                    "status": test.status.value if hasattr(test.status, 'value') else test.status,
                    "variants": [self._variant_to_dict(v) for v in variants],
                    "variant_count": len(variants),
                    "created_by": test.created_by,
                    "created_at": test.created_at.isoformat() if test.created_at else None,
                    "updated_at": test.updated_at.isoformat() if test.updated_at else None,
                })
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.error(f"Error listing A/B tests: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve A/B tests.") from e

    async def get_test(self, test_id: int) -> Optional[Dict[str, Any]]:
        """Get a single A/B test by ID with its variants."""
        try:
            test = await self.ab_test_repo.find_by_id(test_id)
            if not test:
                return None

            variants = await self.ab_test_repo.get_variants(test_id)
            return {
                "id": test.id,
                "name": test.name,
                "description": test.description,
                "status": test.status.value if hasattr(test.status, 'value') else test.status,
                "variants": [self._variant_to_dict(v) for v in variants],
                "created_by": test.created_by,
                "created_at": test.created_at.isoformat() if test.created_at else None,
                "updated_at": test.updated_at.isoformat() if test.updated_at else None,
                "started_at": test.started_at.isoformat() if test.started_at else None,
                "ended_at": test.ended_at.isoformat() if test.ended_at else None,
            }
        except Exception as e:
            logger.error(f"Error getting A/B test {test_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve A/B test.") from e

    async def create_test(
        self,
        name: str,
        description: Optional[str] = None,
        variants: Optional[List[Dict[str, Any]]] = None,
        created_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new A/B test with variants."""
        try:
            # Validate inputs
            if not name or len(name.strip()) == 0:
                raise ValidationError("Test name cannot be empty.")
            name = name.strip()

            if variants is None or len(variants) < 2:
                raise ValidationError("At least 2 variants are required for A/B test.")

            # Validate variants
            variant_names = []
            for idx, variant_data in enumerate(variants):
                variant_name = variant_data.get("name", "").strip()
                if not variant_name:
                    raise ValidationError(f"Variant {idx + 1} name cannot be empty.")
                if variant_name in variant_names:
                    raise ValidationError(f"Duplicate variant name: {variant_name}")
                variant_names.append(variant_name)

            # Create test
            test = ABTest(
                name=name,
                description=description.strip() if description else None,
                status=ABTestStatus.DRAFT,
                created_by=created_by,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            saved_test = await self.ab_test_repo.save(test)

            # Create variants
            saved_variants = []
            for variant_data in variants:
                variant = ABTestVariant(
                    test_id=saved_test.id,
                    name=variant_data["name"].strip(),
                    content=variant_data.get("content", "").strip() or None,
                    weight=variant_data.get("weight", 1),
                    views=0,
                    conversions=0,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                saved_variant = await self.ab_test_repo.save_variant(variant)
                saved_variants.append(saved_variant)

            logger.info(f"A/B test created: {saved_test.id} - {saved_test.name} by {created_by}")
            return {
                "id": saved_test.id,
                "name": saved_test.name,
                "description": saved_test.description,
                "status": saved_test.status.value,
                "variants": [self._variant_to_dict(v) for v in saved_variants],
                "created_at": saved_test.created_at.isoformat(),
            }
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}", exc_info=True)
            raise DatabaseError("Failed to create A/B test.") from e

    async def update_test(
        self,
        test_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        updated_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update an existing A/B test."""
        try:
            test = await self.ab_test_repo.find_by_id(test_id)
            if not test:
                raise NotFoundError(f"A/B test {test_id} not found.")

            if name is not None:
                if not name or len(name.strip()) == 0:
                    raise ValidationError("Test name cannot be empty.")
                test.name = name.strip()

            if description is not None:
                test.description = description.strip() if description else None

            if status is not None:
                try:
                    test.status = ABTestStatus(status)
                except ValueError:
                    raise ValidationError(f"Invalid status: {status}")

                # If status changed to active, set started_at
                if test.status == ABTestStatus.ACTIVE and not test.started_at:
                    test.started_at = datetime.now()
                # If status changed to completed, set ended_at
                if test.status == ABTestStatus.COMPLETED and not test.ended_at:
                    test.ended_at = datetime.now()

            test.updated_by = updated_by
            test.updated_at = datetime.now()
            saved = await self.ab_test_repo.save(test)

            logger.info(f"A/B test {test_id} updated by {updated_by}")
            variants = await self.ab_test_repo.get_variants(test_id)
            return {
                "id": saved.id,
                "name": saved.name,
                "description": saved.description,
                "status": saved.status.value,
                "variants": [self._variant_to_dict(v) for v in variants],
                "updated_at": saved.updated_at.isoformat(),
            }
        except ValidationError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating A/B test {test_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to update A/B test.") from e

    async def delete_test(self, test_id: int, deleted_by: Optional[int] = None) -> bool:
        """Delete an A/B test."""
        try:
            test = await self.ab_test_repo.find_by_id(test_id)
            if not test:
                raise NotFoundError(f"A/B test {test_id} not found.")

            # Only allow deleting tests in draft or archived status
            if test.status not in [ABTestStatus.DRAFT, ABTestStatus.ARCHIVED]:
                raise PermissionDeniedError("Only draft or archived tests can be deleted.")

            await self.ab_test_repo.delete(test_id)
            logger.info(f"A/B test {test_id} deleted by {deleted_by}")
            return True
        except NotFoundError:
            raise
        except PermissionDeniedError:
            raise
        except Exception as e:
            logger.error(f"Error deleting A/B test {test_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to delete A/B test.") from e

    async def stop_test(self, test_id: int, stopped_by: Optional[int] = None) -> Dict[str, Any]:
        """Stop an active A/B test."""
        try:
            test = await self.ab_test_repo.find_by_id(test_id)
            if not test:
                raise NotFoundError(f"A/B test {test_id} not found.")

            if test.status != ABTestStatus.ACTIVE:
                raise ValidationError("Only active tests can be stopped.")

            test.status = ABTestStatus.PAUSED
            test.updated_by = stopped_by
            test.updated_at = datetime.now()
            saved = await self.ab_test_repo.save(test)

            logger.info(f"A/B test {test_id} stopped by {stopped_by}")
            variants = await self.ab_test_repo.get_variants(test_id)
            return {
                "id": saved.id,
                "name": saved.name,
                "status": saved.status.value,
                "variants": [self._variant_to_dict(v) for v in variants],
            }
        except ValidationError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error stopping A/B test {test_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to stop A/B test.") from e

    async def get_test_stats(self, test_id: int) -> Dict[str, Any]:
        """Get statistics for an A/B test."""
        try:
            test = await self.ab_test_repo.find_by_id(test_id)
            if not test:
                raise NotFoundError(f"A/B test {test_id} not found.")

            variants = await self.ab_test_repo.get_variants(test_id)
            total_views = sum(v.views for v in variants)
            total_conversions = sum(v.conversions for v in variants)

            variant_stats = []
            for variant in variants:
                conversion_rate = (variant.conversions / variant.views * 100) if variant.views > 0 else 0
                variant_stats.append({
                    "id": variant.id,
                    "name": variant.name,
                    "views": variant.views,
                    "conversions": variant.conversions,
                    "conversion_rate": round(conversion_rate, 2),
                    "weight": variant.weight,
                })

            return {
                "test_id": test_id,
                "test_name": test.name,
                "status": test.status.value,
                "total_views": total_views,
                "total_conversions": total_conversions,
                "overall_conversion_rate": round((total_conversions / total_views * 100) if total_views > 0 else 0, 2),
                "variants": variant_stats,
            }
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting stats for A/B test {test_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to get A/B test statistics.") from e

    async def record_view(self, test_id: int, variant_id: int) -> bool:
        """Record a view for a specific variant."""
        try:
            variant = await self.ab_test_repo.find_variant_by_id(variant_id)
            if not variant:
                raise NotFoundError(f"Variant {variant_id} not found.")

            variant.views += 1
            variant.updated_at = datetime.now()
            await self.ab_test_repo.save_variant(variant)
            return True
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error recording view for variant {variant_id}: {e}", exc_info=True)
            return False

    async def record_conversion(self, test_id: int, variant_id: int) -> bool:
        """Record a conversion for a specific variant."""
        try:
            variant = await self.ab_test_repo.find_variant_by_id(variant_id)
            if not variant:
                raise NotFoundError(f"Variant {variant_id} not found.")

            variant.conversions += 1
            variant.updated_at = datetime.now()
            await self.ab_test_repo.save_variant(variant)
            return True
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error recording conversion for variant {variant_id}: {e}", exc_info=True)
            return False

    async def get_active_test(self, test_id: int) -> Optional[Dict[str, Any]]:
        """Get an active test with variants for assignment."""
        try:
            test = await self.ab_test_repo.find_by_id(test_id)
            if not test or test.status != ABTestStatus.ACTIVE:
                return None

            variants = await self.ab_test_repo.get_variants(test_id)
            return {
                "id": test.id,
                "name": test.name,
                "variants": [
                    {
                        "id": v.id,
                        "name": v.name,
                        "content": v.content,
                        "weight": v.weight,
                    } for v in variants
                ],
            }
        except Exception as e:
            logger.error(f"Error getting active test {test_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def _variant_to_dict(variant: ABTestVariant) -> Dict[str, Any]:
        """Convert ABTestVariant entity to dict."""
        return {
            "id": variant.id,
            "name": variant.name,
            "content": variant.content,
            "weight": variant.weight,
            "views": variant.views,
            "conversions": variant.conversions,
            "created_at": variant.created_at.isoformat() if variant.created_at else None,
            "updated_at": variant.updated_at.isoformat() if variant.updated_at else None,
        }