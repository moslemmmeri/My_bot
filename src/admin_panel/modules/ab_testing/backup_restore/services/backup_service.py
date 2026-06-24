# src/admin_panel/modules/backup_restore/services/backup_service.py
import asyncio
import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from my_bot.core.exceptions import DatabaseError, PermissionDeniedError, NotFoundError
from my_bot.core.logger import get_logger
from my_bot.core.config import Config
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager

logger = get_logger(__name__)


class BackupService:
    """Service for creating and managing backups."""

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
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = self.backup_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def create_backup(self) -> Dict[str, Any]:
        """
        Create a full backup including database dump and important files.
        Returns dict with file_path, filename, size, timestamp.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            temp_backup_dir = self.temp_dir / backup_name
            temp_backup_dir.mkdir(parents=True, exist_ok=True)

            # 1. Export database
            db_dump_path = await self._dump_database(temp_backup_dir)
            
            # 2. Backup files (e.g., media, config, logs)
            await self._backup_files(temp_backup_dir)

            # 3. Create metadata
            metadata = {
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "db_dump": db_dump_path.name,
                "files_backup": True,
            }
            with open(temp_backup_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            # 4. Zip everything
            zip_filename = f"{backup_name}.zip"
            zip_path = self.backup_dir / zip_filename
            await self._zip_directory(temp_backup_dir, zip_path)

            # 5. Cleanup temp
            shutil.rmtree(temp_backup_dir)

            size = zip_path.stat().st_size
            logger.info(f"Backup created: {zip_filename} ({size} bytes)")
            return {
                "file_path": str(zip_path),
                "filename": zip_filename,
                "size": size,
                "timestamp": timestamp,
            }

        except PermissionError as e:
            logger.error(f"Permission error creating backup: {e}")
            raise PermissionDeniedError("Insufficient permissions to create backup.") from e
        except Exception as e:
            logger.error(f"Error creating backup: {e}", exc_info=True)
            raise DatabaseError("Failed to create backup.") from e

    async def _dump_database(self, target_dir: Path) -> Path:
        """Dump database to SQL file."""
        db_url = self.config.db_url
        
        # Determine the database type
        if "sqlite" in db_url:
            db_path = db_url.replace("sqlite:///", "")
            dump_path = target_dir / "database.sqlite"
            shutil.copy2(db_path, dump_path)
            logger.info(f"SQLite database copied to {dump_path}")
            return dump_path
        elif "postgresql" in db_url or "postgres" in db_url:
            # For PostgreSQL, use pg_dump (async call)
            # In a real scenario, you'd need to construct the command properly
            import asyncpg
            import subprocess
            import re
            
            # Parse connection details
            match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", db_url)
            if match:
                user, password, host, port, dbname = match.groups()
                dump_path = target_dir / "database.sql"
                # Use subprocess with pg_dump
                # Since it's a blocking call, run in thread pool
                def run_pg_dump():
                    cmd = [
                        "pg_dump",
                        f"--host={host}",
                        f"--port={port}",
                        f"--username={user}",
                        f"--dbname={dbname}",
                        "--clean",
                        "--if-exists",
                        "--no-owner",
                        "--no-privileges",
                    ]
                    env = os.environ.copy()
                    env["PGPASSWORD"] = password
                    with open(dump_path, "w") as f:
                        subprocess.run(cmd, env=env, stdout=f, check=True, text=True)
                
                await asyncio.to_thread(run_pg_dump)
                logger.info(f"PostgreSQL dump saved to {dump_path}")
                return dump_path
            else:
                raise ValueError("Invalid PostgreSQL connection string.")
        else:
            raise NotImplementedError(f"Database type not supported for backup: {db_url}")

    async def _backup_files(self, target_dir: Path) -> None:
        """Backup important files (media, config, logs)."""
        # Example: backup uploads/media directory
        media_dir = Path("media")
        if media_dir.exists():
            dest = target_dir / "media"
            shutil.copytree(media_dir, dest, ignore_dangling_symlinks=True)
            logger.info(f"Media files backed up to {dest}")

        # Backup configs
        config_dir = Path("config")
        if config_dir.exists():
            dest = target_dir / "config"
            shutil.copytree(config_dir, dest, ignore_dangling_symlinks=True)
            logger.info(f"Config files backed up to {dest}")

        # Backup logs (only last 10 MB)
        logs_dir = Path("logs")
        if logs_dir.exists():
            dest = target_dir / "logs"
            dest.mkdir(parents=True, exist_ok=True)
            for log_file in logs_dir.glob("*.log"):
                if log_file.stat().st_size > 10 * 1024 * 1024:
                    # Truncate large logs to last 10MB
                    with open(log_file, "rb") as src:
                        src.seek(-10 * 1024 * 1024, 2)
                        tail = src.read()
                    with open(dest / log_file.name, "wb") as dst:
                        dst.write(tail)
                else:
                    shutil.copy2(log_file, dest / log_file.name)
            logger.info(f"Log files backed up to {dest}")

    async def _zip_directory(self, source_dir: Path, zip_path: Path) -> None:
        """Zip the source directory to a zip file."""
        def zip_func():
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(source_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(source_dir.parent)
                        zipf.write(file_path, arcname)
        await asyncio.to_thread(zip_func)

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

    async def delete_backup(self, filename: str) -> bool:
        """Delete a backup file."""
        backup_path = self.backup_dir / filename
        if not backup_path.exists():
            raise NotFoundError(f"Backup file {filename} not found.")
        
        try:
            backup_path.unlink()
            logger.info(f"Backup {filename} deleted.")
            return True
        except Exception as e:
            logger.error(f"Error deleting backup {filename}: {e}")
            raise DatabaseError("Failed to delete backup.") from e