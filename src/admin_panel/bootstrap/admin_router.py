# src/admin_panel/bootstrap/admin_router.py
from typing import Dict, Any, Optional, Callable, List, Union
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.main_menu import get_main_menu_keyboard

logger = get_logger(__name__)


class AdminRouter:
    """
    Router for admin panel callbacks and commands.

    Handles all admin-related callback queries and commands,
    including navigation, back/cancel actions, and module routing.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable] = {}
        self._back_callbacks: Dict[str, str] = {}
        self._module_handlers: Dict[str, Dict[str, Callable]] = {}

    async def handle_admin_callback(self, query: CallbackQuery) -> None:
        """
        Generic handler for admin callback queries.
        Routes callback data to the appropriate handler.
        """
        try:
            callback_data = query.data
            logger.debug(f"Admin callback received: {callback_data}")

            # Check if the callback is handled by a specific module
            for prefix, handler in self._handlers.items():
                if callback_data.startswith(prefix):
                    await handler(query)
                    return

            # If no specific handler, try to route based on the callback pattern
            await self._route_callback(query)

        except Exception as e:
            logger.error(f"Error handling admin callback {query.data}: {e}", exc_info=True)
            await query.answer("خطا در پردازش درخواست!", show_alert=True)

    async def _route_callback(self, query: CallbackQuery) -> None:
        """
        Route callback to appropriate module based on callback pattern.
        """
        data = query.data

        # Extract module and action from callback data
        # Format: admin_{module}_{action}:{params}
        parts = data.split(":")
        base_parts = parts[0].split("_")

        if len(base_parts) >= 3:
            module_name = base_parts[1]  # admin_users -> users
            action = "_".join(base_parts[2:]) if len(base_parts) > 2 else "index"

            # Try to find a handler for this module/action
            if module_name in self._module_handlers:
                module_handlers = self._module_handlers[module_name]
                # Check for exact action match
                if action in module_handlers:
                    await module_handlers[action](query)
                    return
                # Check for generic handler
                elif "default" in module_handlers:
                    await module_handlers["default"](query)
                    return

        # If no specific handler, show a generic response
        await query.answer("این بخش در حال توسعه است.", show_alert=True)

    async def handle_back_to_main(self, query: CallbackQuery) -> None:
        """Handle back to main menu request."""
        try:
            await query.message.edit_text(
                "🏠 **منوی اصلی**\n\n"
                "از منوی زیر یکی از گزینه‌ها را انتخاب کنید:",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown",
            )
            await query.answer()
        except Exception as e:
            logger.error(f"Error handling back to main: {e}", exc_info=True)
            await query.answer("خطا در بازگشت به منوی اصلی!", show_alert=True)

    async def handle_cancel(self, query: CallbackQuery) -> None:
        """Handle cancel request and go back to previous state."""
        try:
            # Get the previous callback or default to main menu
            previous_callback = self._back_callbacks.get(str(query.from_user.id), "admin_panel")
            await query.message.edit_text(
                "❌ عملیات لغو شد.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 بازگشت",
                                callback_data=previous_callback,
                            )
                        ]
                    ]
                ),
                parse_mode="Markdown",
            )
            await query.answer("لغو شد.")
        except Exception as e:
            logger.error(f"Error handling cancel: {e}", exc_info=True)
            await query.answer("خطا!", show_alert=True)

    async def handle_admin_command(self, message: Message) -> None:
        """Handle /admin command."""
        try:
            # Check if user is admin (permission check is done via middleware)
            await message.answer(
                "🔐 **پنل مدیریت**\n\n"
                "به پنل مدیریت خوش آمدید.\n"
                "برای دسترسی به گزینه‌ها، روی دکمه زیر کلیک کنید:",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⚙️ ورود به پنل مدیریت",
                                callback_data="admin_panel",
                            )
                        ]
                    ]
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Error handling admin command: {e}", exc_info=True)
            await message.answer("❌ خطا در نمایش پنل مدیریت. لطفاً دوباره تلاش کنید.")

    async def handle_admin_panel_callback(self, query: CallbackQuery) -> None:
        """Handle admin panel entry callback."""
        try:
            from admin_panel.ui.main_keyboard import get_admin_main_keyboard

            await query.message.edit_text(
                "🔐 **پنل مدیریت**\n\n"
                "یکی از گزینه‌های زیر را برای مدیریت انتخاب کنید:",
                reply_markup=get_admin_main_keyboard(),
                parse_mode="Markdown",
            )
            await query.answer()
        except Exception as e:
            logger.error(f"Error handling admin panel callback: {e}", exc_info=True)
            await query.answer("خطا در نمایش پنل مدیریت!", show_alert=True)

    def register_handler(self, prefix: str, handler: Callable) -> None:
        """
        Register a handler for a specific callback prefix.

        Args:
            prefix: Callback data prefix (e.g., 'admin_users_')
            handler: Async function that takes a CallbackQuery as argument
        """
        self._handlers[prefix] = handler
        logger.info(f"Registered handler for prefix: {prefix}")

    def register_module_handlers(
        self,
        module_name: str,
        handlers: Dict[str, Callable],
    ) -> None:
        """
        Register handlers for a specific module.

        Args:
            module_name: Name of the module (e.g., 'users')
            handlers: Dictionary mapping action names to handler functions
        """
        if module_name not in self._module_handlers:
            self._module_handlers[module_name] = {}
        self._module_handlers[module_name].update(handlers)
        logger.info(f"Registered {len(handlers)} handlers for module: {module_name}")

    def set_back_callback(self, user_id: int, callback_data: str) -> None:
        """
        Set the back callback for a user.

        Args:
            user_id: Telegram user ID
            callback_data: Callback data to go back to
        """
        self._back_callbacks[str(user_id)] = callback_data

    def get_back_callback(self, user_id: int) -> str:
        """
        Get the back callback for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            Callback data for back button, or default 'admin_panel'
        """
        return self._back_callbacks.get(str(user_id), "admin_panel")

    def clear_back_callback(self, user_id: int) -> None:
        """Clear the back callback for a user."""
        if str(user_id) in self._back_callbacks:
            del self._back_callbacks[str(user_id)]

    def get_handler(self, prefix: str) -> Optional[Callable]:
        """Get a registered handler by prefix."""
        return self._handlers.get(prefix)

    def get_module_handlers(self, module_name: str) -> Dict[str, Callable]:
        """Get all handlers for a specific module."""
        return self._module_handlers.get(module_name, {})

    def unregister_handler(self, prefix: str) -> bool:
        """
        Unregister a handler.

        Args:
            prefix: Callback data prefix

        Returns:
            True if handler was removed, False otherwise
        """
        if prefix in self._handlers:
            del self._handlers[prefix]
            logger.info(f"Unregistered handler for prefix: {prefix}")
            return True
        return False

    def unregister_module_handlers(self, module_name: str) -> bool:
        """
        Unregister all handlers for a module.

        Args:
            module_name: Name of the module

        Returns:
            True if handlers were removed, False otherwise
        """
        if module_name in self._module_handlers:
            del self._module_handlers[module_name]
            logger.info(f"Unregistered handlers for module: {module_name}")
            return True
        return False

    def clear_all_handlers(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()
        self._module_handlers.clear()
        self._back_callbacks.clear()
        logger.info("Cleared all admin router handlers.")

    def get_registered_prefixes(self) -> List[str]:
        """Get list of registered callback prefixes."""
        return list(self._handlers.keys())

    def get_registered_modules(self) -> List[str]:
        """Get list of registered modules."""
        return list(self._module_handlers.keys())

    async def handle_noop(self, query: CallbackQuery) -> None:
        """
        No-op handler for callbacks that don't need any action.
        Useful for pagination placeholders.
        """
        await query.answer()