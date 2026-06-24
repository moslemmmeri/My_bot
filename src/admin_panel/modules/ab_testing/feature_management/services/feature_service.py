# src/admin_panel/modules/feature_management/services/feature_service.py
from typing import Optional, List, Dict, Any
from datetime import datetime

from my_bot.core.exceptions import NotFoundError, DatabaseError, ValidationError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.core.feature_flags.flag_manager import FeatureFlagManager
from my_bot.domain.interfaces.repositories.feature_repository import FeatureRepository
from my_bot.domain.entities.feature import Feature

logger = get_logger(__name__)


class FeatureService:
    """Service for managing feature flags in admin panel."""

    def __init__(
        self,
        feature_repo: FeatureRepository,
        flag_manager: FeatureFlagManager,
    ) -> None:
        self.feature_repo = feature_repo
        self.flag_manager = flag_manager

    async def list_features(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_enabled: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated list of features with optional filters.
        Returns dict with 'items' (list of feature dicts) and 'total'.
        """
        try:
            offset = (page - 1) * page_size
            features, total = await self.feature_repo.find_filtered(
                search=search,
                is_enabled=is_enabled,
                limit=page_size,
                offset=offset,
            )
            return {
                "items": [self._to_dict(feature) for feature in features],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.error(f"Error listing features: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve features.") from e

    async def get_feature(self, feature_id: int) -> Optional[Dict[str, Any]]:
        """Get a single feature by ID."""
        try:
            feature = await self.feature_repo.find_by_id(feature_id)
            if not feature:
                return None
            return self._to_dict(feature)
        except Exception as e:
            logger.error(f"Error getting feature {feature_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve feature.") from e

    async def get_feature_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a feature by its name."""
        try:
            feature = await self.feature_repo.find_by_name(name)
            if not feature:
                return None
            return self._to_dict(feature)
        except Exception as e:
            logger.error(f"Error getting feature by name {name}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve feature.") from e

    async def add_feature(
        self,
        name: str,
        description: Optional[str] = None,
        is_enabled: bool = False,
        created_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add a new feature flag."""
        try:
            # Validate
            if not name or len(name.strip()) == 0:
                raise ValidationError("Feature name cannot be empty.")
            name = name.strip()

            # Check if feature already exists
            existing = await self.feature_repo.find_by_name(name)
            if existing:
                raise ValidationError(f"Feature '{name}' already exists.")

            # Create feature
            feature = Feature(
                name=name,
                description=description.strip() if description else None,
                is_enabled=is_enabled,
                created_by=created_by,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            saved = await self.feature_repo.save(feature)

            # Sync with flag manager (if enabled)
            if is_enabled:
                self.flag_manager.enable(name)
            else:
                self.flag_manager.disable(name)

            logger.info(f"Feature created: {saved.name} by {created_by}")
            return self._to_dict(saved)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error adding feature: {e}", exc_info=True)
            raise DatabaseError("Failed to add feature.") from e

    async def update_feature(
        self,
        feature_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update a feature's metadata."""
        try:
            feature = await self.feature_repo.find_by_id(feature_id)
            if not feature:
                raise NotFoundError(f"Feature {feature_id} not found.")

            if name is not None:
                if not name or len(name.strip()) == 0:
                    raise ValidationError("Feature name cannot be empty.")
                new_name = name.strip()
                # Check uniqueness
                existing = await self.feature_repo.find_by_name(new_name)
                if existing and existing.id != feature_id:
                    raise ValidationError(f"Feature '{new_name}' already exists.")
                # Update flag manager if name changed
                if new_name != feature.name:
                    # Disable old name, enable new name if enabled
                    if feature.is_enabled:
                        self.flag_manager.disable(feature.name)
                        self.flag_manager.enable(new_name)
                feature.name = new_name

            if description is not None:
                feature.description = description.strip() if description else None

            feature.updated_by = updated_by
            feature.updated_at = datetime.now()
            saved = await self.feature_repo.save(feature)

            logger.info(f"Feature {feature_id} updated by {updated_by}")
            return self._to_dict(saved)
        except ValidationError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating feature {feature_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to update feature.") from e

    async def toggle_feature(self, feature_id: int, is_enabled: bool, updated_by: Optional[int] = None) -> Dict[str, Any]:
        """Toggle a feature flag on/off."""
        try:
            feature = await self.feature_repo.find_by_id(feature_id)
            if not feature:
                raise NotFoundError(f"Feature {feature_id} not found.")

            feature.is_enabled = is_enabled
            feature.updated_by = updated_by
            feature.updated_at = datetime.now()
            saved = await self.feature_repo.save(feature)

            # Sync with flag manager
            if is_enabled:
                self.flag_manager.enable(feature.name)
            else:
                self.flag_manager.disable(feature.name)

            logger.info(f"Feature {feature_id} ({feature.name}) toggled to {is_enabled} by {updated_by}")
            return self._to_dict(saved)
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error toggling feature {feature_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to toggle feature.") from e

    async def delete_feature(self, feature_id: int, deleted_by: Optional[int] = None) -> bool:
        """Delete a feature flag."""
        try:
            feature = await self.feature_repo.find_by_id(feature_id)
            if not feature:
                raise NotFoundError(f"Feature {feature_id} not found.")

            # Remove from flag manager
            if feature.is_enabled:
                self.flag_manager.disable(feature.name)

            await self.feature_repo.delete(feature_id)
            logger.info(f"Feature {feature_id} ({feature.name}) deleted by {deleted_by}")
            return True
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting feature {feature_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to delete feature.") from e

    async def sync_from_manager(self) -> Dict[str, Any]:
        """Sync database features with FeatureFlagManager."""
        try:
            # Get all features from database
            features = await self.feature_repo.find_all()
            db_names = {f.name for f in features}

            # Get all flags from manager
            manager_flags = self.flag_manager.list_all()
            manager_names = set(manager_flags.keys())

            # Find differences
            to_add = manager_names - db_names
            to_remove = db_names - manager_names
            to_update = manager_names & db_names

            # Add missing features
            added = []
            for name in to_add:
                try:
                    feature = await self.feature_repo.save(
                        Feature(
                            name=name,
                            description=f"Synced from flag manager",
                            is_enabled=manager_flags.get(name, False),
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                        )
                    )
                    added.append(feature.name)
                except Exception as e:
                    logger.error(f"Error adding synced feature {name}: {e}")

            # Update existing features
            updated = []
            for name in to_update:
                try:
                    feature = await self.feature_repo.find_by_name(name)
                    if feature and feature.is_enabled != manager_flags.get(name, False):
                        feature.is_enabled = manager_flags.get(name, False)
                        feature.updated_at = datetime.now()
                        await self.feature_repo.save(feature)
                        updated.append(feature.name)
                except Exception as e:
                    logger.error(f"Error updating synced feature {name}: {e}")

            # Remove features not in manager (optional - we may want to keep them)
            # For safety, we won't auto-delete

            logger.info(f"Sync completed: added {len(added)}, updated {len(updated)}")
            return {
                "added": added,
                "updated": updated,
                "total_managed": len(manager_flags),
                "total_db": len(db_names),
            }
        except Exception as e:
            logger.error(f"Error syncing features with manager: {e}", exc_info=True)
            raise DatabaseError("Failed to sync features.") from e

    async def get_feature_stats(self) -> Dict[str, Any]:
        """Get statistics about features."""
        try:
            total = await self.feature_repo.count()
            enabled = await self.feature_repo.count_enabled()
            disabled = total - enabled

            return {
                "total": total,
                "enabled": enabled,
                "disabled": disabled,
            }
        except Exception as e:
            logger.error(f"Error getting feature stats: {e}", exc_info=True)
            raise DatabaseError("Failed to get feature statistics.") from e

    @staticmethod
    def _to_dict(feature: Feature) -> Dict[str, Any]:
        """Convert Feature entity to dict."""
        return {
            "id": feature.id,
            "name": feature.name,
            "description": feature.description,
            "is_enabled": feature.is_enabled,
            "created_by": feature.created_by,
            "updated_by": getattr(feature, "updated_by", None),
            "created_at": feature.created_at.isoformat() if feature.created_at else None,
            "updated_at": feature.updated_at.isoformat() if feature.updated_at else None,
        }