# src/scripts/seed_data.py
#!/usr/bin/env python
"""
Database Seeding Script

This script populates the database with sample/test data for development
and testing purposes. It creates users, orders, feedback, coupons, and
other entities with realistic-looking data.

Usage:
    python -m src.scripts.seed_data [--count N] [--clear]
    python -m src.scripts.seed_data --help
"""

import os
import sys
import asyncio
import argparse
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from my_bot.core.logger import get_logger
from my_bot.core.config import Config
from my_bot.core.exceptions import DatabaseError, ValidationError
from my_bot.bootstrap.container import Container
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.coupon_repository import CouponRepository
from my_bot.domain.interfaces.repositories.feedback_repository import FeedbackRepository
from my_bot.domain.interfaces.repositories.content_repository import ContentRepository
from my_bot.domain.interfaces.repositories.ticket_repository import TicketRepository
from my_bot.domain.entities.user import User
from my_bot.domain.entities.order import Order
from my_bot.domain.entities.coupon import Coupon, CouponType, CouponStatus
from my_bot.domain.entities.feedback import Feedback, FeedbackStatus
from my_bot.domain.entities.content import Content
from my_bot.domain.entities.ticket import Ticket, TicketStatus, TicketPriority

logger = get_logger(__name__)


class DataSeeder:
    """
    Service for seeding the database with sample data.
    """

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config.from_env()
        self.container = Container(self.config)
        self.user_repo: UserRepository = self.container.user_repo
        self.order_repo: OrderRepository = self.container.order_repo
        self.coupon_repo: CouponRepository = self.container.coupon_repo
        self.feedback_repo: FeedbackRepository = self.container.feedback_repo
        self.content_repo: ContentRepository = self.container.content_repo
        self.ticket_repo: TicketRepository = self.container.ticket_repo

        # Sample data
        self.first_names = ["علی", "محمد", "مهدی", "رضا", "حسین", "احمد", "سعید", "مصطفی", "امیر", "پویا"]
        self.last_names = ["رضایی", "محمدی", "کریمی", "حسینی", "احمدی", "موسوی", "صفوی", "نوری", "شفیعی", "حیدری"]
        self.product_names = ["لپ‌تاپ", "موبایل", "هدفون", "کیبورد", "موس", "مانیتور", "پرینتر", "پاوربانک", "هارد اکسترنال", "تبلت"]
        self.roles = ["super_admin", "admin", "moderator", "support", "admin"]
        self.priorities = ["low", "medium", "high", "critical"]
        self.statuses = ["open", "in_progress", "resolved", "closed"]

    async def clear_all(self) -> None:
        """Clear all existing data from the database."""
        try:
            logger.warning("Clearing all data from database...")
            # Delete in reverse order of dependencies
            await self.ticket_repo.delete_all()
            await self.feedback_repo.delete_all()
            await self.coupon_repo.delete_all()
            await self.order_repo.delete_all()
            await self.content_repo.delete_all()
            await self.user_repo.delete_all()
            logger.info("All data cleared.")
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            raise DatabaseError("Failed to clear data.") from e

    async def seed_users(self, count: int = 20) -> List[Dict[str, Any]]:
        """Seed users with sample data."""
        users = []
        logger.info(f"Seeding {count} users...")

        # Create admin user first
        admin = await self.user_repo.save(
            User(
                telegram_id=random.randint(100000000, 999999999),
                username="admin",
                first_name="مدیر",
                last_name="سیستم",
                is_active=True,
                level="gold",
                points=1000,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        )
        users.append(admin)
        logger.info(f"Created admin user: {admin.id}")

        # Create regular users
        for i in range(count - 1):
            first = random.choice(self.first_names)
            last = random.choice(self.last_names)
            username = f"{first}_{last}_{i}" if random.random() > 0.3 else None
            user = await self.user_repo.save(
                User(
                    telegram_id=random.randint(100000000, 999999999),
                    username=username,
                    first_name=first,
                    last_name=last,
                    is_active=random.random() > 0.2,
                    level=random.choice(["gold", "silver", "bronze", "normal"]),
                    points=random.randint(0, 5000),
                    created_at=datetime.now() - timedelta(days=random.randint(0, 30)),
                    updated_at=datetime.now(),
                )
            )
            users.append(user)

        logger.info(f"Created {len(users)} users.")
        return [self._user_to_dict(u) for u in users]

    async def seed_orders(self, users: List[Dict[str, Any]], count: int = 50) -> List[Dict[str, Any]]:
        """Seed orders with sample data."""
        orders = []
        logger.info(f"Seeding {count} orders...")

        for i in range(count):
            user = random.choice(users)
            order = await self.order_repo.save(
                Order(
                    user_id=user["id"],
                    total_amount=random.randint(10000, 5000000),
                    status=random.choice(["pending", "paid", "shipped", "delivered", "cancelled", "failed"]),
                    items=[{"product": random.choice(self.product_names), "quantity": random.randint(1, 5)}],
                    created_at=datetime.now() - timedelta(days=random.randint(0, 15)),
                    updated_at=datetime.now(),
                )
            )
            orders.append(order)

        logger.info(f"Created {len(orders)} orders.")
        return [self._order_to_dict(o) for o in orders]

    async def seed_coupons(self, count: int = 10) -> List[Dict[str, Any]]:
        """Seed coupons with sample data."""
        coupons = []
        logger.info(f"Seeding {count} coupons...")

        codes = ["SUMMER", "WINTER", "SPRING", "AUTUMN", "WELCOME", "VIP", "SALE", "BLACK", "FRIDAY", "DISCOUNT"]

        for i in range(min(count, len(codes))):
            coupon = await self.coupon_repo.save(
                Coupon(
                    code=codes[i],
                    discount_type=random.choice([CouponType.PERCENTAGE, CouponType.FIXED]),
                    discount_value=random.randint(5, 50) if random.random() > 0.5 else random.randint(10000, 500000),
                    usage_limit=random.choice([None, 10, 20, 50, 100]),
                    used_count=random.randint(0, 5),
                    status=random.choice([CouponStatus.ACTIVE, CouponStatus.INACTIVE, CouponStatus.EXPIRED]),
                    expires_at=datetime.now().date() + timedelta(days=random.randint(0, 90)),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            )
            coupons.append(coupon)

        logger.info(f"Created {len(coupons)} coupons.")
        return [self._coupon_to_dict(c) for c in coupons]

    async def seed_feedback(self, users: List[Dict[str, Any]], count: int = 30) -> List[Dict[str, Any]]:
        """Seed feedback with sample data."""
        feedbacks = []
        logger.info(f"Seeding {count} feedback entries...")

        messages = [
            "عالی بود! خیلی راضی هستم.",
            "کاش زودتر می‌آمدم!",
            "خیلی خوب بود، پیشنهاد می‌کنم.",
            "می‌توانست بهتر باشد.",
            "خوب بود اما جا برای بهبود دارد.",
            "انتظار بیشتری داشتم.",
            "فوق‌العاده! حتماً باز هم استفاده می‌کنم.",
            "بد نبود ولی گرونه!",
            "خدمات عالی، پشتیبانی خوب.",
            "خیلی راضی بودم از کیفیت.",
        ]

        for i in range(count):
            user = random.choice(users)
            feedback = await self.feedback_repo.save(
                Feedback(
                    user_id=user["id"],
                    rating=random.randint(1, 5),
                    message=random.choice(messages),
                    status=random.choice([FeedbackStatus.PENDING, FeedbackStatus.REPLIED, FeedbackStatus.RESOLVED]),
                    reply=random.choice([None, "ممنون از بازخورد شما! در حال بررسی هستیم."]) if random.random() > 0.5 else None,
                    created_at=datetime.now() - timedelta(days=random.randint(0, 10)),
                    updated_at=datetime.now(),
                )
            )
            feedbacks.append(feedback)

        logger.info(f"Created {len(feedbacks)} feedback entries.")
        return [self._feedback_to_dict(f) for f in feedbacks]

    async def seed_content(self, count: int = 15) -> List[Dict[str, Any]]:
        """Seed content with sample data."""
        contents = []
        logger.info(f"Seeding {count} content items...")

        titles = [
            "معرفی محصول جدید",
            "راهنمای استفاده از ربات",
            "اخبار جدید",
            "سوالات متداول",
            "درباره ما",
            "تماس با ما",
            "قوانین و مقررات",
            "حریم خصوصی",
            "کمک و پشتیبانی",
            "آموزش‌های ویدیویی",
        ]
        types = ["article", "news", "page", "landing"]
        bodies = [
            "این یک متن نمونه برای نمایش محتوا است...",
            "توضیحات کامل درباره این موضوع...",
            "اطلاعات بیشتر در این بخش...",
            "راهنمای جامع برای کاربران...",
            "هر آنچه باید بدانید در این مقاله...",
        ]

        for i in range(count):
            content = await self.content_repo.save(
                Content(
                    title=random.choice(titles) + f" {i+1}",
                    body=random.choice(bodies) * random.randint(1, 3),
                    type=random.choice(types),
                    status=random.choice(["draft", "published", "archived"]),
                    created_at=datetime.now() - timedelta(days=random.randint(0, 20)),
                    updated_at=datetime.now(),
                )
            )
            contents.append(content)

        logger.info(f"Created {len(contents)} content items.")
        return [self._content_to_dict(c) for c in contents]

    async def seed_tickets(self, users: List[Dict[str, Any]], count: int = 25) -> List[Dict[str, Any]]:
        """Seed tickets with sample data."""
        tickets = []
        logger.info(f"Seeding {count} tickets...")

        subjects = [
            "مشکل در پرداخت",
            "سوال درباره محصول",
            "درخواست بازگشت کالا",
            "مشکل فنی در ربات",
            "سوال درباره تخفیف",
            "درخواست پشتیبانی",
            "گزارش خطا",
            "پیشنهاد برای بهبود",
        ]
        bodies = [
            "سلام، من مشکل دارم در پرداخت...",
            "چطور می‌توانم محصول را برگردانم؟",
            "ربات من کار نمی‌کند، لطفاً کمک کنید.",
            "آیا تخفیف ویژه برای کاربران جدید دارید؟",
            "پیشنهاد می‌کنم قابلیت جدیدی اضافه شود...",
        ]

        for i in range(count):
            user = random.choice(users)
            ticket = await self.ticket_repo.save(
                Ticket(
                    user_id=user["id"],
                    title=random.choice(subjects),
                    body=random.choice(bodies),
                    status=random.choice([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED]),
                    priority=random.choice([TicketPriority.LOW, TicketPriority.MEDIUM, TicketPriority.HIGH, TicketPriority.CRITICAL]),
                    assigned_to=random.choice([None, random.choice(users)["id"]]) if random.random() > 0.4 else None,
                    created_at=datetime.now() - timedelta(days=random.randint(0, 10)),
                    updated_at=datetime.now(),
                )
            )
            tickets.append(ticket)

        logger.info(f"Created {len(tickets)} tickets.")
        return [self._ticket_to_dict(t) for t in tickets]

    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        return {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "level": user.level,
            "points": user.points,
        }

    def _order_to_dict(self, order: Order) -> Dict[str, Any]:
        return {
            "id": order.id,
            "user_id": order.user_id,
            "total_amount": order.total_amount,
            "status": order.status,
            "items": order.items,
        }

    def _coupon_to_dict(self, coupon: Coupon) -> Dict[str, Any]:
        return {
            "id": coupon.id,
            "code": coupon.code,
            "discount_type": coupon.discount_type.value if hasattr(coupon.discount_type, 'value') else coupon.discount_type,
            "discount_value": coupon.discount_value,
            "usage_limit": coupon.usage_limit,
            "used_count": coupon.used_count,
            "status": coupon.status.value if hasattr(coupon.status, 'value') else coupon.status,
            "expires_at": coupon.expires_at.isoformat() if coupon.expires_at else None,
        }

    def _feedback_to_dict(self, feedback: Feedback) -> Dict[str, Any]:
        return {
            "id": feedback.id,
            "user_id": feedback.user_id,
            "rating": feedback.rating,
            "message": feedback.message,
            "status": feedback.status.value if hasattr(feedback.status, 'value') else feedback.status,
            "reply": feedback.reply,
        }

    def _content_to_dict(self, content: Content) -> Dict[str, Any]:
        return {
            "id": content.id,
            "title": content.title,
            "body": content.body,
            "type": content.type,
            "status": content.status,
        }

    def _ticket_to_dict(self, ticket: Ticket) -> Dict[str, Any]:
        return {
            "id": ticket.id,
            "user_id": ticket.user_id,
            "title": ticket.title,
            "body": ticket.body,
            "status": ticket.status.value if hasattr(ticket.status, 'value') else ticket.status,
            "priority": ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority,
            "assigned_to": ticket.assigned_to,
        }

    async def run(
        self,
        count: int = 20,
        clear: bool = False,
        seed_users_count: int = 20,
        seed_orders_count: int = 50,
        seed_coupons_count: int = 10,
        seed_feedback_count: int = 30,
        seed_content_count: int = 15,
        seed_tickets_count: int = 25,
    ) -> Dict[str, Any]:
        """Run the complete seeding process."""
        results = {
            "users": [],
            "orders": [],
            "coupons": [],
            "feedback": [],
            "content": [],
            "tickets": [],
        }

        try:
            if clear:
                await self.clear_all()

            # Seed in order of dependencies
            users = await self.seed_users(seed_users_count)
            results["users"] = users

            orders = await self.seed_orders(users, seed_orders_count)
            results["orders"] = orders

            coupons = await self.seed_coupons(seed_coupons_count)
            results["coupons"] = coupons

            feedback = await self.seed_feedback(users, seed_feedback_count)
            results["feedback"] = feedback

            content = await self.seed_content(seed_content_count)
            results["content"] = content

            tickets = await self.seed_tickets(users, seed_tickets_count)
            results["tickets"] = tickets

            logger.info("Seeding completed successfully!")
            return results

        except Exception as e:
            logger.error(f"Seeding failed: {e}", exc_info=True)
            raise DatabaseError(f"Failed to seed data: {e}") from e

    def close(self) -> None:
        """Close resources."""
        asyncio.create_task(self.container.dispose())


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed the database with sample data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Seed with default counts
  %(prog)s --count 50               # Seed more data
  %(prog)s --clear                  # Clear existing data first
  %(prog)s --users 30 --orders 100  # Custom counts
        """
    )

    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Base count for seeding (default: 20)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before seeding",
    )
    parser.add_argument(
        "--users",
        type=int,
        help="Number of users to create (default: 20)",
    )
    parser.add_argument(
        "--orders",
        type=int,
        help="Number of orders to create (default: 50)",
    )
    parser.add_argument(
        "--coupons",
        type=int,
        help="Number of coupons to create (default: 10)",
    )
    parser.add_argument(
        "--feedback",
        type=int,
        help="Number of feedback entries to create (default: 30)",
    )
    parser.add_argument(
        "--content",
        type=int,
        help="Number of content items to create (default: 15)",
    )
    parser.add_argument(
        "--tickets",
        type=int,
        help="Number of tickets to create (default: 25)",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompt",
    )

    return parser.parse_args()


async def main_async() -> None:
    """Async main function."""
    args = parse_arguments()

    # Set counts with defaults
    seed_users = args.users or max(20, args.count)
    seed_orders = args.orders or max(50, args.count * 2)
    seed_coupons = args.coupons or max(10, args.count // 2)
    seed_feedback = args.feedback or max(30, args.count + 10)
    seed_content = args.content or max(15, args.count)
    seed_tickets = args.tickets or max(25, args.count + 5)

    print("\n📊 Data Seeding Configuration:")
    print(f"  Users: {seed_users}")
    print(f"  Orders: {seed_orders}")
    print(f"  Coupons: {seed_coupons}")
    print(f"  Feedback: {seed_feedback}")
    print(f"  Content: {seed_content}")
    print(f"  Tickets: {seed_tickets}")
    print(f"  Clear existing data: {'Yes' if args.clear else 'No'}")

    if not args.no_confirm:
        confirm = input("\nProceed with seeding? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Seeding cancelled.")
            return

    seeder = DataSeeder()

    try:
        print("\n⏳ Seeding data...")
        results = await seeder.run(
            count=args.count,
            clear=args.clear,
            seed_users_count=seed_users,
            seed_orders_count=seed_orders,
            seed_coupons_count=seed_coupons,
            seed_feedback_count=seed_feedback,
            seed_content_count=seed_content,
            seed_tickets_count=seed_tickets,
        )

        print("\n✅ Data seeding completed successfully!")
        print(f"  Users created: {len(results['users'])}")
        print(f"  Orders created: {len(results['orders'])}")
        print(f"  Coupons created: {len(results['coupons'])}")
        print(f"  Feedback entries created: {len(results['feedback'])}")
        print(f"  Content items created: {len(results['content'])}")
        print(f"  Tickets created: {len(results['tickets'])}")

    except DatabaseError as e:
        print(f"\n❌ Database error: {e}")
        logger.error(f"Database error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        seeder.close()


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