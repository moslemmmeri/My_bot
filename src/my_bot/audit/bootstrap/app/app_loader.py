# my_bot_project/src/my_bot/bootstrap/app/app_loader.py
"""
بارگذاری و راه‌اندازی برنامه (App Loader).

این ماژول شامل کلاس `AppLoader` است که مسئولیت راه‌اندازی کامل برنامه،
ثبت هندلرها، میدلورها، راه‌اندازی ربات تلگرام و مدیریت چرخه‌ی حیات
برنامه را بر عهده دارد.
"""

import asyncio
import signal
from typing import Optional, List, Callable, Awaitable

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.fsm.storage.memory import MemoryStorage

from my_bot.core.config.app_config import AppConfig
from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.bootstrap.container.di_container import DIContainer
from my_bot.bootstrap.app.startup_hooks import StartupHooks
from my_bot.bootstrap.app.shutdown_hooks import ShutdownHooks
from my_bot.presentation.web_api.web_app import WebApp
from my_bot.presentation.web_api.routes.webhook import WebhookRouter
from my_bot.presentation.middlewares.rate_limiter import RateLimiterMiddleware
from my_bot.presentation.middlewares.logging_middleware import LoggingMiddleware
from my_bot.presentation.middlewares.i18n_middleware import I18nMiddleware
from my_bot.presentation.middlewares.feature_flag_middleware import FeatureFlagMiddleware
from my_bot.audit.audit_middleware import AuditMiddleware

logger = get_logger(__name__)


class AppLoader:
    """
    بارگذاری و راه‌اندازی برنامه.

    این کلاس با استفاده از ظرف DI، تمام وابستگی‌ها را دریافت کرده،
    ربات تلگرام را راه‌اندازی کرده و هندلرها و میدلورها را ثبت می‌کند.

    Attributes:
        config: پیکربندی اصلی برنامه.
        container: ظرف DI با تمام وابستگی‌ها.
        bot: نمونه ربات تلگرام.
        dispatcher: نمونه Dispatcher.
        web_app: نمونه وب‌سرویس (اختیاری).
        _startup_hooks: لیست توابع startup.
        _shutdown_hooks: لیست توابع shutdown.
        _is_running: وضعیت اجرای برنامه.
    """

    def __init__(
        self,
        config: AppConfig,
        container: DIContainer,
    ) -> None:
        """
        مقداردهی اولیه AppLoader.

        Args:
            config: پیکربندی اصلی برنامه.
            container: ظرف DI با تمام وابستگی‌ها.
        """
        self.config = config
        self.container = container
        self.bot: Optional[Bot] = None
        self.dispatcher: Optional[Dispatcher] = None
        self.web_app: Optional[WebApp] = None
        self._startup_hooks: List[Callable[[], Awaitable[None]]] = []
        self._shutdown_hooks: List[Callable[[], Awaitable[None]]] = []
        self._is_running = False

        logger.info("AppLoader initialized.")

    async def load(self) -> None:
        """
        بارگذاری کامل برنامه.

        این متد مراحل زیر را انجام می‌دهد:
        1. مقداردهی اولیه ظرف DI
        2. ایجاد نمونه ربات و دیسپچر
        3. ثبت میدلورها
        4. ثبت هندلرها
        5. تنظیم دستورات ربات
        6. راه‌اندازی وب‌سرویس (در صورت نیاز)
        7. اجرای هک‌های startup
        """
        logger.info("Loading application...")

        try:
            # 1. مقداردهی اولیه ظرف DI
            await self.container.initialize()

            # 2. ایجاد نمونه ربات و دیسپچر
            await self._create_bot_and_dispatcher()

            # 3. ثبت میدلورها
            await self._register_middlewares()

            # 4. ثبت هندلرها
            await self._register_handlers()

            # 5. تنظیم دستورات ربات
            await self._set_bot_commands()

            # 6. راه‌اندازی وب‌سرویس (در صورت نیاز)
            if self.config.enable_webhook:
                await self._setup_webhook()

            # 7. اجرای هک‌های startup
            await self._run_startup_hooks()

            self._is_running = True
            logger.info("Application loaded successfully.")

        except Exception as e:
            logger.error(f"Failed to load application: {e}")
            raise

    async def run(self) -> None:
        """
        اجرای برنامه با Long Polling.

        این متد برنامه را با استفاده از Long Polling اجرا می‌کند.
        اگر وب‌هوک فعال باشد، وب‌سرویس اجرا می‌شود.
        """
        if not self._is_running:
            await self.load()

        if self.config.enable_webhook:
            await self._run_webhook_mode()
        else:
            await self._run_long_polling_mode()

    async def _create_bot_and_dispatcher(self) -> None:
        """
        ایجاد نمونه ربات و دیسپچر.

        Raises:
            ValueError: اگر توکن ربات وجود نداشته باشد.
        """
        if not self.config.bot_token:
            raise ValueError("BOT_TOKEN is required but not set.")

        # ایجاد ربات
        self.bot = Bot(token=self.config.bot_token)

        # ایجاد دیسپچر با حافظه محلی
        storage = MemoryStorage()
        self.dispatcher = Dispatcher(storage=storage)

        # تنظیم shutdown handler
        self.dispatcher.shutdown.register(self._shutdown_handler)

        logger.info("Bot and Dispatcher created.")

    async def _register_middlewares(self) -> None:
        """
        ثبت میدلورها در دیسپچر.
        """
        if not self.dispatcher:
            raise RuntimeError("Dispatcher not initialized.")

        # Rate Limiter Middleware
        rate_limiter = self.container.resolve("rate_limiter_middleware")
        self.dispatcher.message.middleware(rate_limiter)
        self.dispatcher.callback_query.middleware(rate_limiter)

        # Logging Middleware
        logging_middleware = self.container.resolve("logging_middleware")
        self.dispatcher.message.middleware(logging_middleware)
        self.dispatcher.callback_query.middleware(logging_middleware)

        # I18n Middleware
        i18n_middleware = self.container.resolve("i18n_middleware")
        self.dispatcher.message.middleware(i18n_middleware)
        self.dispatcher.callback_query.middleware(i18n_middleware)

        # Feature Flag Middleware
        feature_flag_middleware = self.container.resolve("feature_flag_middleware")
        self.dispatcher.message.middleware(feature_flag_middleware)
        self.dispatcher.callback_query.middleware(feature_flag_middleware)

        # Audit Middleware
        audit_middleware = self.container.resolve("audit_middleware")
        self.dispatcher.message.middleware(audit_middleware)
        self.dispatcher.callback_query.middleware(audit_middleware)

        logger.info("Middlewares registered.")

    async def _register_handlers(self) -> None:
        """
        ثبت هندلرها در دیسپچر.
        """
        if not self.dispatcher:
            raise RuntimeError("Dispatcher not initialized.")

        # Start Handler
        start_handler = self.container.resolve("start_command_handler")
        self.dispatcher.message.register(
            start_handler.handle,
            lambda msg: msg.text and msg.text.startswith("/start"),
        )

        # Greeting Handler
        greeting_handler = self.container.resolve("greeting_handler")
        self.dispatcher.callback_query.register(
            greeting_handler.show_main_menu_by_callback,
            lambda c: c.data == "back_to_main",
        )
        self.dispatcher.message.register(
            greeting_handler.handle_help,
            lambda msg: msg.text == "❓ راهنما",
        )

        # Profile Handler
        profile_handler = self.container.resolve("profile_handler")
        self.dispatcher.callback_query.register(
            profile_handler.show_profile,
            lambda c: c.data == "profile",
        )
        self.dispatcher.callback_query.register(
            profile_handler.show_orders,
            lambda c: c.data == "orders",
        )
        self.dispatcher.callback_query.register(
            profile_handler.show_level_info,
            lambda c: c.data == "level_info",
        )
        self.dispatcher.callback_query.register(
            profile_handler.back_to_profile,
            lambda c: c.data == "profile",
        )

        # Order History Handler
        order_history_handler = self.container.resolve("order_history_handler")
        self.dispatcher.callback_query.register(
            order_history_handler.show_orders,
            lambda c: c.data.startswith("orders:page"),
        )
        self.dispatcher.callback_query.register(
            order_history_handler.show_order_detail,
            lambda c: c.data.startswith("order:detail:"),
        )
        self.dispatcher.callback_query.register(
            order_history_handler.filter_orders,
            lambda c: c.data == "orders:filter",
        )

        # Help Handler
        help_handler = self.container.resolve("help_handler")
        self.dispatcher.callback_query.register(
            help_handler.show_help,
            lambda c: c.data == "help",
        )
        self.dispatcher.callback_query.register(
            help_handler.show_full_guide,
            lambda c: c.data == "help:full_guide",
        )
        self.dispatcher.callback_query.register(
            help_handler.show_faq,
            lambda c: c.data == "help:faq",
        )
        self.dispatcher.callback_query.register(
            help_handler.show_contact,
            lambda c: c.data == "help:contact",
        )
        self.dispatcher.callback_query.register(
            help_handler.back_to_help,
            lambda c: c.data == "help:back",
        )

        # Form Handlers
        form_list_handler = self.container.resolve("form_list_handler")
        self.dispatcher.callback_query.register(
            form_list_handler.show_forms,
            lambda c: c.data == "forms_list",
        )
        self.dispatcher.callback_query.register(
            form_list_handler.select_form,
            lambda c: c.data.startswith("form:start:"),
        )

        form_start_handler = self.container.resolve("form_start_handler")
        self.dispatcher.callback_query.register(
            form_start_handler.start_form,
            lambda c: c.data.startswith("form:start:"),
        )
        self.dispatcher.callback_query.register(
            form_start_handler.cancel_form,
            lambda c: c.data == "form:cancel",
        )

        form_step_handler = self.container.resolve("form_step_handler")
        self.dispatcher.message.register(
            form_step_handler.handle_message,
            lambda msg: msg.text and not msg.text.startswith("/"),
        )
        self.dispatcher.callback_query.register(
            form_step_handler.handle_callback,
            lambda c: c.data.startswith("form:answer:") or
            c.data.startswith("form:multi_answer:") or
            c.data.startswith("form:multi_confirm:") or
            c.data in ["form:next", "form:previous", "form:cancel"],
        )

        form_submit_handler = self.container.resolve("form_submit_handler")
        self.dispatcher.callback_query.register(
            form_submit_handler.submit_form,
            lambda c: c.data == "form:submit",
        )
        self.dispatcher.callback_query.register(
            form_submit_handler.confirm_submission,
            lambda c: c.data == "form:confirm",
        )
        self.dispatcher.callback_query.register(
            form_submit_handler.edit_form,
            lambda c: c.data == "form:edit",
        )

        # Payment Handlers
        payment_initiate_handler = self.container.resolve("payment_initiate_handler")
        self.dispatcher.callback_query.register(
            payment_initiate_handler.initiate_payment,
            lambda c: c.data.startswith("payment:initiate:"),
        )
        self.dispatcher.callback_query.register(
            payment_initiate_handler.apply_coupon,
            lambda c: c.data == "payment:coupon",
        )
        self.dispatcher.message.register(
            payment_initiate_handler.handle_coupon_input,
            lambda msg: msg.text and msg.text.startswith("COUPON_"),
        )

        payment_callback_handler = self.container.resolve("payment_callback_handler")
        self.dispatcher.callback_query.register(
            payment_callback_handler.handle_callback,
            lambda c: c.data.startswith("payment:callback:"),
        )

        # Admin Handlers
        admin_panel_entry = self.container.resolve("admin_panel_entry_handler")
        self.dispatcher.callback_query.register(
            admin_panel_entry.enter_admin_panel,
            lambda c: c.data == "admin_panel",
        )
        self.dispatcher.callback_query.register(
            admin_panel_entry.exit_admin_panel,
            lambda c: c.data == "exit_admin",
        )

        admin_callbacks = self.container.resolve("admin_callbacks_handler")
        self.dispatcher.callback_query.register(
            admin_callbacks.handle_callback,
            lambda c: c.data.startswith("admin_"),
        )

        admin_commands = self.container.resolve("admin_commands_handler")
        self.dispatcher.message.register(
            admin_commands.admin_command,
            lambda msg: msg.text and msg.text.startswith("/admin"),
        )
        self.dispatcher.message.register(
            admin_commands.admin_users_command,
            lambda msg: msg.text and msg.text.startswith("/admin_users"),
        )
        self.dispatcher.message.register(
            admin_commands.admin_stats_command,
            lambda msg: msg.text and msg.text.startswith("/admin_stats"),
        )
        self.dispatcher.message.register(
            admin_commands.admin_broadcast_command,
            lambda msg: msg.text and msg.text.startswith("/admin_broadcast"),
        )
        self.dispatcher.message.register(
            admin_commands.admin_features_command,
            lambda msg: msg.text and msg.text.startswith("/admin_features"),
        )
        self.dispatcher.message.register(
            admin_commands.admin_help_command,
            lambda msg: msg.text and msg.text.startswith("/admin_help"),
        )

        # Broadcast Handlers (register from service if available)
        try:
            broadcast_handlers = self.container.resolve("broadcast_handlers")
            if broadcast_handlers:
                self.dispatcher.callback_query.register(
                    broadcast_handlers.show_broadcast_menu,
                    lambda c: c.data == "admin_broadcast",
                )
                self.dispatcher.message.register(
                    broadcast_handlers.handle_broadcast_input,
                    lambda msg: msg.text and not msg.text.startswith("/"),
                )
                self.dispatcher.callback_query.register(
                    broadcast_handlers.select_filter,
                    lambda c: c.data.startswith("broadcast:filter:"),
                )
                self.dispatcher.callback_query.register(
                    broadcast_handlers.send_broadcast,
                    lambda c: c.data == "broadcast:send",
                )
                self.dispatcher.callback_query.register(
                    broadcast_handlers.schedule_broadcast,
                    lambda c: c.data == "broadcast:schedule",
                )
        except KeyError:
            logger.warning("Broadcast handlers not found in container.")

        # Feature Management Handlers (Admin Panel Module)
        feature_handlers = self.container.resolve("feature_management_handlers")
        if feature_handlers:
            self.dispatcher.callback_query.register(
                feature_handlers.show_features,
                lambda c: c.data == "admin_features",
            )
            self.dispatcher.callback_query.register(
                feature_handlers.toggle_feature,
                lambda c: c.data.startswith("feature_toggle:"),
            )

        # Admin Panel Main Menu callbacks
        self.dispatcher.callback_query.register(
            self._handle_admin_menu_callbacks,
            lambda c: c.data.startswith("admin_") and c.data not in [
                "admin_panel",
                "admin_features",
                "admin_users",
                "admin_orders",
                "admin_analytics",
                "admin_broadcast",
                "admin_content",
                "admin_settings",
                "admin_logs",
                "admin_errors",
                "admin_coupons",
                "admin_tickets",
                "admin_backup",
                "admin_health",
                "admin_abtest",
                "admin_docs",
            ],
        )

        logger.info("Handlers registered.")

    async def _handle_admin_menu_callbacks(self, callback) -> None:
        """
        پردازش کالبک‌های منوی اصلی ادمین.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            # پیام‌های نمونه برای بخش‌های مختلف
            messages = {
                "admin_users": "👥 **مدیریت کاربران**\n\nاین بخش در حال توسعه است.",
                "admin_orders": "📦 **مدیریت سفارشات**\n\nاین بخش در حال توسعه است.",
                "admin_analytics": "📊 **آمار و تحلیل**\n\nاین بخش در حال توسعه است.",
                "admin_content": "📝 **مدیریت محتوا**\n\nاین بخش در حال توسعه است.",
                "admin_settings": "⚙️ **تنظیمات**\n\nاین بخش در حال توسعه است.",
                "admin_logs": "📑 **لاگ‌ها**\n\nاین بخش در حال توسعه است.",
                "admin_errors": "🚨 **خطاها**\n\nاین بخش در حال توسعه است.",
                "admin_coupons": "💳 **کوپن‌ها**\n\nاین بخش در حال توسعه است.",
                "admin_tickets": "🎫 **تیکت‌ها**\n\nاین بخش در حال توسعه است.",
                "admin_backup": "🔄 **پشتیبان**\n\nاین بخش در حال توسعه است.",
                "admin_health": "💚 **سلامت سیستم**\n\nاین بخش در حال توسعه است.",
                "admin_abtest": "📌 **A/B تست**\n\nاین بخش در حال توسعه است.",
                "admin_docs": "📖 **مستندات**\n\nاین بخش در حال توسعه است.",
            }

            text = messages.get(callback.data, "⚙️ **مدیریت**\n\nاین بخش در حال توسعه است.")
            from my_bot.presentation.keyboards.admin.admin_keyboards import get_admin_back_button

            await callback.message.edit_text(
                text=text,
                reply_markup=get_admin_back_button(),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error handling admin menu callback: {e}")
            await callback.answer("⚠️ خطا در پردازش درخواست.", show_alert=True)

    async def _set_bot_commands(self) -> None:
        """
        تنظیم دستورات ربات در منوی تلگرام.
        """
        if not self.bot:
            raise RuntimeError("Bot not initialized.")

        commands = [
            BotCommand(command="start", description="شروع و ثبت‌نام"),
            BotCommand(command="help", description="راهنمای کاربر"),
            BotCommand(command="admin", description="پنل مدیریت (فقط ادمین‌ها)"),
        ]

        # اضافه کردن دستورات ادمین برای کاربران عادی (فقط نمایش داده می‌شوند)
        if self.config.admin_ids:
            admin_commands = [
                BotCommand(command="admin_users", description="مدیریت کاربران"),
                BotCommand(command="admin_stats", description="آمار سیستم"),
                BotCommand(command="admin_broadcast", description="ارسال گروهی"),
                BotCommand(command="admin_features", description="مدیریت فیچرها"),
                BotCommand(command="admin_help", description="راهنمای ادمین"),
            ]
            commands.extend(admin_commands)

        await self.bot.set_my_commands(
            commands=commands,
            scope=BotCommandScopeDefault(),
        )

        logger.info("Bot commands set.")

    async def _setup_webhook(self) -> None:
        """
        راه‌اندازی وب‌هوک و وب‌سرویس.
        """
        if not self.bot:
            raise RuntimeError("Bot not initialized.")

        # ایجاد وب‌سرویس
        webhook_router = WebhookRouter(
            bot=self.bot,
            dispatcher=self.dispatcher,
            config=self.config,
        )

        # تنظیم وب‌هوک
        webhook_url = self.config.webhook_url or f"https://your-domain.com/webhook"
        await webhook_router.set_webhook(webhook_url)

        # ایجاد وب‌اپ
        self.web_app = WebApp(
            config=self.config,
            webhook_router=webhook_router,
        )

        # راه‌اندازی وب‌سرویس
        await self.web_app.start()

        logger.info(f"Webhook configured: {webhook_url}")

    async def _run_long_polling_mode(self) -> None:
        """
        اجرای برنامه با Long Polling.
        """
        if not self.bot or not self.dispatcher:
            raise RuntimeError("Bot and Dispatcher not initialized.")

        logger.info("Starting bot with Long Polling...")

        try:
            # حذف وب‌هوک (در صورت وجود)
            await self.bot.delete_webhook(drop_pending_updates=True)

            # شروع Long Polling
            await self.dispatcher.start_polling(
                self.bot,
                allowed_updates=["message", "callback_query"],
            )
        except asyncio.CancelledError:
            logger.info("Long Polling cancelled.")
        except Exception as e:
            logger.error(f"Error in Long Polling: {e}")
            raise
        finally:
            await self._shutdown()

    async def _run_webhook_mode(self) -> None:
        """
        اجرای برنامه با وب‌هوک.
        """
        if not self.web_app:
            raise RuntimeError("Web app not initialized.")

        logger.info("Starting bot with Webhook mode...")

        try:
            # وب‌سرویس در حال اجرا است
            await self.web_app.wait_for_shutdown()
        except asyncio.CancelledError:
            logger.info("Webhook mode cancelled.")
        except Exception as e:
            logger.error(f"Error in Webhook mode: {e}")
            raise
        finally:
            await self._shutdown()

    async def _run_startup_hooks(self) -> None:
        """
        اجرای هک‌های startup.
        """
        startup_hooks = self.container.resolve("startup_hooks")
        await startup_hooks.run_all()

    async def _shutdown_handler(self) -> None:
        """
        هندلر shutdown برای دیسپچر.
        """
        await self._shutdown()

    async def _shutdown(self) -> None:
        """
        خاموش‌سازی برنامه و آزادسازی منابع.
        """
        if not self._is_running:
            return

        logger.info("Shutting down application...")

        # اجرای هک‌های shutdown
        shutdown_hooks = self.container.resolve("shutdown_hooks")
        await shutdown_hooks.run_all()

        # بستن وب‌سرویس
        if self.web_app:
            await self.web_app.stop()

        # بستن ربات
        if self.bot:
            await self.bot.session.close()

        # خاموش‌سازی ظرف DI
        await self.container.shutdown()

        self._is_running = False
        logger.info("Application shut down successfully.")

    async def stop(self) -> None:
        """
        توقف برنامه.
        """
        await self._shutdown()

    def register_startup_hook(self, hook: Callable[[], Awaitable[None]]) -> None:
        """
        ثبت یک تابع startup.

        Args:
            hook: تابع async برای اجرا در startup.
        """
        self._startup_hooks.append(hook)
        logger.debug(f"Startup hook registered: {hook.__name__}")

    def register_shutdown_hook(self, hook: Callable[[], Awaitable[None]]) -> None:
        """
        ثبت یک تابع shutdown.

        Args:
            hook: تابع async برای اجرا در shutdown.
        """
        self._shutdown_hooks.append(hook)
        logger.debug(f"Shutdown hook registered: {hook.__name__}")