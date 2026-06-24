# my_bot_project/src/my_bot/application/services/ticket/__init__.py
"""
ماژول سرویس‌های تیکت پشتیبانی (Ticket Services).

این ماژول شامل سرویس‌های مربوط به مدیریت تیکت‌های پشتیبانی در سیستم است:
- TicketCreationService: ایجاد تیکت جدید
- TicketAssignmentService: تخصیص تیکت به اپراتور یا ادمین
- TicketResolutionService: حل و بستن تیکت‌ها
"""

from my_bot.application.services.ticket.ticket_creation import TicketCreationService
from my_bot.application.services.ticket.ticket_assignment import TicketAssignmentService
from my_bot.application.services.ticket.ticket_resolution import TicketResolutionService

__all__ = [
    "TicketCreationService",
    "TicketAssignmentService",
    "TicketResolutionService",
]