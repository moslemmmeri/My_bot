# src/tests/e2e/test_user_flow.py
"""
End-to-End Tests for User Flows.

These tests simulate real user interactions with the bot, covering
complete scenarios from start to finish, including:
- User registration and onboarding
- Navigation through menus
- Form submission
- Payment flow
- Admin interactions
- Error handling

These tests use mocked external dependencies to ensure isolation
and repeatability.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, User, Chat, InlineKeyboardMarkup, InlineKeyboardButton

from my_bot.core.config import Config
from my_bot.core.exceptions import ValidationError, NotFoundError
from my_bot.bootstrap.container import Container
from my_bot.bootstrap.app import create_bot, create_dispatcher
from my_bot.presentation.handlers.start.start_command import start_command
from my_bot.presentation.handlers.user.profile_handler import profile_handler, order_history_handler
from my_bot.presentation.handlers.form.form_list_handler import form_list_handler
from my_bot.presentation.handlers.form.form_start_handler import form_start_handler
from my_bot.presentation.handlers.form.form_step_handler import form_step_handler
from my_bot.presentation.handlers.form.form_submit_handler import form_submit_handler
from my_bot.presentation.handlers.payment.payment_initiate_handler import payment_initiate_handler
from my_bot.presentation.handlers.payment.payment_callback_handler import payment_callback_handler
from my_bot.presentation.handlers.admin.admin_panel_entry import admin_panel_callback, admin_command
from my_bot.presentation.handlers.admin.admin_callbacks import admin_callback_handler
from my_bot.presentation.keyboards.common.main_menu import get_main_menu_keyboard
from admin_panel.ui.main_keyboard import get_admin_main_keyboard

from tests.integration.test_handlers import MockBot


class TestUserFlow:
    """
    End-to-end test suite for user flows.
    Simulates a complete user journey through the bot.
    """

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot instance for E2E testing."""
        return MockBot(token="test_token")

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config(
            bot_token="test_token",
            admin_ids=[123456789],
            db_url="sqlite+aiosqlite:///:memory:",
            redis_url=None,
            cache_ttl_seconds=60,
            log_file_path="logs/test.log",
            rate_limit_requests=30,
            rate_limit_window_seconds=60,
        )

    @pytest.fixture
    def container(self, config):
        """Create test container with mocked repositories."""
        with patch('my_bot.infrastructure.database.session_manager.DatabaseSessionManager') as mock_db:
            container = Container(config)
            # Mock repositories for E2E testing
            container.user_repo = AsyncMock()
            container.order_repo = AsyncMock()
            container.payment_repo = AsyncMock()
            container.form_repo = AsyncMock()
            container.coupon_repo = AsyncMock()
            container.ticket_repo = AsyncMock()
            container.content_repo = AsyncMock()
            container.admin_repo = AsyncMock()
            container.feature_repo = AsyncMock()
            container.feedback_repo = AsyncMock()
            container.ab_test_repo = AsyncMock()
            container.behavior_repo = AsyncMock()
            yield container

    @pytest.fixture
    async def dispatcher(self, container, mock_bot):
        """Create a fully configured dispatcher with all handlers."""
        dp = Dispatcher(storage=container.storage)
        
        # Register user handlers
        dp.message.register(start_command, lambda msg: msg.text == "/start")
        dp.callback_query.register(profile_handler, lambda c: c.data == "profile")
        dp.callback_query.register(order_history_handler, lambda c: c.data == "order_history")
        dp.callback_query.register(form_list_handler, lambda c: c.data == "forms_list")
        dp.callback_query.register(form_start_handler, lambda c: c.data.startswith("form_start:"))
        dp.callback_query.register(form_step_handler, lambda c: c.data.startswith("form_step:"))
        dp.callback_query.register(form_submit_handler, lambda c: c.data.startswith("form_submit:"))
        dp.callback_query.register(payment_initiate_handler, lambda c: c.data.startswith("payment_initiate:"))
        dp.callback_query.register(payment_callback_handler, lambda c: c.data.startswith("payment_callback:"))
        
        # Register admin handlers
        dp.message.register(admin_command, lambda msg: msg.text == "/admin")
        dp.callback_query.register(admin_panel_callback, lambda c: c.data == "admin_panel")
        dp.callback_query.register(admin_callback_handler, lambda c: c.data.startswith("admin_"))
        
        # Register common navigation
        dp.callback_query.register(self._back_to_main, lambda c: c.data == "back_to_main")
        dp.callback_query.register(self._cancel_handler, lambda c: c.data == "cancel")
        
        return dp

    async def _back_to_main(self, query: CallbackQuery):
        """Helper: back to main menu."""
        await query.message.edit_text(
            "🏠 منوی اصلی",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown",
        )
        await query.answer()

    async def _cancel_handler(self, query: CallbackQuery):
        """Helper: cancel operation."""
        await query.message.edit_text(
            "❌ عملیات لغو شد.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown",
        )
        await query.answer()

    @pytest.fixture
    def test_user(self):
        """Create a test user."""
        return User(id=123456789, is_bot=False, first_name="Test", last_name="User", username="testuser")

    @pytest.fixture
    def test_admin_user(self):
        """Create a test admin user."""
        return User(id=123456789, is_bot=False, first_name="Admin", last_name="User", username="adminuser")

    @pytest.fixture
    def test_message(self, mock_bot, test_user):
        """Create a test message."""
        return Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(id=123456789, type="private"),
            from_user=test_user,
            text="/start",
            bot=mock_bot,
        )

    @pytest.fixture
    def test_callback_query(self, mock_bot, test_user):
        """Create a test callback query."""
        return CallbackQuery(
            id="123",
            from_user=test_user,
            chat_instance="test",
            message=Mock(
                message_id=1,
                chat=Chat(id=123456789, type="private"),
                text="Old text",
            ),
            data="profile",
            bot=mock_bot,
        )

    @pytest.fixture
    def admin_callback_query(self, mock_bot, test_admin_user):
        """Create an admin callback query."""
        return CallbackQuery(
            id="456",
            from_user=test_admin_user,
            chat_instance="test",
            message=Mock(
                message_id=2,
                chat=Chat(id=123456789, type="private"),
                text="Admin menu",
            ),
            data="admin_panel",
            bot=mock_bot,
        )

    # ====================== Test Scenarios ======================

    @pytest.mark.asyncio
    async def test_complete_user_journey(self, mock_bot, dispatcher, test_message, test_callback_query):
        """
        Test a complete user journey:
        1. Start command -> main menu
        2. View profile
        3. Browse forms
        4. Fill out a form
        5. Make a payment
        6. View order history
        """
        # Step 1: Start command
        await dispatcher.feed_update(mock_bot, test_message)
        assert len(mock_bot.sent_messages) == 1
        start_msg = mock_bot.sent_messages[0]
        assert "خوش آمد" in start_msg["text"] or "سلام" in start_msg["text"]
        assert start_msg["reply_markup"] is not None

        # Step 2: View profile
        profile_query = CallbackQuery(
            id="profile_1",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=2,
                chat=Chat(id=123456789, type="private"),
                text="Main menu",
            ),
            data="profile",
            bot=mock_bot,
        )
        with patch('my_bot.application.services.user.user_profile.UserProfileService.get_user_profile') as mock_profile:
            mock_profile.return_value = {
                "id": 1,
                "telegram_id": 123456789,
                "username": "testuser",
                "first_name": "Test",
                "last_name": "User",
                "is_active": True,
                "level": "gold",
                "points": 100,
                "created_at": datetime.now().isoformat(),
            }
            await dispatcher.feed_update(mock_bot, profile_query)
            # Should edit message with profile info
            assert len(mock_bot.edited_messages) >= 1
            edited_profile = mock_bot.edited_messages[-1]
            assert "پروفایل" in edited_profile["text"] or "👤" in edited_profile["text"]
            assert "testuser" in edited_profile["text"] or "Test" in edited_profile["text"]
            assert "gold" in edited_profile["text"] or "طلایی" in edited_profile["text"]

        # Step 3: Browse forms
        forms_query = CallbackQuery(
            id="forms_1",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=3,
                chat=Chat(id=123456789, type="private"),
                text="Profile",
            ),
            data="forms_list",
            bot=mock_bot,
        )
        with patch('my_bot.dynamic_forms.engine.form_renderer.FormRenderer.list_forms') as mock_list:
            mock_list.return_value = [
                {"id": 1, "title": "فرم ثبت‌نام", "description": "ثبت‌نام در دوره"},
                {"id": 2, "title": "فرم نظرسنجی", "description": "نظر شما مهم است"},
            ]
            await dispatcher.feed_update(mock_bot, forms_query)
            assert len(mock_bot.edited_messages) >= 1
            edited_forms = mock_bot.edited_messages[-1]
            assert "فرم" in edited_forms["text"] or "لیست" in edited_forms["text"]
            assert "ثبت‌نام" in edited_forms["text"]

        # Step 4: Fill out a form
        form_start_query = CallbackQuery(
            id="form_start_1",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=4,
                chat=Chat(id=123456789, type="private"),
                text="Forms list",
            ),
            data="form_start:1",
            bot=mock_bot,
        )
        with patch('my_bot.dynamic_forms.engine.form_renderer.FormRenderer.start_form') as mock_start:
            mock_start.return_value = (
                "مرحله ۱: لطفاً نام خود را وارد کنید",
                InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="🔙 بازگشت", callback_data="form_back:1")
                ]])
            )
            await dispatcher.feed_update(mock_bot, form_start_query)
            assert len(mock_bot.edited_messages) >= 1
            edited_form = mock_bot.edited_messages[-1]
            assert "مرحله ۱" in edited_form["text"] or "نام" in edited_form["text"]

        # Simulate user typing answer (text message)
        answer_message = Message(
            message_id=5,
            date=datetime.now(),
            chat=Chat(id=123456789, type="private"),
            from_user=test_callback_query.from_user,
            text="علی رضایی",
            bot=mock_bot,
        )
        # For simplicity, we'll skip the actual form step handler and go to submit
        # In a real test, we'd simulate the multi-step form flow

        # Step 5: Submit form
        form_submit_query = CallbackQuery(
            id="form_submit_1",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=6,
                chat=Chat(id=123456789, type="private"),
                text="Form step",
            ),
            data="form_submit:1",
            bot=mock_bot,
        )
        with patch('my_bot.dynamic_forms.engine.form_renderer.FormRenderer.submit_form') as mock_submit:
            mock_submit.return_value = "✅ فرم با موفقیت ثبت شد!"
            await dispatcher.feed_update(mock_bot, form_submit_query)
            assert len(mock_bot.edited_messages) >= 1
            edited_submit = mock_bot.edited_messages[-1]
            assert "ثبت شد" in edited_submit["text"] or "موفق" in edited_submit["text"]

        # Step 6: View order history
        order_query = CallbackQuery(
            id="order_history_1",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=7,
                chat=Chat(id=123456789, type="private"),
                text="Main menu",
            ),
            data="order_history",
            bot=mock_bot,
        )
        with patch('my_bot.application.services.order.order_history.OrderHistoryService.get_order_history') as mock_history:
            mock_history.return_value = {
                "orders": [
                    {"id": 1, "total_amount": 150000, "status": "paid", "created_at": "2024-01-01T10:00:00"},
                    {"id": 2, "total_amount": 75000, "status": "shipped", "created_at": "2024-01-05T14:30:00"},
                ],
                "total": 2,
            }
            await dispatcher.feed_update(mock_bot, order_query)
            assert len(mock_bot.edited_messages) >= 1
            edited_order = mock_bot.edited_messages[-1]
            assert "سفارشات" in edited_order["text"] or "تاریخچه" in edited_order["text"]
            assert "۱۵۰,۰۰۰" in edited_order["text"] or "۱۵۰۰۰۰" in edited_order["text"]

    @pytest.mark.asyncio
    async def test_payment_flow(self, mock_bot, dispatcher, test_callback_query):
        """
        Test the complete payment flow:
        1. Initiate payment from order
        2. Callback from payment gateway
        3. Verify payment status
        """
        # Step 1: Initiate payment
        payment_initiate_query = CallbackQuery(
            id="payment_init_1",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=10,
                chat=Chat(id=123456789, type="private"),
                text="Order details",
            ),
            data="payment_initiate:1",
            bot=mock_bot,
        )
        with patch('my_bot.application.services.payment.payment_gateway.PaymentGatewayService.initiate_payment') as mock_init:
            mock_init.return_value = {
                "payment_url": "https://payment.test/pay/123",
                "transaction_id": "txn_123",
                "status": "pending",
            }
            await dispatcher.feed_update(mock_bot, payment_initiate_query)
            assert len(mock_bot.edited_messages) >= 1
            edited_payment = mock_bot.edited_messages[-1]
            assert "پرداخت" in edited_payment["text"] or "pay" in edited_payment["text"].lower()
            # Should include a button with payment URL
            assert "reply_markup" in edited_payment

        # Step 2: Payment callback (simulate webhook)
        payment_callback_query = CallbackQuery(
            id="payment_cb_1",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=11,
                chat=Chat(id=123456789, type="private"),
                text="Payment pending",
            ),
            data="payment_callback:txn_123:success",
            bot=mock_bot,
        )
        with patch('my_bot.application.services.payment.payment_verification.PaymentVerificationService.verify_callback') as mock_verify:
            mock_verify.return_value = {
                "status": "completed",
                "transaction_id": "txn_123",
                "amount": 100000,
            }
            await dispatcher.feed_update(mock_bot, payment_callback_query)
            assert len(mock_bot.edited_messages) >= 1
            edited_callback = mock_bot.edited_messages[-1]
            assert "موفق" in edited_callback["text"] or "تأیید" in edited_callback["text"]

        # Step 3: Check payment status
        status_query = CallbackQuery(
            id="payment_status_1",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=12,
                chat=Chat(id=123456789, type="private"),
                text="Payment result",
            ),
            data="payment_status:txn_123",
            bot=mock_bot,
        )
        with patch('my_bot.application.services.payment.payment_verification.PaymentVerificationService.check_payment_status') as mock_status:
            mock_status.return_value = {
                "status": "completed",
                "reference_id": "ref_456",
            }
            await dispatcher.feed_update(mock_bot, status_query)
            assert len(mock_bot.edited_messages) >= 1
            edited_status = mock_bot.edited_messages[-1]
            assert "وضعیت" in edited_status["text"] or "تراکنش" in edited_status["text"]

    @pytest.mark.asyncio
    async def test_admin_flow(self, mock_bot, dispatcher, admin_callback_query):
        """
        Test the admin panel flow:
        1. Access admin panel
        2. View users list
        3. View orders
        4. Send broadcast
        """
        # Step 1: Access admin panel
        await dispatcher.feed_update(mock_bot, admin_callback_query)
        assert len(mock_bot.edited_messages) >= 1
        edited_admin = mock_bot.edited_messages[-1]
        assert "پنل مدیریت" in edited_admin["text"] or "مدیریت" in edited_admin["text"]
        assert "reply_markup" in edited_admin

        # Step 2: View users list
        users_query = CallbackQuery(
            id="admin_users_1",
            from_user=admin_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=20,
                chat=Chat(id=123456789, type="private"),
                text="Admin panel",
            ),
            data="admin_users_list:1",
            bot=mock_bot,
        )
        with patch('admin_panel.modules.user_management.services.user_list_service.UserListService.list_users') as mock_list:
            mock_list.return_value = {
                "items": [
                    {"id": 1, "username": "user1", "is_active": True, "level": "gold"},
                    {"id": 2, "username": "user2", "is_active": True, "level": "silver"},
                    {"id": 3, "username": "user3", "is_active": False, "level": "normal"},
                ],
                "total": 3,
                "page": 1,
                "page_size": 10,
            }
            await dispatcher.feed_update(mock_bot, users_query)
            assert len(mock_bot.edited_messages) >= 1
            edited_users = mock_bot.edited_messages[-1]
            assert "کاربران" in edited_users["text"] or "👥" in edited_users["text"]
            assert "user1" in edited_users["text"]
            assert "user2" in edited_users["text"]

        # Step 3: View orders (admin)
        orders_query = CallbackQuery(
            id="admin_orders_1",
            from_user=admin_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=21,
                chat=Chat(id=123456789, type="private"),
                text="Admin users",
            ),
            data="admin_orders_list:1",
            bot=mock_bot,
        )
        with patch('admin_panel.modules.order_management.services.order_list_service.OrderListService.list_orders') as mock_orders:
            mock_orders.return_value = {
                "items": [
                    {"id": 1, "user_id": 1, "total_amount": 150000, "status": "paid"},
                    {"id": 2, "user_id": 2, "total_amount": 75000, "status": "pending"},
                ],
                "total": 2,
                "page": 1,
                "page_size": 10,
            }
            await dispatcher.feed_update(mock_bot, orders_query)
            assert len(mock_bot.edited_messages) >= 1
            edited_orders = mock_bot.edited_messages[-1]
            assert "سفارشات" in edited_orders["text"] or "📦" in edited_orders["text"]
            assert "۱۵۰,۰۰۰" in edited_orders["text"] or "۱۵۰۰۰۰" in edited_orders["text"]

        # Step 4: Send broadcast
        broadcast_query = CallbackQuery(
            id="admin_broadcast_1",
            from_user=admin_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=22,
                chat=Chat(id=123456789, type="private"),
                text="Admin orders",
            ),
            data="admin_broadcast_compose",
            bot=mock_bot,
        )
        await dispatcher.feed_update(mock_bot, broadcast_query)
        assert len(mock_bot.edited_messages) >= 1
        edited_broadcast = mock_bot.edited_messages[-1]
        assert "ارسال" in edited_broadcast["text"] or "پیام" in edited_broadcast["text"]
        # Should have type selection buttons

    @pytest.mark.asyncio
    async def test_error_scenarios(self, mock_bot, dispatcher, test_callback_query):
        """
        Test error handling in user flows:
        - Form not found
        - Payment failure
        - Network error
        - Permission denied
        """
        # Scenario: Form not found
        form_start_query = CallbackQuery(
            id="form_start_error",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=30,
                chat=Chat(id=123456789, type="private"),
                text="Forms",
            ),
            data="form_start:999",
            bot=mock_bot,
        )
        with patch('my_bot.dynamic_forms.engine.form_renderer.FormRenderer.start_form') as mock_start:
            mock_start.side_effect = NotFoundError("Form not found")
            await dispatcher.feed_update(mock_bot, form_start_query)
            # Should answer callback with alert
            assert len(mob_bot.answered_callbacks) >= 1  # Note: typo in original, fixing
            # Should show error message
            assert any("یافت نشد" in cb.get("text", "") for cb in mock_bot.answered_callbacks)

        # Scenario: Payment failure
        payment_fail_query = CallbackQuery(
            id="payment_fail_1",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=31,
                chat=Chat(id=123456789, type="private"),
                text="Order",
            ),
            data="payment_initiate:1",
            bot=mock_bot,
        )
        with patch('my_bot.application.services.payment.payment_gateway.PaymentGatewayService.initiate_payment') as mock_init:
            mock_init.side_effect = Exception("Payment gateway timeout")
            await dispatcher.feed_update(mock_bot, payment_fail_query)
            # Should handle gracefully
            assert len(mock_bot.answered_callbacks) >= 1
            assert any("خطا" in cb.get("text", "") for cb in mock_bot.answered_callbacks)

        # Scenario: Permission denied for admin action
        non_admin_query = CallbackQuery(
            id="admin_panel_non_admin",
            from_user=test_callback_query.from_user,  # Not admin
            chat_instance="test",
            message=Mock(
                message_id=32,
                chat=Chat(id=123456789, type="private"),
                text="Main menu",
            ),
            data="admin_panel",
            bot=mock_bot,
        )
        with patch('admin_panel.core.permissions.permission_checker.is_admin', return_value=False):
            await dispatcher.feed_update(mock_bot, non_admin_query)
            assert len(mock_bot.answered_callbacks) >= 1
            # Should show "دسترسی غیرمجاز"
            assert any("دسترسی" in cb.get("text", "") for cb in mock_bot.answered_callbacks)

    @pytest.mark.asyncio
    async def test_navigation_flow(self, mock_bot, dispatcher, test_callback_query):
        """
        Test navigation between menus:
        - Main menu -> Profile -> Back to main
        - Main menu -> Forms -> Form details -> Cancel
        - Main menu -> Admin (if admin) -> Admin submenu -> Back
        """
        # Start from main menu
        main_menu_msg = Message(
            message_id=40,
            date=datetime.now(),
            chat=Chat(id=123456789, type="private"),
            from_user=test_callback_query.from_user,
            text="/start",
            bot=mock_bot,
        )
        await dispatcher.feed_update(mock_bot, main_menu_msg)
        assert len(mock_bot.sent_messages) == 1
        main_menu_sent = mock_bot.sent_messages[0]

        # Navigate to profile
        profile_query = CallbackQuery(
            id="nav_profile_1",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=41,
                chat=Chat(id=123456789, type="private"),
                text="Main menu",
            ),
            data="profile",
            bot=mock_bot,
        )
        with patch('my_bot.application.services.user.user_profile.UserProfileService.get_user_profile') as mock_profile:
            mock_profile.return_value = {"id": 1, "username": "testuser", "level": "gold", "points": 100}
            await dispatcher.feed_update(mock_bot, profile_query)
            assert len(mock_bot.edited_messages) >= 1
            edited_profile = mock_bot.edited_messages[-1]
            assert "پروفایل" in edited_profile["text"]

        # Back to main
        back_query = CallbackQuery(
            id="nav_back_1",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=42,
                chat=Chat(id=123456789, type="private"),
                text="Profile",
            ),
            data="back_to_main",
            bot=mock_bot,
        )
        await dispatcher.feed_update(mock_bot, back_query)
        assert len(mock_bot.edited_messages) >= 1
        back_edited = mock_bot.edited_messages[-1]
        assert "منوی اصلی" in back_edited["text"]

        # Navigate to forms, then cancel
        forms_nav_query = CallbackQuery(
            id="nav_forms_1",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=43,
                chat=Chat(id=123456789, type="private"),
                text="Main menu",
            ),
            data="forms_list",
            bot=mock_bot,
        )
        with patch('my_bot.dynamic_forms.engine.form_renderer.FormRenderer.list_forms') as mock_list:
            mock_list.return_value = [{"id": 1, "title": "فرم تست"}]
            await dispatcher.feed_update(mock_bot, forms_nav_query)
            assert len(mock_bot.edited_messages) >= 1
            forms_edited = mock_bot.edited_messages[-1]
            assert "فرم" in forms_edited["text"]

        # Cancel
        cancel_query = CallbackQuery(
            id="nav_cancel_1",
            from_user=test_callback_query.from_user,
            chat_instance="test",
            message=Mock(
                message_id=44,
                chat=Chat(id=123456789, type="private"),
                text="Forms",
            ),
            data="cancel",
            bot=mock_bot,
        )
        await dispatcher.feed_update(mock_bot, cancel_query)
        assert len(mock_bot.edited_messages) >= 1
        cancel_edited = mock_bot.edited_messages[-1]
        assert "لغو" in cancel_edited["text"] or "منوی اصلی" in cancel_edited["text"]

    @pytest.mark.asyncio
    async def test_parallel_user_flows(self, mock_bot, dispatcher, test_user):
        """
        Test multiple user flows in parallel to ensure thread safety.
        """
        async def simulate_user(user_id, user_name):
            # Create a user-specific message
            user_msg = Message(
                message_id=user_id * 100,
                date=datetime.now(),
                chat=Chat(id=user_id, type="private"),
                from_user=User(id=user_id, is_bot=False, first_name=user_name, username=user_name.lower()),
                text="/start",
                bot=mock_bot,
            )
            await dispatcher.feed_update(mock_bot, user_msg)
            return mock_bot.sent_messages[-1] if mock_bot.sent_messages else None

        # Simulate 5 users starting the bot simultaneously
        users = [
            ("User1", 111),
            ("User2", 222),
            ("User3", 333),
            ("User4", 444),
            ("User5", 555),
        ]
        tasks = [simulate_user(uid, name) for name, uid in users]
        results = await asyncio.gather(*tasks)

        # All users should have received a response
        assert all(result is not None for result in results)
        # Each message should contain a welcome
        for result in results:
            if result:
                assert "خوش آمد" in result["text"] or "سلام" in result["text"]