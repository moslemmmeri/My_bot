# my_bot_project/src/my_bot/presentation/handlers/admin/__init__.py
"""
ماژول هندلرهای ادمین (Admin Handlers).

این ماژول شامل هندلرهای مربوط به پنل مدیریت است:
- AdminPanelEntryHandler: ورود به پنل مدیریت
- AdminCallbacksHandler: پردازش تمام کالبک‌های پنل مدیریت
"""

from my_bot.presentation.handlers.admin.admin_panel_entry import AdminPanelEntryHandler
from my_bot.presentation.handlers.admin.admin_callbacks import AdminCallbacksHandler

__all__ = [
    "AdminPanelEntryHandler",
    "AdminCallbacksHandler",
]