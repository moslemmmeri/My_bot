# src/my_bot/presentation/handlers/start_command.py
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from my_bot.core.logger import get_logger
from my_bot.core.config import Config
from my_bot.shared.utils.message_pool import MessagePool
from my_bot.presentation.keyboards.common.main_menu import get_main_menu_keyboard

logger = get_logger(__name__)


async def start_command(message: Message, bot: Bot, config: Config) -> None:
    """
    Handler for the /start command.

    Sends a welcome message with the main menu keyboard.
    Uses a random greeting from the message pool.
    """
    user_id = message.from_user.id
    username = message.from_user.username or "کاربر"
    first_name = message.from_user.first_name or ""

    logger.info(f"User {user_id} (@{username}) started the bot.")

    # Get a random greeting
    greeting = MessagePool.random_greeting()

    # Build welcome text
    welcome_text = (
        f"{greeting}\n\n"
        f"{first_name} عزیز، به ربات خوش آمدی! 🎉\n"
        f"من اینجا هستم تا بهت کمک کنم.\n\n"
        f"از منوی زیر یکی از گزینه‌ها رو انتخاب کن:"
    )

    # Check if user is admin (optional)
    # For now, we'll use the main menu; admin panel button is included conditionally in the keyboard builder.
    # The keyboard builder will check admin status if needed, but we can pass user_id to it.
    keyboard = get_main_menu_keyboard(user_id=user_id)

    await message.answer(
        text=welcome_text,
        reply_markup=keyboard,
        parse_mode="Markdown",
    )