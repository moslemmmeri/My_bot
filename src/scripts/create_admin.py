# src/scripts/create_admin.py
#!/usr/bin/env python
"""
Create Admin User Script

This script creates an admin user in the system using the admin management
service. It can be run directly or imported as a module.

Usage:
    python -m src.scripts.create_admin --username admin --telegram-id 123456789 --role super_admin
    python -m src.scripts.create_admin --help
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from my_bot.core.logger import get_logger
from my_bot.core.config import Config
from my_bot.core.exceptions import ValidationError, NotFoundError
from my_bot.bootstrap.container import Container
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.admin_repository import AdminRepository
from my_bot.application.services.user.user_registration import UserRegistrationService
from admin_panel.modules.admin_management.services.admin_crud_service import AdminCRUDService

logger = get_logger(__name__)


class AdminCreator:
    """
    Service for creating admin users from command line.
    """

    def __init__(self) -> None:
        self.config = Config.from_env()
        self.container = Container(self.config)
        self.user_repo: UserRepository = self.container.user_repo
        self.admin_repo: AdminRepository = self.container.admin_repo
        self.admin_service = AdminCRUDService(
            admin_repo=self.admin_repo,
            user_repo=self.user_repo,
        )

    async def create_admin(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: str = "admin",
        is_active: bool = True,
    ) -> dict:
        """
        Create an admin user.

        Args:
            telegram_id: Telegram user ID
            username: Telegram username (optional)
            first_name: User's first name (optional)
            last_name: User's last name (optional)
            role: Admin role (super_admin, admin, moderator, support)
            is_active: Whether the admin is active

        Returns:
            dict: Created admin information

        Raises:
            ValidationError: If input validation fails
            NotFoundError: If user cannot be found
            DatabaseError: If database operation fails
        """
        # Check if user exists, create if not
        existing_user = await self.user_repo.find_by_telegram_id(telegram_id)
        if not existing_user:
            logger.info(f"User {telegram_id} not found. Creating new user...")
            user_registration = UserRegistrationService(
                user_repo=self.user_repo,
                cache=self.container.cache,
            )
            user = await user_registration.register_user(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            logger.info(f"User created: {user.id}")

        # Create admin
        try:
            admin = await self.admin_service.add_admin(
                user_id=telegram_id,
                role=role,
                added_by=None,  # System admin creation
            )
            logger.info(f"Admin created: {admin.get('id')} with role {role}")
            return admin
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating admin: {e}")
            raise

    async def list_admins(self) -> list:
        """List all admin users."""
        result = await self.admin_service.list_admins(page=1, page_size=100)
        return result.get("items", [])

    async def remove_admin(self, admin_id: int) -> bool:
        """Remove an admin by ID."""
        try:
            await self.admin_service.remove_admin(admin_id)
            logger.info(f"Admin {admin_id} removed.")
            return True
        except Exception as e:
            logger.error(f"Error removing admin {admin_id}: {e}")
            return False

    async def get_admin(self, admin_id: int) -> Optional[dict]:
        """Get admin by ID."""
        return await self.admin_service.get_admin(admin_id)

    async def get_admin_by_user_id(self, user_id: int) -> Optional[dict]:
        """Get admin by user ID."""
        return await self.admin_service.get_admin_by_user_id(user_id)

    def close(self) -> None:
        """Close resources."""
        asyncio.create_task(self.container.dispose())


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create admin user for the bot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --telegram-id 123456789 --username admin --role super_admin
  %(prog)s --telegram-id 987654321 --role admin
  %(prog)s --list
  %(prog)s --remove 1
        """
    )

    parser.add_argument(
        "-i", "--telegram-id",
        type=int,
        help="Telegram user ID of the user to make admin",
    )
    parser.add_argument(
        "-u", "--username",
        help="Username of the user (optional)",
    )
    parser.add_argument(
        "-f", "--first-name",
        help="First name of the user (optional)",
    )
    parser.add_argument(
        "-l", "--last-name",
        help="Last name of the user (optional)",
    )
    parser.add_argument(
        "-r", "--role",
        choices=["super_admin", "admin", "moderator", "support"],
        default="admin",
        help="Admin role (default: admin)",
    )
    parser.add_argument(
        "--inactive",
        action="store_true",
        help="Create admin as inactive",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all existing admins",
    )
    parser.add_argument(
        "--remove",
        type=int,
        metavar="ADMIN_ID",
        help="Remove admin by ID",
    )
    parser.add_argument(
        "--get",
        type=int,
        metavar="ADMIN_ID",
        help="Get admin by ID",
    )
    parser.add_argument(
        "--get-by-user",
        type=int,
        metavar="USER_ID",
        help="Get admin by user ID",
    )

    return parser.parse_args()


async def main_async() -> None:
    """Async main function."""
    args = parse_arguments()

    creator = AdminCreator()

    try:
        if args.list:
            admins = await creator.list_admins()
            if not admins:
                print("No admin users found.")
            else:
                print("Admin users:")
                for admin in admins:
                    status = "Active" if admin.get("is_active") else "Inactive"
                    print(
                        f"  ID: {admin.get('id')} | "
                        f"User ID: {admin.get('user_id')} | "
                        f"Role: {admin.get('role')} | "
                        f"Status: {status}"
                    )
            return

        if args.remove is not None:
            success = await creator.remove_admin(args.remove)
            if success:
                print(f"Admin {args.remove} removed successfully.")
            else:
                print(f"Failed to remove admin {args.remove}.")
            return

        if args.get is not None:
            admin = await creator.get_admin(args.get)
            if admin:
                print(f"Admin: {admin}")
            else:
                print(f"Admin {args.get} not found.")
            return

        if args.get_by_user is not None:
            admin = await creator.get_admin_by_user_id(args.get_by_user)
            if admin:
                print(f"Admin: {admin}")
            else:
                print(f"Admin for user {args.get_by_user} not found.")
            return

        if args.telegram_id is None:
            print("Error: --telegram-id is required for creating an admin.")
            print("Use --help for usage information.")
            return

        # Create admin
        admin = await creator.create_admin(
            telegram_id=args.telegram_id,
            username=args.username,
            first_name=args.first_name,
            last_name=args.last_name,
            role=args.role,
            is_active=not args.inactive,
        )

        print("\n✅ Admin created successfully!")
        print(f"  ID: {admin.get('id')}")
        print(f"  User ID: {admin.get('user_id')}")
        print(f"  Role: {admin.get('role')}")
        print(f"  Status: {'Active' if admin.get('is_active') else 'Inactive'}")
        if args.username:
            print(f"  Username: @{args.username}")
        print("\nYou can now use the admin panel in the bot.")

    except ValidationError as e:
        print(f"\n❌ Validation error: {e}")
    except NotFoundError as e:
        print(f"\n❌ User not found: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        creator.close()


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