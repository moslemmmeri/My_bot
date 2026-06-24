# src/admin_panel/modules/backup_restore/services/restore_service.py
import asyncio
import json
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, List

from my_bot.core.exceptions import DatabaseError, NotFoundError, PermissionDeniedError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.core.config import Config
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager

logger = get_logger(__name__)


class RestoreService:
    """Service for restoring backups."""

    def __init__(
        self,
        config: Optional[Config] = None,
        db_manager: Optional[DatabaseSessionManager] = None,
    ) -> None:
        self.config = config or Config.from_env()
        self.db_manager = db_manager or DatabaseSessionManager(
            self.config.db_url,
            self.config.db_pool_size,
            self.config.db_max_overflow,
        )
        self.backup_dir = Path("backups")
        self.temp_dir = self.backup_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backup files."""
        backups = []
        for zip_file in self.backup_dir.glob("*.zip"):
            stat = zip_file.stat()
            backups.append({
                "filename": zip_file.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "path": str(zip_file),
            })
        return sorted(backups, key=lambda x: x["created"], reverse=True)

    async def restore_backup(self, filename: str) -> Dict[str, Any]:
        """
        Restore a backup from a zip file.
        Returns dict with success status, duration, records_restored.
        """
        import time
        start_time = time.time()

        backup_path = self.backup_dir / filename
        if not backup_path.exists():
            raise NotFoundError(f"Backup file {filename} not found.")

        # Create a temporary extraction directory
        extract_dir = self.temp_dir / f"restore_{filename.replace('.zip', '')}"
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Extract the backup
            await self._extract_zip(backup_path, extract_dir)

            # 2. Read metadata
            metadata_file = extract_dir / "metadata.json"
            if not metadata_file.exists():
                raise ValidationError("Backup metadata not found. The backup may be corrupted.")
            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            # 3. Restore database
            db_dump_name = metadata.get("db_dump")
            if not db_dump_name:
                raise ValidationError("Database dump file not found in backup.")
            db_dump_path = extract_dir / db_dump_name
            if not db_dump_path.exists():
                raise ValidationError(f"Database dump file {db_dump_name} not found.")

            records_restored = await self._restore_database(db_dump_path)

            # 4. Restore files (media, config, logs)
            await self._restore_files(extract_dir)

            duration = time.time() - start_time
            logger.info(f"Backup {filename} restored successfully in {duration:.2f}s")
            return {
                "success": True,
                "duration": round(duration, 2),
                "records_restored": records_restored,
            }

        except Exception as e:
            logger.error(f"Error restoring backup {filename}: {e}", exc_info=True)
            raise DatabaseError(f"Failed to restore backup: {str(e)}")
        finally:
            # Cleanup temp extraction directory
            if extract_dir.exists():
                shutil.rmtree(extract_dir)

    async def _extract_zip(self, zip_path: Path, target_dir: Path) -> None:
        """Extract a zip file to the target directory."""
        def extract():
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(target_dir)
        await asyncio.to_thread(extract)
        logger.info(f"Extracted {zip_path.name} to {target_dir}")

    async def _restore_database(self, dump_path: Path) -> int:
        """Restore database from dump file."""
        db_url = self.config.db_url
        records_restored = 0

        if "sqlite" in db_url:
            # For SQLite, just copy the file
            db_path = db_url.replace("sqlite:///", "")
            target_db = Path(db_path)
            shutil.copy2(dump_path, target_db)
            logger.info(f"SQLite database restored from {dump_path} to {target_db}")
            # Approximate records count (could parse, but we'll return 0)
            records_restored = 0

        elif "postgresql" in db_url or "postgres" in db_url:
            import subprocess
            import re
            import os

            match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", db_url)
            if match:
                user, password, host, port, dbname = match.groups()
                # Use psql to restore
                def run_psql():
                    cmd = [
                        "psql",
                        f"--host={host}",
                        f"--port={port}",
                        f"--username={user}",
                        f"--dbname={dbname}",
                        "--file=" + str(dump_path),
                    ]
                    env = os.environ.copy()
                    env["PGPASSWORD"] = password
                    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise DatabaseError(f"psql error: {result.stderr}")
                    return result.stderr  # psql outputs number of restored rows in stderr

                output = await asyncio.to_thread(run_psql)
                # Parse output for row count (rough)
                import re
                match_count = re.search(r"COPY (\d+)", output)
                if match_count:
                    records_restored = int(match_count.group(1))
                else:
                    records_restored = 0
                logger.info(f"PostgreSQL database restored from {dump_path}")
            else:
                raise ValidationError("Invalid PostgreSQL connection string.")
        else:
            raise NotImplementedError(f"Database type not supported for restore: {db_url}")

        return records_restored

    async def _restore_files(self, extract_dir: Path) -> None:
        """Restore files (media, config, logs) from backup."""
        # Restore media
        media_backup = extract_dir / "media"
        if media_backup.exists():
            target_media = Path("media")
            if target_media.exists():
                shutil.rmtree(target_media)
            shutil.copytree(media_backup, target_media)
            logger.info("Media files restored.")

        # Restore config
        config_backup = extract_dir / "config"
        if config_backup.exists():
            target_config = Path("config")
            if target_config.exists():
                shutil.rmtree(target_config)
            shutil.copytree(config_backup, target_config)
            logger.info("Config files restored.")

        # Restore logs (might be overwritten or merged - we'll overwrite)
        logs_backup = extract_dir / "logs"
        if logs_backup.exists():
            target_logs = Path("logs")
            if target_logs.exists():
                shutil.rmtree(target_logs)
            shutil.copytree(logs_backup, target_logs)
            logger.info("Log files restored.")

    async def get_backup_info(self, filename: str) -> Dict[str, Any]:
        """Get detailed info about a backup without restoring."""
        backup_path = self.backup_dir / filename
        if not backup_path.exists():
            raise NotFoundError(f"Backup file {filename} not found.")

        # Extract just the metadata
        extract_dir = self.temp_dir / f"info_{filename.replace('.zip', '')}"
        extract_dir.mkdir(parents=True, exist_ok=True)
        try:
            await self._extract_zip(backup_path, extract_dir)
            metadata_file = extract_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
            else:
                metadata = {"error": "No metadata found"}
            return metadata
        finally:
            if extract_dir.exists():
                shutil.rmtree(extract_dir)