# src/scripts/__init__.py
"""
Scripts package for utility and maintenance scripts.

This package contains standalone scripts for:
- Database migrations
- Admin user creation
- Database backup
- Data seeding
- Other administrative tasks

These scripts are meant to be run directly, not imported as modules.
"""

__version__ = "1.0.0"

# Optionally expose helper functions for the scripts
from .db_migrate import run_migration
from .create_admin import create_admin_user
from .backup_db import backup_database
from .seed_data import seed_demo_data

__all__ = [
    "run_migration",
    "create_admin_user",
    "backup_database",
    "seed_demo_data",
]