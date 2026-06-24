# my_bot_project/src/my_bot/bootstrap/app/startup_hooks.py
"""
Startup Hooks for the application.
...
"""

from typing import List, Callable, Awaitable
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)

class StartupHooks:
    def __init__(self):
        self._hooks: List[Callable[[], Awaitable[None]]] = []
        logger.info("StartupHooks initialized.")

    def register(self, hook: Callable[[], Awaitable[None]]) -> None:
        self._hooks.append(hook)
        logger.debug(f"Startup hook registered: {hook.__name__}")

    async def run_all(self) -> None:
        for hook in self._hooks:
            try:
                await hook()
                logger.debug(f"Startup hook executed: {hook.__name__}")
            except Exception as e:
                logger.error(f"Startup hook failed: {hook.__name__} - {e}")
                # Decide whether to raise or continue; we'll raise to fail fast
                raise