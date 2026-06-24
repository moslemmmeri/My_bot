# src/scripts/db_migrate.py
#!/usr/bin/env python
"""
Database Migration Script

This script provides CLI commands for managing database migrations
using Alembic. It can be run directly or imported as a module.

Usage:
    python -m src.scripts.db_migrate --help
    python -m src.scripts.db_migrate init
    python -m src.scripts.db_migrate migrate -m "message"
    python -m src.scripts.db_migrate upgrade
    python -m src.scripts.db_migrate downgrade -1
    python -m src.scripts.db_migrate status
    python -m src.scripts.db_migrate current
    python -m src.scripts.db_migrate history
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from my_bot.core.logger import get_logger
from my_bot.core.config import Config

logger = get_logger(__name__)


class MigrationManager:
    """
    Manages database migrations using Alembic.
    """

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config.from_env()
        self.project_root = PROJECT_ROOT
        self.alembic_ini = self.project_root / "alembic.ini"
        self.migrations_dir = self.project_root / "migrations"
        self._ensure_alembic()

    def _ensure_alembic(self) -> None:
        """Ensure Alembic is installed and initialized."""
        try:
            import alembic
        except ImportError:
            logger.error("Alembic is not installed. Please run: pip install alembic")
            sys.exit(1)

        # Check if alembic is initialized
        if not self.alembic_ini.exists():
            logger.info("Alembic not initialized. Running init...")
            self.init()

    def _run_alembic_command(self, command: str, *args: str) -> subprocess.CompletedProcess:
        """
        Run an Alembic command as a subprocess.

        Args:
            command: Alembic command (e.g., 'upgrade', 'downgrade')
            *args: Additional arguments for the command

        Returns:
            CompletedProcess with stdout and stderr
        """
        cmd = ["alembic", command]
        cmd.extend(args)

        # Add config file path if not default
        if self.alembic_ini.exists():
            cmd.extend(["--config", str(self.alembic_ini)])

        logger.debug(f"Running: {' '.join(cmd)}")
        return subprocess.run(
            cmd,
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
        )

    def init(self) -> bool:
        """
        Initialize Alembic migrations.
        Creates migrations directory and alembic.ini.
        """
        try:
            result = self._run_alembic_command("init", "migrations")
            if result.returncode != 0:
                logger.error(f"Failed to initialize migrations: {result.stderr}")
                return False

            # Update alembic.ini with database URL from config
            self._update_alembic_config()
            logger.info("Migrations initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Error initializing migrations: {e}")
            return False

    def _update_alembic_config(self) -> None:
        """Update alembic.ini with database URL from config."""
        if not self.alembic_ini.exists():
            logger.warning("alembic.ini not found. Skipping update.")
            return

        try:
            with open(self.alembic_ini, "r") as f:
                content = f.read()

            # Replace sqlalchemy.url with config value
            db_url = self.config.db_url
            # Escape special characters for replacement
            db_url_escaped = db_url.replace("\\", "\\\\")
            import re
            content = re.sub(
                r"sqlalchemy\.url\s*=\s*.+",
                f"sqlalchemy.url = {db_url_escaped}",
                content
            )

            with open(self.alembic_ini, "w") as f:
                f.write(content)

            logger.info("Updated alembic.ini with database URL.")
        except Exception as e:
            logger.error(f"Failed to update alembic.ini: {e}")

    def create_migration(self, message: str, autogenerate: bool = True) -> bool:
        """
        Create a new migration.

        Args:
            message: Migration message
            autogenerate: Whether to autogenerate from model changes

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = ["revision", "--message", message]
            if autogenerate:
                cmd.append("--autogenerate")
            result = self._run_alembic_command(*cmd)
            if result.returncode != 0:
                logger.error(f"Failed to create migration: {result.stderr}")
                return False

            # Extract the migration file name from output
            output = result.stdout
            import re
            match = re.search(r"Creating revision\s+['\"]?([^'\"]+)['\"]?", output)
            if match:
                version = match.group(1)
                logger.info(f"Migration created successfully: {version}")
            else:
                logger.info("Migration created successfully.")
            return True
        except Exception as e:
            logger.error(f"Error creating migration: {e}")
            return False

    def upgrade(self, revision: str = "head") -> bool:
        """
        Upgrade database to a specific revision.

        Args:
            revision: Target revision (default: 'head')

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._run_alembic_command("upgrade", revision)
            if result.returncode != 0:
                logger.error(f"Failed to upgrade database: {result.stderr}")
                return False
            logger.info(f"Database upgraded to {revision}.")
            return True
        except Exception as e:
            logger.error(f"Error upgrading database: {e}")
            return False

    def downgrade(self, revision: str = "-1") -> bool:
        """
        Downgrade database to a specific revision.

        Args:
            revision: Target revision (default: '-1')

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._run_alembic_command("downgrade", revision)
            if result.returncode != 0:
                logger.error(f"Failed to downgrade database: {result.stderr}")
                return False
            logger.info(f"Database downgraded to {revision}.")
            return True
        except Exception as e:
            logger.error(f"Error downgrading database: {e}")
            return False

    def current(self) -> Optional[str]:
        """Get the current database revision."""
        try:
            result = self._run_alembic_command("current")
            if result.returncode != 0:
                logger.error(f"Failed to get current revision: {result.stderr}")
                return None

            # Parse output to extract revision
            output = result.stdout.strip()
            if not output:
                return None

            import re
            match = re.search(r"([a-f0-9]+)", output)
            if match:
                return match.group(1)
            return output
        except Exception as e:
            logger.error(f"Error getting current revision: {e}")
            return None

    def history(self) -> List[Dict[str, str]]:
        """Get migration history."""
        try:
            result = self._run_alembic_command("history", "--verbose")
            if result.returncode != 0:
                logger.error(f"Failed to get history: {result.stderr}")
                return []

            history = []
            lines = result.stdout.strip().split("\n")
            current_revision = self.current()

            for line in lines:
                if line.startswith("Revision ID:"):
                    rev_id = line.split(":", 1)[1].strip()
                elif line.startswith("Rev:"):
                    rev_id = line.split(":", 1)[1].strip()
                elif line.startswith("Parents:"):
                    parents = line.split(":", 1)[1].strip()
                elif line.startswith("Message:"):
                    message = line.split(":", 1)[1].strip()
                elif line.startswith("Date:"):
                    date = line.split(":", 1)[1].strip()
                    history.append({
                        "id": rev_id,
                        "parents": parents,
                        "message": message,
                        "date": date,
                        "is_current": rev_id == current_revision,
                    })
                    rev_id = None

            return history
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []

    def status(self) -> Dict[str, Any]:
        """Get migration status."""
        current = self.current()
        history = self.history()

        return {
            "current_revision": current,
            "has_migrations": len(history) > 0,
            "migration_count": len(history),
            "is_head": current == "head" or (history and history[-1].get("id") == current),
        }


def run_migration() -> None:
    """CLI entry point for database migration management."""
    parser = argparse.ArgumentParser(
        description="Database migration management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s init                    # Initialize Alembic
  %(prog)s migrate -m "add users"  # Create a new migration
  %(prog)s upgrade                 # Upgrade to latest
  %(prog)s downgrade -1            # Downgrade one step
  %(prog)s status                  # Show migration status
  %(prog)s current                 # Show current revision
  %(prog)s history                 # Show migration history
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Init command
    subparsers.add_parser("init", help="Initialize Alembic migrations")

    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Create a new migration")
    migrate_parser.add_argument("-m", "--message", required=True, help="Migration message")
    migrate_parser.add_argument(
        "--no-autogenerate",
        action="store_true",
        help="Disable autogeneration",
    )

    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database")
    upgrade_parser.add_argument(
        "revision",
        nargs="?",
        default="head",
        help="Target revision (default: head)",
    )

    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database")
    downgrade_parser.add_argument(
        "revision",
        nargs="?",
        default="-1",
        help="Target revision (default: -1)",
    )

    # Status command
    subparsers.add_parser("status", help="Show migration status")

    # Current command
    subparsers.add_parser("current", help="Show current revision")

    # History command
    subparsers.add_parser("history", help="Show migration history")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = MigrationManager()

    if args.command == "init":
        success = manager.init()
        sys.exit(0 if success else 1)

    elif args.command == "migrate":
        success = manager.create_migration(
            message=args.message,
            autogenerate=not args.no_autogenerate,
        )
        sys.exit(0 if success else 1)

    elif args.command == "upgrade":
        success = manager.upgrade(args.revision)
        sys.exit(0 if success else 1)

    elif args.command == "downgrade":
        success = manager.downgrade(args.revision)
        sys.exit(0 if success else 1)

    elif args.command == "status":
        status = manager.status()
        print(f"Current revision: {status['current_revision'] or 'None'}")
        print(f"Has migrations: {status['has_migrations']}")
        print(f"Migration count: {status['migration_count']}")
        print(f"Is at head: {status['is_head']}")
        sys.exit(0)

    elif args.command == "current":
        current = manager.current()
        print(current or "No current revision")
        sys.exit(0)

    elif args.command == "history":
        history = manager.history()
        if not history:
            print("No migrations found.")
            sys.exit(0)

        print("Migration History:")
        for rev in history:
            indicator = " *" if rev.get("is_current") else "  "
            print(f"{indicator} {rev['id'][:8]} - {rev['message']} ({rev['date']})")
        sys.exit(0)


if __name__ == "__main__":
    run_migration()