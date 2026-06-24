# my_bot_project/src/my_bot/bootstrap/container/di_container.py
"""
ظرف DI (Dependency Injection Container).

این کلاس به‌عنوان مرکز مدیریت وابستگی‌های سیستم عمل می‌کند.
با استفاده از این ظرف، می‌توان سرویس‌ها، ریپازیتوری‌ها و سایر
وابستگی‌ها را ثبت و دریافت کرد.

ویژگی‌ها:
- ثبت سرویس‌ها به‌صورت Singleton یا Factory
- مدیریت چرخه‌ی حیات وابستگی‌ها
- پشتیبانی از وابستگی‌های تزریقی (Constructor Injection)
- راه‌اندازی اولیه (Initialize) برای اتصالات دیتابیس و کش
"""

from typing import Dict, Any, Type, TypeVar, Optional, Callable, cast
from functools import lru_cache

from my_bot.core.config.app_config import AppConfig
from my_bot.core.config.db_config import DBConfig
from my_bot.core.config.redis_config import RedisConfig
from my_bot.core.config.logging_config import LoggingConfig
from my_bot.core.config.rate_limit_config import RateLimitConfig
from my_bot.core.logger.logger_setup import setup_logger, get_logger
from my_bot.core.feature_flags.flag_manager import FeatureFlagManager
from my_bot.core.feature_flags.flag_repository import FlagRepository
from my_bot.core.feature_flags.flag_cache import FlagCache

from my_bot.infrastructure.database.session_manager import DatabaseSessionManager
from my_bot.infrastructure.database.connection_pool import ConnectionPool
from my_bot.infrastructure.cache.cache_manager import CacheManager
from my_bot.infrastructure.cache.redis_adapter import RedisAdapter
from my_bot.infrastructure.cache.local_adapter import LocalAdapter
from my_bot.infrastructure.cache.cache_fallback import CacheFallback
from my_bot.infrastructure.repositories.user_repo_impl import UserRepositoryImpl
from my_bot.infrastructure.repositories.order_repo_impl import OrderRepositoryImpl
from my_bot.infrastructure.repositories.payment_repo_impl import PaymentRepositoryImpl
from my_bot.infrastructure.repositories.coupon_repo_impl import CouponRepositoryImpl
from my_bot.infrastructure.repositories.form_repo_impl import FormRepositoryImpl
from my_bot.infrastructure.repositories.ticket_repo_impl import TicketRepositoryImpl
from my_bot.infrastructure.repositories.audit_repo_impl import AuditRepositoryImpl
from my_bot.infrastructure.external.payment.zarinpal import ZarinpalGateway
from my_bot.infrastructure.external.payment.mock_gateway import MockPaymentGateway
from my_bot.infrastructure.external.email.smtp_sender import SMTPSender
from my_bot.infrastructure.external.sms.kavenegar import KavenegarSMS
from my_bot.infrastructure.health_check.health_checker import HealthChecker

from my_bot.application.services.user.user_registration import UserRegistrationService
from my_bot.application.services.user.user_profile import UserProfileService
from my_bot.application.services.user.user_level_upgrade import UserLevelUpgradeService
from my_bot.application.services.order.order_creation import OrderCreationService
from my_bot.application.services.order.order_status_update import OrderStatusUpdateService
from my_bot.application.services.order.order_history import OrderHistoryService
from my_bot.application.services.payment.payment_gateway import PaymentGatewayService
from my_bot.application.services.payment.payment_verification import PaymentVerificationService
from my_bot.application.services.payment.payment_webhook import PaymentWebhookService
from my_bot.application.services.form.form_builder import FormBuilderService
from my_bot.application.services.form.form_submission import FormSubmissionService
from my_bot.application.services.form.form_analytics import FormAnalyticsService
from my_bot.application.services.broadcast.broadcast_sender import BroadcastSenderService
from my_bot.application.services.broadcast.broadcast_filter import BroadcastFilterService
from my_bot.application.services.broadcast.broadcast_scheduler import BroadcastSchedulerService
from my_bot.application.services.ticket.ticket_creation import TicketCreationService
from my_bot.application.services.ticket.ticket_assignment import TicketAssignmentService
from my_bot.application.services.ticket.ticket_resolution import TicketResolutionService
from my_bot.application.services.coupon.coupon_generation import CouponGenerationService
from my_bot.application.services.coupon.coupon_validation import CouponValidationService
from my_bot.application.services.analytics.user_behavior import UserBehaviorAnalyticsService
from my_bot.application.services.analytics.order_statistics import OrderStatisticsService
from my_bot.application.services.analytics.ab_testing import ABTestingService

from my_bot.application.use_cases.user.register_user import RegisterUserUseCase
from my_bot.application.use_cases.user.update_profile import UpdateProfileUseCase
from my_bot.application.use_cases.order.create_order import CreateOrderUseCase
from my_bot.application.use_cases.order.cancel_order import CancelOrderUseCase
from my_bot.application.use_cases.payment.initiate_payment import InitiatePaymentUseCase
from my_bot.application.use_cases.payment.confirm_payment import ConfirmPaymentUseCase

from my_bot.presentation.handlers.start.start_command import StartCommandHandler
from my_bot.presentation.handlers.start.greeting import GreetingHandler
from my_bot.presentation.handlers.user.profile_handler import ProfileHandler
from my_bot.presentation.handlers.user.order_history_handler import OrderHistoryHandler
from my_bot.presentation.handlers.user.help_handler import HelpHandler
from my_bot.presentation.handlers.form.form_list_handler import FormListHandler
from my_bot.presentation.handlers.form.form_start_handler import FormStartHandler
from my_bot.presentation.handlers.form.form_step_handler import FormStepHandler
from my_bot.presentation.handlers.form.form_submit_handler import FormSubmitHandler
from my_bot.presentation.handlers.payment.payment_initiate_handler import PaymentInitiateHandler
from my_bot.presentation.handlers.payment.payment_callback_handler import PaymentCallbackHandler
from my_bot.presentation.handlers.payment.coupon_apply_handler import CouponApplyHandler
from my_bot.presentation.handlers.admin.admin_panel_entry import AdminPanelEntryHandler
from my_bot.presentation.handlers.admin.admin_callbacks import AdminCallbacksHandler
from my_bot.presentation.handlers.admin.admin_commands import AdminCommandsHandler
from my_bot.presentation.middlewares.rate_limiter import RateLimiterMiddleware
from my_bot.presentation.middlewares.logging_middleware import LoggingMiddleware
from my_bot.presentation.middlewares.i18n_middleware import I18nMiddleware
from my_bot.presentation.middlewares.feature_flag_middleware import FeatureFlagMiddleware

from my_bot.audit.audit_logger import AuditLogger
from my_bot.audit.audit_middleware import AuditMiddleware

from my_bot.bootstrap.app.startup_hooks import StartupHooks
from my_bot.bootstrap.app.shutdown_hooks import ShutdownHooks

from admin_panel.modules.feature_management.handlers import FeatureManagementHandlers

logger = get_logger(__name__)

T = TypeVar("T")


class DIContainer:
    """
    ظرف Dependency Injection.

    این کلاس با استفاده از یک رجیستری داخلی، وابستگی‌ها را مدیریت می‌کند.
    امکان ثبت سرویس‌ها به‌صورت Singleton یا Factory فراهم است.

    Attributes:
        _registry: دیکشنری نگاشت نام سرویس به مقدار (یا factory)
        _singletons: دیکشنری نگاشت نام سرویس به نمونه singleton
    """

    def __init__(self) -> None:
        """
        مقداردهی اولیه ظرف DI.
        """
        self._registry: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._initialized = False

        logger.info("DIContainer initialized.")

    def register(
        self,
        name: str,
        instance_or_factory: Any,
        is_singleton: bool = True,
    ) -> None:
        """
        ثبت یک سرویس در ظرف.

        Args:
            name: نام سرویس (برای شناسایی).
            instance_or_factory: نمونه یا تابع تولیدکننده.
            is_singleton: آیا به‌صورت Singleton باشد.
        """
        self._registry[name] = {
            "value": instance_or_factory,
            "singleton": is_singleton,
        }
        logger.debug(f"Service registered: {name} (singleton={is_singleton})")

    def register_factory(self, name: str, factory: Callable) -> None:
        """
        ثبت یک Factory برای سرویس.

        Args:
            name: نام سرویس.
            factory: تابعی که نمونه‌ی سرویس را ایجاد می‌کند.
        """
        self.register(name, factory, is_singleton=False)

    def register_singleton(self, name: str, instance: Any) -> None:
        """
        ثبت یک نمونه Singleton.

        Args:
            name: نام سرویس.
            instance: نمونه‌ی سرویس.
        """
        self.register(name, instance, is_singleton=True)

    def resolve(self, name: str) -> Any:
        """
        دریافت یک سرویس از ظرف.

        Args:
            name: نام سرویس.

        Returns:
            نمونه‌ی سرویس.

        Raises:
            KeyError: اگر سرویس ثبت نشده باشد.
        """
        if name not in self._registry:
            raise KeyError(f"Service '{name}' not registered.")

        entry = self._registry[name]
        is_singleton = entry["singleton"]
        value = entry["value"]

        # اگر Singleton باشد و قبلاً ساخته شده، نمونه را برگردان
        if is_singleton and name in self._singletons:
            return self._singletons[name]

        # اگر مقدار یک تابع باشد (Factory)، آن را صدا بزن
        if callable(value) and not isinstance(value, type):
            instance = value()
        else:
            instance = value

        # اگر Singleton است، ذخیره کن
        if is_singleton:
            self._singletons[name] = instance

        return instance

    def has(self, name: str) -> bool:
        """
        بررسی وجود یک سرویس در ظرف.

        Args:
            name: نام سرویس.

        Returns:
            True اگر سرویس ثبت شده باشد.
        """
        return name in self._registry

    async def initialize(self) -> None:
        """
        مقداردهی اولیه سرویس‌های نیازمند راه‌اندازی.
        """
        if self._initialized:
            logger.warning("DIContainer already initialized.")
            return

        logger.info("Initializing DIContainer...")

        # راه‌اندازی DatabaseSessionManager
        db_manager = self.resolve("database_session_manager")
        await db_manager.initialize()

        # راه‌اندازی CacheManager
        cache_manager = self.resolve("cache_manager")
        await cache_manager.initialize()

        # راه‌اندازی FeatureFlagManager
        flag_manager = self.resolve("feature_flag_manager")
        await flag_manager.initialize()

        self._initialized = True
        logger.info("DIContainer initialized successfully.")

    async def shutdown(self) -> None:
        """
        خاموش‌سازی و آزادسازی منابع.
        """
        logger.info("Shutting down DIContainer...")

        # بستن اتصالات دیتابیس
        db_manager = self.resolve("database_session_manager")
        await db_manager.close()

        # بستن کش
        cache_manager = self.resolve("cache_manager")
        await cache_manager.close()

        self._initialized = False
        logger.info("DIContainer shut down successfully.")


# ==============================================
# تابع ساخت ظرف با تمام وابستگی‌ها
# ==============================================

def build_container(
    app_config: AppConfig,
    db_config: DBConfig,
    redis_config: RedisConfig,
    rate_limit_config: RateLimitConfig,
    logging_config: LoggingConfig,
) -> DIContainer:
    """
    ساخت ظرف DI با تمام وابستگی‌های ثبت‌شده.

    Args:
        app_config: پیکربندی اصلی برنامه.
        db_config: پیکربندی دیتابیس.
        redis_config: پیکربندی Redis.
        rate_limit_config: پیکربندی محدودیت نرخ.
        logging_config: پیکربندی لاگ‌گیری.

    Returns:
        DIContainer: ظرف پیکربندی‌شده.
    """
    container = DIContainer()

    # ==========================================
    # ثبت Configها
    # ==========================================
    container.register_singleton("app_config", app_config)
    container.register_singleton("db_config", db_config)
    container.register_singleton("redis_config", redis_config)
    container.register_singleton("rate_limit_config", rate_limit_config)
    container.register_singleton("logging_config", logging_config)

    # ==========================================
    # ثبت Logger
    # ==========================================
    container.register_factory(
        "logger",
        lambda: setup_logger("my_bot", logging_config),
    )

    # ==========================================
    # ثبت دیتابیس و کش
    # ==========================================
    container.register_singleton(
        "database_session_manager",
        DatabaseSessionManager(db_config),
    )
    container.register_singleton(
        "connection_pool",
        ConnectionPool(db_config),
    )

    # Redis Adapter (در صورت وجود Redis)
    if redis_config.url:
        redis_adapter = RedisAdapter(redis_config)
        container.register_singleton("redis_adapter", redis_adapter)
    else:
        container.register_singleton("redis_adapter", None)

    # Local Adapter
    local_adapter = LocalAdapter()
    container.register_singleton("local_adapter", local_adapter)

    # Cache Manager
    if redis_config.url:
        # از Redis + Local Fallback استفاده می‌کنیم
        cache_fallback = CacheFallback(
            primary=redis_adapter,
            fallback=local_adapter,
            fallback_enabled=True,
        )
        cache_manager = CacheManager(
            redis_adapter=redis_adapter,
            local_adapter=local_adapter,
            fallback_enabled=True,
        )
    else:
        # فقط Local Cache
        cache_manager = CacheManager(
            redis_adapter=None,
            local_adapter=local_adapter,
            fallback_enabled=False,
        )
    container.register_singleton("cache_manager", cache_manager)

    # ==========================================
    # ثبت Feature Flag
    # ==========================================
    flag_repository = FlagRepository(
        session_factory=lambda: container.resolve("database_session_manager").get_session()
    )
    flag_cache = FlagCache(cache_manager)
    flag_manager = FeatureFlagManager(
        repository=flag_repository,
        cache=flag_cache,
    )
    container.register_singleton("flag_repository", flag_repository)
    container.register_singleton("flag_cache", flag_cache)
    container.register_singleton("feature_flag_manager", flag_manager)

    # ==========================================
    # ثبت ریپازیتوری‌ها
    # ==========================================
    db_manager = container.resolve("database_session_manager")

    user_repo = UserRepositoryImpl(db_manager)
    order_repo = OrderRepositoryImpl(db_manager)
    payment_repo = PaymentRepositoryImpl(db_manager)
    coupon_repo = CouponRepositoryImpl(db_manager)
    form_repo = FormRepositoryImpl(db_manager)
    ticket_repo = TicketRepositoryImpl(db_manager)
    audit_repo = AuditRepositoryImpl(db_manager)

    container.register_singleton("user_repository", user_repo)
    container.register_singleton("order_repository", order_repo)
    container.register_singleton("payment_repository", payment_repo)
    container.register_singleton("coupon_repository", coupon_repo)
    container.register_singleton("form_repository", form_repo)
    container.register_singleton("ticket_repository", ticket_repo)
    container.register_singleton("audit_repository", audit_repo)

    # ==========================================
    # ثبت سرویس‌های لایه کاربرد
    # ==========================================
    message_publisher = None  # در صورت نیاز می‌توان پیاده‌سازی کرد

    # User Services
    user_registration_service = UserRegistrationService(
        user_repository=user_repo,
        message_publisher=message_publisher,
    )
    user_profile_service = UserProfileService(
        user_repository=user_repo,
        order_repository=order_repo,
        payment_repository=payment_repo,
    )
    user_level_upgrade_service = UserLevelUpgradeService(
        user_repository=user_repo,
        message_publisher=message_publisher,
    )

    container.register_singleton("user_registration_service", user_registration_service)
    container.register_singleton("user_profile_service", user_profile_service)
    container.register_singleton("user_level_upgrade_service", user_level_upgrade_service)

    # Order Services
    order_creation_service = OrderCreationService(
        order_repository=order_repo,
        user_repository=user_repo,
        coupon_repository=coupon_repo,
        message_publisher=message_publisher,
    )
    order_status_update_service = OrderStatusUpdateService(
        order_repository=order_repo,
        message_publisher=message_publisher,
    )
    order_history_service = OrderHistoryService(
        order_repository=order_repo,
        user_repository=user_repo,
    )

    container.register_singleton("order_creation_service", order_creation_service)
    container.register_singleton("order_status_update_service", order_status_update_service)
    container.register_singleton("order_history_service", order_history_service)

    # Payment Services
    payment_gateway_service = PaymentGatewayService(default_gateway="mock")
    # ثبت درگاه‌ها
    if app_config.enable_webhook:  # در صورت نیاز می‌توان زینپال را اضافه کرد
        zarinpal = ZarinpalGateway(
            merchant_id="your_merchant_id",
            sandbox=True,
        )
        payment_gateway_service._register_gateway("zarinpal", zarinpal)

    payment_verification_service = PaymentVerificationService(
        payment_repository=payment_repo,
        order_repository=order_repo,
        gateway_service=payment_gateway_service,
        message_publisher=message_publisher,
    )
    payment_webhook_service = PaymentWebhookService(
        payment_repository=payment_repo,
        verification_service=payment_verification_service,
        message_publisher=message_publisher,
    )

    container.register_singleton("payment_gateway_service", payment_gateway_service)
    container.register_singleton("payment_verification_service", payment_verification_service)
    container.register_singleton("payment_webhook_service", payment_webhook_service)

    # Form Services
    form_builder_service = FormBuilderService(
        form_repository=form_repo,
        message_publisher=message_publisher,
        cache=cache_manager,
    )
    form_submission_service = FormSubmissionService(
        form_repository=form_repo,
        user_repository=user_repo,
        message_publisher=message_publisher,
        cache=cache_manager,
    )
    form_analytics_service = FormAnalyticsService(
        form_repository=form_repo,
        cache=cache_manager,
    )

    container.register_singleton("form_builder_service", form_builder_service)
    container.register_singleton("form_submission_service", form_submission_service)
    container.register_singleton("form_analytics_service", form_analytics_service)

    # Broadcast Services
    broadcast_sender_service = BroadcastSenderService(
        broadcast_repository=None,  # نیاز به پیاده‌سازی BroadcastRepository
        user_repository=user_repo,
        message_publisher=message_publisher,
        cache=cache_manager,
    )
    broadcast_filter_service = BroadcastFilterService(
        user_repository=user_repo,
        cache=cache_manager,
    )
    broadcast_scheduler_service = BroadcastSchedulerService(
        broadcast_repository=None,
        broadcast_sender=broadcast_sender_service,
        message_publisher=message_publisher,
        cache=cache_manager,
    )

    container.register_singleton("broadcast_sender_service", broadcast_sender_service)
    container.register_singleton("broadcast_filter_service", broadcast_filter_service)
    container.register_singleton("broadcast_scheduler_service", broadcast_scheduler_service)

    # Ticket Services
    ticket_creation_service = TicketCreationService(
        ticket_repository=ticket_repo,
        user_repository=user_repo,
        message_publisher=message_publisher,
        cache=cache_manager,
    )
    ticket_assignment_service = TicketAssignmentService(
        ticket_repository=ticket_repo,
        user_repository=user_repo,
        message_publisher=message_publisher,
        cache=cache_manager,
    )
    ticket_resolution_service = TicketResolutionService(
        ticket_repository=ticket_repo,
        user_repository=user_repo,
        message_publisher=message_publisher,
        cache=cache_manager,
    )

    container.register_singleton("ticket_creation_service", ticket_creation_service)
    container.register_singleton("ticket_assignment_service", ticket_assignment_service)
    container.register_singleton("ticket_resolution_service", ticket_resolution_service)

    # Coupon Services
    coupon_generation_service = CouponGenerationService(
        coupon_repository=coupon_repo,
        user_repository=user_repo,
        message_publisher=message_publisher,
        cache=cache_manager,
    )
    coupon_validation_service = CouponValidationService(
        coupon_repository=coupon_repo,
        user_repository=user_repo,
        order_repository=order_repo,
        message_publisher=message_publisher,
        cache=cache_manager,
    )

    container.register_singleton("coupon_generation_service", coupon_generation_service)
    container.register_singleton("coupon_validation_service", coupon_validation_service)

    # Analytics Services
    user_behavior_analytics = UserBehaviorAnalyticsService(
        user_repository=user_repo,
        order_repository=order_repo,
        cache=cache_manager,
    )
    order_statistics_service = OrderStatisticsService(
        order_repository=order_repo,
        payment_repository=payment_repo,
        user_repository=user_repo,
        cache=cache_manager,
    )
    ab_testing_service = ABTestingService(
        ab_test_repository=None,  # نیاز به پیاده‌سازی
        user_repository=user_repo,
        message_publisher=message_publisher,
        cache=cache_manager,
    )

    container.register_singleton("user_behavior_analytics", user_behavior_analytics)
    container.register_singleton("order_statistics_service", order_statistics_service)
    container.register_singleton("ab_testing_service", ab_testing_service)

    # ==========================================
    # ثبت Use Cases
    # ==========================================
    register_user_use_case = RegisterUserUseCase(
        registration_service=user_registration_service,
    )
    update_profile_use_case = UpdateProfileUseCase(
        profile_service=user_profile_service,
    )
    create_order_use_case = CreateOrderUseCase(
        order_creation_service=order_creation_service,
    )
    cancel_order_use_case = CancelOrderUseCase(
        order_creation_service=order_creation_service,
    )
    initiate_payment_use_case = InitiatePaymentUseCase(
        payment_repository=payment_repo,
        user_repository=user_repo,
        order_repository=order_repo,
        gateway_service=payment_gateway_service,
    )
    confirm_payment_use_case = ConfirmPaymentUseCase(
        verification_service=payment_verification_service,
    )

    container.register_singleton("register_user_use_case", register_user_use_case)
    container.register_singleton("update_profile_use_case", update_profile_use_case)
    container.register_singleton("create_order_use_case", create_order_use_case)
    container.register_singleton("cancel_order_use_case", cancel_order_use_case)
    container.register_singleton("initiate_payment_use_case", initiate_payment_use_case)
    container.register_singleton("confirm_payment_use_case", confirm_payment_use_case)

    # ==========================================
    # ثبت Audit Logger
    # ==========================================
    audit_logger = AuditLogger(
        repository=audit_repo,
        default_status="success",
        enabled=True,
    )
    container.register_singleton("audit_logger", audit_logger)

    # ==========================================
    # ثبت Health Checker
    # ==========================================
    health_checker = HealthChecker()
    container.register_singleton("health_checker", health_checker)

    # ==========================================
    # ثبت Middlewareها
    # ==========================================
    rate_limiter_middleware = RateLimiterMiddleware(rate_limit_config)
    logging_middleware = LoggingMiddleware()
    i18n_middleware = I18nMiddleware(default_language="fa")
    feature_flag_middleware = FeatureFlagMiddleware(flag_manager)

    container.register_singleton("rate_limiter_middleware", rate_limiter_middleware)
    container.register_singleton("logging_middleware", logging_middleware)
    container.register_singleton("i18n_middleware", i18n_middleware)
    container.register_singleton("feature_flag_middleware", feature_flag_middleware)

    audit_middleware = AuditMiddleware(
        audit_logger=audit_logger,
        log_requests=True,
        log_errors=True,
        enabled=True,
    )
    container.register_singleton("audit_middleware", audit_middleware)

    # ==========================================
    # ثبت Handlers
    # ==========================================
    start_command_handler = StartCommandHandler(
        register_user_use_case=register_user_use_case,
    )
    greeting_handler = GreetingHandler()

    profile_handler = ProfileHandler(
        profile_service=user_profile_service,
        level_upgrade_service=user_level_upgrade_service,
    )
    order_history_handler = OrderHistoryHandler(
        order_history_service=order_history_service,
    )
    help_handler = HelpHandler()

    form_list_handler = FormListHandler(
        form_builder_service=form_builder_service,
    )
    # برای FormStartHandler و غیره نیاز به state manager داریم که فعلاً پیاده‌سازی نشده
    # اینجا به‌صورت placeholder می‌گذاریم
    form_start_handler = FormStartHandler(
        form_repository=form_repo,
        state_manager=None,  # نیاز به FormStateManager
    )
    form_step_handler = FormStepHandler(
        form_repository=form_repo,
        state_manager=None,
    )
    form_submit_handler = FormSubmitHandler(
        form_repository=form_repo,
        form_submission_service=form_submission_service,
        state_manager=None,
    )

    payment_initiate_handler = PaymentInitiateHandler(
        initiate_payment_use_case=initiate_payment_use_case,
        coupon_validation_service=coupon_validation_service,
    )
    payment_callback_handler = PaymentCallbackHandler(
        confirm_payment_use_case=confirm_payment_use_case,
    )
    coupon_apply_handler = CouponApplyHandler(
        coupon_validation_service=coupon_validation_service,
        coupon_generation_service=coupon_generation_service,
    )

    admin_panel_entry_handler = AdminPanelEntryHandler(
        profile_service=user_profile_service,
    )
    admin_callbacks_handler = AdminCallbacksHandler()
    admin_commands_handler = AdminCommandsHandler(
        profile_service=user_profile_service,
    )

    container.register_singleton("start_command_handler", start_command_handler)
    container.register_singleton("greeting_handler", greeting_handler)
    container.register_singleton("profile_handler", profile_handler)
    container.register_singleton("order_history_handler", order_history_handler)
    container.register_singleton("help_handler", help_handler)
    container.register_singleton("form_list_handler", form_list_handler)
    container.register_singleton("form_start_handler", form_start_handler)
    container.register_singleton("form_step_handler", form_step_handler)
    container.register_singleton("form_submit_handler", form_submit_handler)
    container.register_singleton("payment_initiate_handler", payment_initiate_handler)
    container.register_singleton("payment_callback_handler", payment_callback_handler)
    container.register_singleton("coupon_apply_handler", coupon_apply_handler)
    container.register_singleton("admin_panel_entry_handler", admin_panel_entry_handler)
    container.register_singleton("admin_callbacks_handler", admin_callbacks_handler)
    container.register_singleton("admin_commands_handler", admin_commands_handler)

    # ==========================================
    # ثبت Admin Panel Modules (Feature Management)
    # ==========================================
    feature_management_handlers = FeatureManagementHandlers(
        flag_manager=flag_manager,
    )
    container.register_singleton("feature_management_handlers", feature_management_handlers)

    # ==========================================
    # ثبت Startup/Shutdown Hooks
    # ==========================================
    startup_hooks = StartupHooks()
    shutdown_hooks = ShutdownHooks()

    container.register_singleton("startup_hooks", startup_hooks)
    container.register_singleton("shutdown_hooks", shutdown_hooks)

    logger.info("Container built with all dependencies registered.")
    return container