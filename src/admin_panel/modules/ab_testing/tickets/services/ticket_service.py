# src/admin_panel/modules/tickets/services/ticket_service.py
from typing import Optional, List, Dict, Any
from datetime import datetime

from my_bot.core.exceptions import NotFoundError, DatabaseError, PermissionDeniedError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.ticket_repository import TicketRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.entities.ticket import Ticket, TicketReply, TicketStatus, TicketPriority

logger = get_logger(__name__)


class TicketService:
    """Service for managing support tickets in admin panel."""

    def __init__(
        self,
        ticket_repo: TicketRepository,
        user_repo: UserRepository,
    ) -> None:
        self.ticket_repo = ticket_repo
        self.user_repo = user_repo

    async def list_tickets(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated list of tickets with optional filters.
        Returns dict with 'items' (list of ticket dicts) and 'total'.
        """
        try:
            offset = (page - 1) * page_size
            tickets, total = await self.ticket_repo.find_filtered(
                status=status,
                priority=priority,
                assigned_to=assigned_to,
                user_id=user_id,
                limit=page_size,
                offset=offset,
            )
            items = []
            for ticket in tickets:
                user = await self.user_repo.find_by_id(ticket.user_id)
                items.append({
                    "id": ticket.id,
                    "title": ticket.title,
                    "body": ticket.body[:100] + "..." if len(ticket.body) > 100 else ticket.body,
                    "status": ticket.status.value if hasattr(ticket.status, 'value') else ticket.status,
                    "priority": ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority,
                    "user_id": ticket.user_id,
                    "user_name": user.username if user else "نامشخص",
                    "assigned_to": ticket.assigned_to,
                    "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                    "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
                })
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.error(f"Error listing tickets: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve tickets.") from e

    async def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Get a single ticket by ID with its replies."""
        try:
            ticket = await self.ticket_repo.find_by_id(ticket_id)
            if not ticket:
                return None

            user = await self.user_repo.find_by_id(ticket.user_id)
            assigned_user = None
            if ticket.assigned_to:
                assigned_user = await self.user_repo.find_by_id(ticket.assigned_to)

            # Get replies
            replies = await self.ticket_repo.get_replies(ticket_id)
            reply_list = []
            for reply in replies:
                reply_user = await self.user_repo.find_by_id(reply.user_id)
                reply_list.append({
                    "id": reply.id,
                    "user_id": reply.user_id,
                    "user_name": reply_user.username if reply_user else "نامشخص",
                    "text": reply.text,
                    "is_admin": reply.is_admin,
                    "created_at": reply.created_at.isoformat() if reply.created_at else None,
                })

            return {
                "id": ticket.id,
                "title": ticket.title,
                "body": ticket.body,
                "status": ticket.status.value if hasattr(ticket.status, 'value') else ticket.status,
                "priority": ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority,
                "user_id": ticket.user_id,
                "user_name": user.username if user else "نامشخص",
                "assigned_to": ticket.assigned_to,
                "assigned_to_name": assigned_user.username if assigned_user else None,
                "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
                "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
                "replies": reply_list,
            }
        except Exception as e:
            logger.error(f"Error getting ticket {ticket_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve ticket.") from e

    async def create_ticket(
        self,
        user_id: int,
        title: str,
        body: str,
        priority: str = "medium",
    ) -> Dict[str, Any]:
        """Create a new ticket (from user side)."""
        try:
            # Validate priority
            try:
                priority_enum = TicketPriority(priority)
            except ValueError:
                raise ValidationError(f"Invalid priority: {priority}")

            ticket = Ticket(
                user_id=user_id,
                title=title,
                body=body,
                status=TicketStatus.OPEN,
                priority=priority_enum,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            saved = await self.ticket_repo.save(ticket)
            logger.info(f"Ticket created: {saved.id} by user {user_id}")
            return {
                "id": saved.id,
                "title": saved.title,
                "body": saved.body,
                "status": saved.status.value,
                "priority": saved.priority.value,
                "user_id": saved.user_id,
                "created_at": saved.created_at.isoformat(),
            }
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating ticket: {e}", exc_info=True)
            raise DatabaseError("Failed to create ticket.") from e

    async def reply_to_ticket(
        self,
        ticket_id: int,
        user_id: int,
        text: str,
        is_admin: bool = True,
    ) -> Dict[str, Any]:
        """Add a reply to a ticket."""
        try:
            ticket = await self.ticket_repo.find_by_id(ticket_id)
            if not ticket:
                raise NotFoundError(f"Ticket {ticket_id} not found")

            # Check if ticket is closed
            if ticket.status == TicketStatus.CLOSED:
                raise ValidationError("Cannot reply to a closed ticket.")

            reply = TicketReply(
                ticket_id=ticket_id,
                user_id=user_id,
                text=text,
                is_admin=is_admin,
                created_at=datetime.now(),
            )
            await self.ticket_repo.add_reply(reply)

            # Update ticket status if it was open and admin replies
            if is_admin and ticket.status == TicketStatus.OPEN:
                ticket.status = TicketStatus.IN_PROGRESS
                ticket.updated_at = datetime.now()
                await self.ticket_repo.save(ticket)

            logger.info(f"Reply added to ticket {ticket_id} by {'admin' if is_admin else 'user'} {user_id}")
            return {
                "id": reply.id,
                "ticket_id": ticket_id,
                "user_id": user_id,
                "text": text,
                "is_admin": is_admin,
                "created_at": reply.created_at.isoformat(),
            }
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error adding reply to ticket {ticket_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to add reply.") from e

    async def close_ticket(self, ticket_id: int, closed_by: int) -> Dict[str, Any]:
        """Close a ticket."""
        try:
            ticket = await self.ticket_repo.find_by_id(ticket_id)
            if not ticket:
                raise NotFoundError(f"Ticket {ticket_id} not found")

            if ticket.status == TicketStatus.CLOSED:
                raise ValidationError("Ticket is already closed.")

            ticket.status = TicketStatus.CLOSED
            ticket.closed_at = datetime.now()
            ticket.updated_at = datetime.now()
            saved = await self.ticket_repo.save(ticket)

            logger.info(f"Ticket {ticket_id} closed by {closed_by}")
            return {
                "id": saved.id,
                "title": saved.title,
                "status": saved.status.value,
                "closed_at": saved.closed_at.isoformat(),
            }
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error closing ticket {ticket_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to close ticket.") from e

    async def assign_ticket(self, ticket_id: int, assignee_id: int, assigned_by: int) -> Dict[str, Any]:
        """Assign a ticket to an admin."""
        try:
            ticket = await self.ticket_repo.find_by_id(ticket_id)
            if not ticket:
                raise NotFoundError(f"Ticket {ticket_id} not found")

            # Check if assignee exists
            assignee = await self.user_repo.find_by_id(assignee_id)
            if not assignee:
                raise NotFoundError(f"User {assignee_id} not found")

            # Check if assignee is admin (optional: check role)
            # For simplicity, assume all users can be assigned, but in real app, check admin role

            ticket.assigned_to = assignee_id
            ticket.updated_at = datetime.now()
            if ticket.status == TicketStatus.OPEN:
                ticket.status = TicketStatus.IN_PROGRESS
            saved = await self.ticket_repo.save(ticket)

            logger.info(f"Ticket {ticket_id} assigned to {assignee_id} by {assigned_by}")
            return {
                "id": saved.id,
                "title": saved.title,
                "assigned_to": saved.assigned_to,
                "status": saved.status.value,
            }
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error assigning ticket {ticket_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to assign ticket.") from e

    async def get_ticket_stats(self) -> Dict[str, Any]:
        """Get statistics about tickets."""
        try:
            total = await self.ticket_repo.count()
            open_count = await self.ticket_repo.count_by_status("open")
            in_progress = await self.ticket_repo.count_by_status("in_progress")
            resolved = await self.ticket_repo.count_by_status("resolved")
            closed = await self.ticket_repo.count_by_status("closed")

            return {
                "total": total,
                "open": open_count,
                "in_progress": in_progress,
                "resolved": resolved,
                "closed": closed,
                "open_percentage": round((open_count / total * 100), 1) if total > 0 else 0,
            }
        except Exception as e:
            logger.error(f"Error getting ticket stats: {e}", exc_info=True)
            raise DatabaseError("Failed to get ticket statistics.") from e