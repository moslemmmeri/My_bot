# src/admin_panel/bootstrap/admin_loader.py
"""
Admin Panel Loader

Responsible for initializing and loading all admin panel modules,
registering their handlers, and setting up the admin panel's routing
and middleware.
"""

from typing import Dict, Any, Optional, List, Type
from importlib import import_module
from pathlib import Path

from aiogram import Dispatcher, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from my_bot.core.logger import get_logger
from my_bot.core.config import Config
from my_bot.bootstrap.container import Container

from admin_panel.core.permissions import permission_checker
from admin_panel.bootstrap.module_register import ModuleRegister
from admin_panel.bootstrap.admin_router import AdminRouter

logger = get_logger(__name__)


class AdminLoader:
    """
    Loader for admin panel components.

    Responsible for:
    - Discovering and loading admin modules
    - Registering handlers with the dispatcher
    - Setting up admin-specific middlewares
    - Initializing the admin router
    """

    def __init__(
        self,
        bot: Bot,
        dispatcher: Dispatcher,
        container: Container,
        config: Config,
    ) -> None:
        self.bot = bot
        self.dispatcher = dispatcher
        self.container = container
        self.config = config
        self.module_register = ModuleRegister()
        self.admin_router = AdminRouter()
        self._loaded_modules: List[str] = []

    async def load_all(self) -> None:
        """
        Load all admin modules and register their handlers.
        This is the main entry point for admin panel initialization.
        """
        logger.info("Loading admin panel...")

        # 1. Discover modules
        modules = self._discover_modules()
        logger.info(f"Discovered admin modules: {modules}")

        # 2. Register each module
        for module_name in modules:
            await self._load_module(module_name)

        # 3. Register global admin middlewares
        await self._setup_middlewares()

        # 4. Register admin router handlers
        self._register_router_handlers()

        # 5. Register admin panel entry point
        self._register_admin_entry()

        logger.info(f"Admin panel loaded successfully. {len(self._loaded_modules)} modules loaded.")

    def _discover_modules(self) -> List[str]:
        """
        Discover all admin modules in the admin_panel/modules directory.
        Returns a list of module names (e.g., ['user_management', 'order_management']).
        """
        modules_dir = Path(__file__).parent.parent / "modules"
        if not modules_dir.exists():
            logger.warning(f"Admin modules directory not found: {modules_dir}")
            return []

        module_names = []
        for item in modules_dir.iterdir():
            if item.is_dir() and not item.name.startswith("__"):
                # Check if it has handlers.py or __init__.py
                if (item / "handlers").exists() or (item / "__init__.py").exists():
                    module_names.append(item.name)
        return sorted(module_names)

    async def _load_module(self, module_name: str) -> None:
        """
        Load a single admin module and register its handlers.
        """
        try:
            # Try to import the module's handlers package
            module_path = f"admin_panel.modules.{module_name}.handlers"
            try:
                handlers_module = import_module(module_path)
                # If the module has a register function, call it
                if hasattr(handlers_module, "register"):
                    await handlers_module.register(
                        dispatcher=self.dispatcher,
                        container=self.container,
                        admin_router=self.admin_router,
                    )
                    logger.info(f"Registered admin module: {module_name} (via register())")
                else:
                    # Otherwise, we assume all handlers are defined and we will register them
                    # by scanning for functions with specific decorators or naming conventions.
                    # For simplicity, we'll rely on the AdminRouter to register individual handlers.
                    # We can also let the AdminRouter discover them.
                    self.admin_router.register_module_handlers(module_name, handlers_module)
                    logger.info(f"Registered admin module: {module_name} (via router)")
            except ImportError as e:
                logger.warning(f"Could not import handlers for module {module_name}: {e}")
                # Try to import the module itself and use its handlers
                module_full = f"admin_panel.modules.{module_name}"
                mod = import_module(module_full)
                if hasattr(mod, "handlers") and callable(mod.handlers):
                    # If handlers is a function that returns a list of handlers
                    handlers = mod.handlers(self.container)
                    self._register_handlers(handlers)
                    logger.info(f"Registered admin module: {module_name} (via module.handlers)")
                else:
                    logger.warning(f"No handlers found for module {module_name}")

            self._loaded_modules.append(module_name)

        except Exception as e:
            logger.error(f"Error loading admin module {module_name}: {e}", exc_info=True)

    def _register_handlers(self, handlers: List[Dict[str, Any]]) -> None:
        """
        Register a list of handlers with the dispatcher.
        Each handler dict should contain:
        - 'type': 'message' or 'callback_query'
        - 'handler': callable
        - 'filters': optional list of filters
        - 'callback_data': optional pattern for callback queries
        """
        for handler_info in handlers:
            handler_type = handler_info.get("type")
            handler_func = handler_info.get("handler")
            if not handler_func:
                continue

            if handler_type == "callback_query":
                pattern = handler_info.get("callback_data")
                if pattern:
                    self.dispatcher.callback_query.register(
                        handler_func,
                        lambda c: c.data.startswith(pattern)
                    )
                else:
                    self.dispatcher.callback_query.register(handler_func)
            elif handler_type == "message":
                filters = handler_info.get("filters", [])
                if filters:
                    self.dispatcher.message.register(handler_func, *filters)
                else:
                    self.dispatcher.message.register(handler_func)
            else:
                logger.warning(f"Unknown handler type: {handler_type}")

    async def _setup_middlewares(self) -> None:
        """Set up admin-specific middlewares."""
        # Import middlewares
        from admin_panel.core.middlewares import AdminAuthMiddleware, AdminLoggingMiddleware

        # Register admin auth middleware
        self.dispatcher.callback_query.middleware(
            AdminAuthMiddleware(container=self.container)
        )
        self.dispatcher.message.middleware(
            AdminAuthMiddleware(container=self.container)
        )

        # Register admin logging middleware
        self.dispatcher.callback_query.middleware(
            AdminLoggingMiddleware()
        )
        self.dispatcher.message.middleware(
            AdminLoggingMiddleware()
        )

        logger.info("Admin middlewares installed.")

    def _register_router_handlers(self) -> None:
        """Register the admin router's generic handlers."""
        # Register the admin panel entry handler
        self.dispatcher.callback_query.register(
            self.admin_router.handle_admin_callback,
            lambda c: c.data.startswith("admin_")
        )

        # Register the back to main handler
        self.dispatcher.callback_query.register(
            self.admin_router.handle_back_to_main,
            lambda c: c.data == "back_to_main"
        )

        # Register the cancel handler
        self.dispatcher.callback_query.register(
            self.admin_router.handle_cancel,
            lambda c: c.data == "cancel"
        )

    def _register_admin_entry(self) -> None:
        """Register the command and callback to enter admin panel."""
        # Command: /admin
        self.dispatcher.message.register(
            self.admin_router.handle_admin_command,
            Command("admin")
        )

        # Callback: admin_panel (from main menu)
        self.dispatcher.callback_query.register(
            self.admin_router.handle_admin_panel_callback,
            lambda c: c.data == "admin_panel"
        )

    def get_loaded_modules(self) -> List[str]:
        """Return list of successfully loaded module names."""
        return self._loaded_modules.copy()