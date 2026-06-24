# src/admin_panel/modules/content_management/handlers/add_content.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import ValidationError, DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button
from my_bot.presentation.keyboards.common.cancel_buttons import get_cancel_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.content_management.services import ContentCRUDService
from admin_panel.modules.content_management.validators import ContentValidator

logger = get_logger(__name__)


@requires_admin
async def add_content(query: CallbackQuery) -> None:
    """
    Start the add content process.
    Show content type selection.
    """
    try:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📄 مقاله",
                        callback_data="admin_content_add_type:article"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📰 خبر",
                        callback_data="admin_content_add_type:news"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📝 صفحه",
                        callback_data="admin_content_add_type:page"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🎯 لندینگ",
                        callback_data="admin_content_add_type:landing"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست",
                        callback_data="admin_content"
                    )
                ]
            ]
        )

        await query.message.edit_text(
            "➕ **افزودن محتوای جدید**\n\n"
            "لطفاً نوع محتوا را انتخاب کنید:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error showing add content menu: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش فرم افزودن محتوا.",
            reply_markup=get_back_button("admin_content")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def add_content_type(query: CallbackQuery) -> None:
    """
    Handle content type selection.
    Callback data format: "admin_content_add_type:{content_type}"
    """
    try:
        _, content_type = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ نوع محتوا نامعتبر است.", show_alert=True)
        return

    # Store content type in user state (in production, use cache/state manager)
    # For now, we'll pass via callback data
    
    # Ask for title
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_content"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"✏️ **افزودن محتوای جدید**\n\n"
        f"📂 نوع: {content_type}\n\n"
        f"لطفاً **عنوان** محتوا را وارد کنید:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def add_content_title(query: CallbackQuery) -> None:
    """
    Handle title input and ask for body.
    Callback data format: "admin_content_add_title:{content_type}:{title}"
    This is triggered after user sends text message.
    """
    # This handler is for callback query from title input
    # Actual title collection happens through message handler
    await query.answer()


@requires_admin
async def add_content_body(query: CallbackQuery) -> None:
    """
    Ask for content body.
    Callback data format: "admin_content_add_body:{content_type}:{title}"
    """
    try:
        _, content_type, title = query.data.split(":", 2)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش عنوان",
                    callback_data=f"admin_content_add_retry_title:{content_type}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_content"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"✏️ **افزودن محتوای جدید**\n\n"
        f"📂 نوع: {content_type}\n"
        f"📝 عنوان: {title}\n\n"
        f"لطفاً **متن** محتوا را وارد کنید:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def add_content_status(query: CallbackQuery) -> None:
    """
    Ask for content status (publish or draft).
    Callback data format: "admin_content_add_status:{content_type}:{title}:{body}"
    """
    try:
        _, content_type, title, body = query.data.split(":", 3)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ انتشار فوری",
                    callback_data=f"admin_content_add_save:{content_type}:{title}:{body}:published"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 ذخیره به عنوان پیش‌نویس",
                    callback_data=f"admin_content_add_save:{content_type}:{title}:{body}:draft"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش متن",
                    callback_data=f"admin_content_add_retry_body:{content_type}:{title}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_content"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"✅ **تأیید نهایی محتوا**\n\n"
        f"📂 نوع: {content_type}\n"
        f"📝 عنوان: {title}\n"
        f"📄 متن: {body[:100]}...\n\n"
        f"لطفاً وضعیت انتشار را انتخاب کنید:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def save_content(query: CallbackQuery) -> None:
    """
    Save the content to database.
    Callback data format: "admin_content_add_save:{content_type}:{title}:{body}:{status}"
    """
    try:
        _, content_type, title, body, status = query.data.split(":", 4)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        # Validate input
        validator = ContentValidator()
        validated_data = validator.validate_create(
            {
                "type": content_type,
                "title": title,
                "body": body,
                "status": status,
            }
        )

        # Save content
        service = ContentCRUDService()
        content = await service.create_content(
            type=validated_data["type"],
            title=validated_data["title"],
            body=validated_data["body"],
            status=validated_data["status"],
            created_by=query.from_user.id,
        )

        status_icon = "✅" if status == "published" else "📝"
        status_text = "منتشر شد" if status == "published" else "به عنوان پیش‌نویس ذخیره شد"

        await query.message.edit_text(
            f"{status_icon} محتوا با موفقیت {status_text}!\n\n"
            f"🆔 شناسه: `{content.get('id')}`\n"
            f"📝 عنوان: {content.get('title')}\n"
            f"📂 نوع: {content.get('type')}\n"
            f"📊 وضعیت: {'✅ منتشر شده' if content.get('status') == 'published' else '📝 پیش‌نویس'}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📄 مشاهده محتوا",
                            callback_data=f"admin_content_view:{content.get('id')}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="✏️ ویرایش محتوا",
                            callback_data=f"admin_content_edit:{content.get('id')}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="➕ افزودن محتوای جدید",
                            callback_data="admin_content_add"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت به لیست",
                            callback_data="admin_content"
                        )
                    ]
                ]
            ),
            parse_mode="Markdown"
        )
        logger.info(f"Content created by admin {query.from_user.id}: {content.get('id')}")
        await query.answer("محتوا ذخیره شد!")
    except ValidationError as e:
        logger.warning(f"Validation error in save_content: {e}")
        await query.message.edit_text(
            f"❌ خطای اعتبارسنجی:\n{str(e)}",
            reply_markup=get_back_button("admin_content")
        )
        await query.answer("خطا در اعتبارسنجی!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in save_content: {e}")
        await query.message.edit_text(
            "❌ خطا در ذخیره محتوا. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_content")
        )
        await query.answer("خطا در ذخیره!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in save_content: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در ذخیره محتوا.",
            reply_markup=get_back_button("admin_content")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def retry_title(query: CallbackQuery) -> None:
    """
    Retry entering title.
    Callback data format: "admin_content_add_retry_title:{content_type}"
    """
    try:
        _, content_type = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_content"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"✏️ **ویرایش عنوان**\n\n"
        f"📂 نوع: {content_type}\n\n"
        f"لطفاً **عنوان** جدید را وارد کنید:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def retry_body(query: CallbackQuery) -> None:
    """
    Retry entering body.
    Callback data format: "admin_content_add_retry_body:{content_type}:{title}"
    """
    try:
        _, content_type, title = query.data.split(":", 2)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش عنوان",
                    callback_data=f"admin_content_add_retry_title:{content_type}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_content"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"✏️ **ویرایش متن**\n\n"
        f"📂 نوع: {content_type}\n"
        f"📝 عنوان: {title}\n\n"
        f"لطفاً **متن** جدید را وارد کنید:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()