# src/admin_panel/modules/feature_management/services/feature_sync_service.py
from typing import Dict, Any, List, Optional
from datetime import datetime

from my_bot.core.exceptions import DatabaseError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.core.feature_flags.flag_manager import FeatureFlagManager
from my_bot.domain.interfaces.repositories.feature_repository import FeatureRepository
from my_bot.domain.entities.feature import Feature

logger = get_logger(__name__)


class FeatureSyncService:
    """Service for synchronizing features between database and flag manager."""

    def __init__(
        self,
        feature_repo: FeatureRepository,
        flag_manager: FeatureFlagManager,
    ) -> None:
        self.feature_repo = feature_repo
        self.flag_manager = flag_manager

    async def sync_from_manager(self) -> Dict[str, Any]:
        """
        Sync database features with FeatureFlagManager.
        Returns dict with added, updated, and removed counts.
        """
        try:
            # Get all features from database
            db_features = await self.feature_repo.find_all()
            db_names = {f.name: f for f in db_features}

            # Get all flags from manager
            manager_flags = self.flag_manager.list_all()
            manager_names = set(manager_flags.keys())

            # Initialize result
            result = {
                "added": [],
                "updated": [],
                "removed": [],
                "total_db": len(db_names),
                "total_manager": len(manager_names),
            }

            # Add features from manager that don't exist in DB
            for name in manager_names:
                if name not in db_names:
                    feature = Feature(
                        name=name,
                        description=f"Synced from flag manager at {datetime.now().isoformat()}",
                        is_enabled=manager_flags.get(name, False),
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    saved = await self.feature_repo.save(feature)
                    result["added"].append({
                        "id": saved.id,
                        "name": saved.name,
                        "is_enabled": saved.is_enabled,
                    })
                    logger.info(f"Feature '{name}' added to database from manager")

            # Update existing features if status differs
            for name in db_names:
                if name in manager_names:
                    db_feature = db_names[name]
                    manager_enabled = manager_flags.get(name, False)
                    if db_feature.is_enabled != manager_enabled:
                        db_feature.is_enabled = manager_enabled
                        db_feature.updated_at = datetime.now()
                        saved = await self.feature_repo.save(db_feature)
                        result["updated"].append({
                            "id": saved.id,
                            "name": saved.name,
                            "old_status": db_feature.is_enabled,
                            "new_status": manager_enabled,
                        })
                        logger.info(f"Feature '{name}' status synced: {manager_enabled}")

            # Remove features from DB that don't exist in manager (if configured)
            # Note: This is optional and should be used with caution
            for name in db_names:
                if name not in manager_names:
                    # We'll only mark as removed but not actually delete
                    result["removed"].append({
                        "name": name,
                        "id": db_names[name].id,
                    })

            logger.info(
                f"Sync completed: added {len(result['added'])}, "
                f"updated {len(result['updated'])}, "
                f"removed (only flagged) {len(result['removed'])}"
            )
            return result

        except Exception as e:
            logger.error(f"Error syncing from manager: {e}", exc_info=True)
            raise DatabaseError("Failed to sync features from manager.") from e

    async def sync_to_manager(self) -> Dict[str, Any]:
        """
        Sync FeatureFlagManager with database features.
        Returns dict with updated flags in manager.
        """
        try:
            # Get all features from database
            db_features = await self.feature_repo.find_all()
            db_names = {f.name: f for f in db_features}

            # Get all flags from manager
            manager_flags = self.flag_manager.list_all()
            manager_names = set(manager_flags.keys())

            result = {
                "updated": [],
                "added_to_manager": [],
                "removed_from_manager": [],
            }

            # Update manager with DB status
            for name, feature in db_names.items():
                current_enabled = manager_flags.get(name, None)
                if current_enabled != feature.is_enabled:
                    if feature.is_enabled:
                        self.flag_manager.enable(name)
                    else:
                        self.flag_manager.disable(name)
                    result["updated"].append({
                        "name": name,
                        "old_status": current_enabled,
                        "new_status": feature.is_enabled,
                    })
                    logger.info(f"Manager sync: {name} -> {feature.is_enabled}")

            # Add features to manager that don't exist (but are in DB)
            for name, feature in db_names.items():
                if name not in manager_names:
                    if feature.is_enabled:
                        self.flag_manager.enable(name)
                    result["added_to_manager"].append({
                        "name": name,
                        "is_enabled": feature.is_enabled,
                    })
                    logger.info(f"Feature '{name}' added to manager")

            # Remove features from manager that don't exist in DB (optional)
            for name in manager_names:
                if name not in db_names:
                    self.flag_manager.disable(name)
                    result["removed_from_manager"].append({
                        "name": name,
                    })
                    logger.info(f"Feature '{name}' removed from manager")

            logger.info(
                f"Sync to manager completed: updated {len(result['updated'])}, "
                f"added {len(result['added_to_manager'])}, "
                f"removed {len(result['removed_from_manager'])}"
            )
            return result

        except Exception as e:
            logger.error(f"Error syncing to manager: {e}", exc_info=True)
            raise DatabaseError("Failed to sync features to manager.") from e

    async def sync_bidirectional(self) -> Dict[str, Any]:
        """
        Perform a bidirectional sync between database and manager.
        This ensures both sides are consistent.
        """
        try:
            # First sync from manager to DB
            from_manager = await self.sync_from_manager()

            # Then sync from DB to manager (to update manager with any changes)
            to_manager = await self.sync_to_manager()

            return {
                "from_manager": from_manager,
                "to_manager": to_manager,
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error during bidirectional sync: {e}", exc_info=True)
            raise DatabaseError("Failed to perform bidirectional sync.") from e

    async def get_sync_status(self) -> Dict[str, Any]:
        """
        Get the synchronization status between database and manager.
        Returns differences between the two sources.
        """
        try:
            # Get all features from database
            db_features = await self.feature_repo.find_all()
            db_names = {f.name: f for f in db_features}

            # Get all flags from manager
            manager_flags = self.flag_manager.list_all()
            manager_names = set(manager_flags.keys())

            # Find differences
            only_in_db = db_names.keys() - manager_names
            only_in_manager = manager_names - db_names.keys()

            # Check status differences
            status_diff = []
            for name in (db_names.keys() & manager_names):
                db_feature = db_names[name]
                manager_enabled = manager_flags.get(name, False)
                if db_feature.is_enabled != manager_enabled:
                    status_diff.append({
                        "name": name,
                        "db_status": db_feature.is_enabled,
                        "manager_status": manager_enabled,
                    })

            return {
                "is_synced": len(only_in_db) == 0 and len(only_in_manager) == 0 and len(status_diff) == 0,
                "only_in_db": list(only_in_db),
                "only_in_manager": list(only_in_manager),
                "status_differences": status_diff,
                "total_db": len(db_names),
                "total_manager": len(manager_names),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting sync status: {e}", exc_info=True)
            raise DatabaseError("Failed to get sync status.") from e

    async def force_resync(self, direction: str = "bidirectional") -> Dict[str, Any]:
        """
        Force a full resync between database and manager.
        direction: 'from_manager', 'to_manager', or 'bidirectional'
        """
        if direction not in ["from_manager", "to_manager", "bidirectional"]:
            raise ValidationError(f"Invalid direction: {direction}")

        try:
            if direction == "from_manager":
                return await self.sync_from_manager()
            elif direction == "to_manager":
                return await self.sync_to_manager()
            else:
                return await self.sync_bidirectional()

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error during force resync: {e}", exc_info=True)
            raise DatabaseError("Failed to perform force resync.") from e