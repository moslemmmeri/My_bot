# src/scripts/backup_db.py
#!/usr/bin/env python
"""
Database Backup Script

This script creates a backup of the database and optionally compresses
the backup file. It supports both SQLite and PostgreSQL databases.

Usage:
    python -m src.scripts.backup_db [--output-dir DIR] [--compress]
    python -m src.scripts.backup_db --help
"""

import os
import sys
import asyncio
import argparse
import subprocess
import shutil
import gzip
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from my_bot.core.logger import get_logger
from my_bot.core.config import Config
from my_bot.core.exceptions import DatabaseError

logger = get_logger(__name__)


class DatabaseBackup:
    """
    Service for creating database backups.
    """

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config.from_env()
        self.db_url = self.config.db_url
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._detect_db_type()

    def _detect_db_type(self) -> None:
        """Detect database type from connection URL."""
        if "sqlite" in self.db_url:
            self.db_type = "sqlite"
            # Extract database file path
            match = re.search(r"sqlite:///(.+)", self.db_url)
            if match:
                self.db_file = Path(match.group(1))
                if not self.db_file.is_absolute():
                    self.db_file = PROJECT_ROOT / self.db_file
            else:
                # Default fallback
                self.db_file = PROJECT_ROOT / "data" / "database.sqlite"
                self.db_file.parent.mkdir(parents=True, exist_ok=True)
        elif "postgresql" in self.db_url or "postgres" in self.db_url:
            self.db_type = "postgresql"
            self._parse_postgres_url()
        else:
            raise DatabaseError(f"Unsupported database type: {self.db_url}")

    def _parse_postgres_url(self) -> None:
        """Parse PostgreSQL connection string."""
        # Format: postgresql://user:password@host:port/database
        match = re.match(
            r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)",
            self.db_url
        )
        if match:
            self.db_user, self.db_password, self.db_host, self.db_port, self.db_name = match.groups()
        else:
            # Try without password or with different format
            match = re.match(r"postgresql://([^:/]+)(?::(\d+))?/(.+)", self.db_url)
            if match:
                self.db_user = match.group(1)
                self.db_port = match.group(2) or "5432"
                self.db_name = match.group(3)
                self.db_host = "localhost"
                self.db_password = ""
            else:
                raise DatabaseError(f"Could not parse PostgreSQL URL: {self.db_url}")

    def create_backup(self, output_dir: Optional[Path] = None, compress: bool = False) -> Dict[str, Any]:
        """
        Create a database backup.

        Args:
            output_dir: Directory to save the backup (default: backups/)
            compress: Whether to compress the backup file

        Returns:
            dict: Backup information with file path, size, timestamp
        """
        output_dir = Path(output_dir) if output_dir else self.backup_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"db_backup_{timestamp}"
        backup_file = output_dir / backup_name

        try:
            if self.db_type == "sqlite":
                backup_path = self._backup_sqlite(backup_file)
            else:
                backup_path = self._backup_postgres(backup_file)

            # Compress if requested
            if compress and backup_path.exists():
                compressed_path = self._compress_file(backup_path)
                if compressed_path:
                    backup_path.unlink()  # Remove uncompressed
                    backup_path = compressed_path

            stat = backup_path.stat()
            return {
                "file_path": str(backup_path),
                "filename": backup_path.name,
                "size": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "timestamp": timestamp,
                "db_type": self.db_type,
                "compressed": compress,
            }

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise DatabaseError(f"Failed to create backup: {e}") from e

    def _backup_sqlite(self, backup_file: Path) -> Path:
        """Create SQLite backup by copying the database file."""
        if not self.db_file.exists():
            raise DatabaseError(f"SQLite database file not found: {self.db_file}")

        # Append extension
        backup_path = Path(str(backup_file) + ".sqlite")

        # Copy the file
        shutil.copy2(self.db_file, backup_path)
        logger.info(f"SQLite backup created: {backup_path}")

        return backup_path

    def _backup_postgres(self, backup_file: Path) -> Path:
        """Create PostgreSQL backup using pg_dump."""
        # Check if pg_dump is available
        if not shutil.which("pg_dump"):
            raise DatabaseError("pg_dump not found. Please install PostgreSQL client tools.")

        backup_path = Path(str(backup_file) + ".sql")

        # Build pg_dump command
        cmd = [
            "pg_dump",
            f"--host={self.db_host}",
            f"--port={self.db_port}",
            f"--username={self.db_user}",
            f"--dbname={self.db_name}",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
        ]

        # Set password environment variable if needed
        env = os.environ.copy()
        if self.db_password:
            env["PGPASSWORD"] = self.db_password

        # Run pg_dump
        try:
            with open(backup_path, "w") as f:
                result = subprocess.run(
                    cmd,
                    env=env,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )

            if result.returncode != 0:
                raise DatabaseError(f"pg_dump failed: {result.stderr}")

            logger.info(f"PostgreSQL backup created: {backup_path}")
            return backup_path
        except Exception as e:
            raise DatabaseError(f"Failed to create PostgreSQL backup: {e}") from e

    def _compress_file(self, file_path: Path) -> Path:
        """Compress a file using gzip."""
        try:
            compressed_path = Path(str(file_path) + ".gz")
            with open(file_path, "rb") as f_in:
                with gzip.open(compressed_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            logger.info(f"Compressed backup: {compressed_path}")
            return compressed_path
        except Exception as e:
            logger.warning(f"Failed to compress backup: {e}")
            return file_path

    def list_backups(self, output_dir: Optional[Path] = None) -> list:
        """List all backup files."""
        output_dir = Path(output_dir) if output_dir else self.backup_dir
        if not output_dir.exists():
            return []

        backups = []
        patterns = ["*.sqlite", "*.sqlite.gz", "*.sql", "*.sql.gz"]
        for pattern in patterns:
            for file in output_dir.glob(pattern):
                stat = file.stat()
                backups.append({
                    "filename": file.name,
                    "path": str(file),
                    "size": stat.st_size,
                    "size_mb": stat.st_size / (1024 * 1024),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "compressed": file.suffix == ".gz",
                })

        return sorted(backups, key=lambda x: x["created"], reverse=True)

    def restore_backup(self, backup_file: Path) -> Dict[str, Any]:
        """
        Restore a database from a backup file.

        Args:
            backup_file: Path to the backup file

        Returns:
            dict: Restore information
        """
        if not backup_file.exists():
            raise DatabaseError(f"Backup file not found: {backup_file}")

        # Determine backup type from extension
        filename = backup_file.name
        is_compressed = filename.endswith(".gz")
        backup_path = backup_file

        # Extract if compressed
        if is_compressed:
            import tempfile
            temp_dir = Path(tempfile.mkdtemp())
            extracted_path = temp_dir / filename.replace(".gz", "")
            with gzip.open(backup_file, "rb") as f_in:
                with open(extracted_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_path = extracted_path

        try:
            if self.db_type == "sqlite":
                result = self._restore_sqlite(backup_path)
            else:
                result = self._restore_postgres(backup_path)

            # Clean up temp files
            if is_compressed and backup_path.parent.name == "tmp":
                shutil.rmtree(backup_path.parent)

            return result

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise DatabaseError(f"Failed to restore backup: {e}") from e

    def _restore_sqlite(self, backup_path: Path) -> Dict[str, Any]:
        """Restore SQLite database from backup."""
        if self.db_file.exists():
            # Backup current database before restoring
            backup_current = self.db_file.parent / f"{self.db_file.stem}_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite"
            shutil.copy2(self.db_file, backup_current)
            logger.info(f"Current database backed up to: {backup_current}")

        # Restore
        shutil.copy2(backup_path, self.db_file)
        logger.info(f"SQLite database restored from: {backup_path}")
        return {"status": "success", "message": f"Restored from {backup_path.name}"}

    def _restore_postgres(self, backup_path: Path) -> Dict[str, Any]:
        """Restore PostgreSQL database from backup."""
        if not shutil.which("psql"):
            raise DatabaseError("psql not found. Please install PostgreSQL client tools.")

        cmd = [
            "psql",
            f"--host={self.db_host}",
            f"--port={self.db_port}",
            f"--username={self.db_user}",
            f"--dbname={self.db_name}",
            "--file=" + str(backup_path),
        ]

        env = os.environ.copy()
        if self.db_password:
            env["PGPASSWORD"] = self.db_password

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                raise DatabaseError(f"psql restore failed: {result.stderr}")

            logger.info(f"PostgreSQL database restored from: {backup_path}")
            return {"status": "success", "message": f"Restored from {backup_path.name}"}

        except Exception as e:
            raise DatabaseError(f"Failed to restore PostgreSQL backup: {e}") from e


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Database backup and restore utility.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s backup                        # Create a backup
  %(prog)s backup --compress             # Create compressed backup
  %(prog)s backup --output-dir ./my_backups
  %(prog)s list                          # List all backups
  %(prog)s restore ./backups/db_backup.sql
  %(prog)s restore ./backups/db_backup.sql.gz
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a new backup")
    backup_parser.add_argument(
        "-o", "--output-dir",
        help="Directory to save the backup (default: backups/)",
    )
    backup_parser.add_argument(
        "-c", "--compress",
        action="store_true",
        help="Compress the backup file",
    )

    # List command
    subparsers.add_parser("list", help="List all backups")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore a backup")
    restore_parser.add_argument(
        "file",
        help="Path to the backup file to restore",
    )

    return parser.parse_args()


async def main_async() -> None:
    """Async main function."""
    args = parse_arguments()

    try:
        backup = DatabaseBackup()

        if args.command == "backup":
            output_dir = Path(args.output_dir) if args.output_dir else None
            result = backup.create_backup(
                output_dir=output_dir,
                compress=args.compress,
            )
            print("✅ Backup created successfully!")
            print(f"  File: {result['filename']}")
            print(f"  Size: {result['size_mb']:.2f} MB")
            print(f"  Type: {result['db_type']}")
            print(f"  Compressed: {'Yes' if result['compressed'] else 'No'}")
            print(f"  Path: {result['file_path']}")

        elif args.command == "list":
            backups = backup.list_backups()
            if not backups:
                print("No backups found.")
            else:
                print("Backups:")
                for b in backups:
                    size = b['size_mb']
                    if size < 1:
                        size_str = f"{size * 1024:.2f} KB"
                    else:
                        size_str = f"{size:.2f} MB"
                    print(f"  {b['filename']} ({size_str}) - {b['created']}")

        elif args.command == "restore":
            backup_file = Path(args.file)
            if not backup_file.exists():
                print(f"❌ File not found: {args.file}")
                return

            print(f"⏳ Restoring from: {args.file}")
            result = backup.restore_backup(backup_file)
            print("✅ Restore completed successfully!")
            print(f"  {result['message']}")

        else:
            print("Unknown command. Use --help for usage.")

    except DatabaseError as e:
        print(f"\n❌ Database error: {e}")
        logger.error(f"Database error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Unexpected error: {e}", exc_info=True)


def main():
    """Entry point for the script."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()