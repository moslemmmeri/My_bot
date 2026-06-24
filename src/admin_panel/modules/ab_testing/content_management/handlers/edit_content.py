# src/admin_panel/modules/content_management/handlers/edit_content.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import NotFoundError, ValidationError, DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.content_management.services import ContentCRUDService

logger = get_logger(__name__)


@requires_admin
async def edit_content(query: CallbackQuery) -> None:
    """
    Show edit form for content.
    Callback data format: "admin_content_edit:{content_id}"
    """
    try:
        _, content_id_str = query.data.split(":", 1)
        content_id = int(content_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه محتوا نامعتبر است.", show_alert=True)
        return

    try:
        service = ContentCRUDService()
        content = await service.get_content(content_id)

        if not content:
            await query.message.edit_text(
                "❌ محتوای مورد نظر یافت نشد.",
                reply_markup=get_back_button("admin_content")
            )
            await query.answer("محتوا یافت نشد!", show_alert=True)
            return

        # Show edit options
        text = (
            f"✏️ **ویرایش محتوا**\n\n"
            f"🆔 شناسه: `{content.get('id')}`\n"
            f"📝 عنوان: {content.get('title', 'بدون عنوان')}\n"
            f"📂 نوع: {content.get('type', 'unknown')}\n"
            f"📊 وضعیت: {'✅ منتشر شده' if content.get('status') == 'published' else '📝 پیش‌نویس'}\n"
            f"📅 ایجاد: {content.get('created_at', 'نامشخص')}\n\n"
            f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 ویرایش عنوان",
                        callback_data=f"admin_content_edit_title:{content_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📄 ویرایش متن",
                        callback_data=f"admin_content_edit_body:{content_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📂 تغییر نوع",
                        callback_data=f"admin_content_edit_type:{content_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 تغییر وضعیت",
                        callback_data=f"admin_content_edit_status:{content_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ انتشار",
                        callback_data=f"admin_content_publish:{content_id}"
                    ),
                    InlineKeyboardButton(
                        text="📝 پیش‌نویس",
                        callback_data=f"admin_content_draft:{content_id}"
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
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except NotFoundError as e:
        logger.warning(f"Content {content_id} not found: {e}")
        await query.message.edit_text(
            "❌ محتوای مورد نظر یافت نشد.",
            reply_markup=get_back_button("admin_content")
        )
        await query.answer("محتوا یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error editing content {content_id}: {e}")
        await query.answer("❌ خطا در دریافت اطلاعات محتوا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error editing content {content_id}: {e}", exc_info=True)
        await query.answer("❌ خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def edit_title(query: CallbackQuery) -> None:
    """
    Edit content title.
    Callback data format: "admin_content_edit_title:{content_id}"
    """
    try:
        _, content_id_str = query.data.split(":", 1)
        content_id = int(content_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه نامعتبر است.", show_alert=True)
        return

    # Store state that user is editing title
    # In production, you would store this in user state/cache
    await query.message.edit_text(
        f"✏️ **ویرایش عنوان**\n\n"
        f"لطفاً عنوان جدید را وارد کنید:\n"
        f"(برای انصراف روی دکمه لغو کلیک کنید)",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data=f"admin_content_edit:{content_id}"
                    )
                ]
            ]
        ),
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def edit_body(query: CallbackQuery) -> None:
    """
    Edit content body.
    Callback data format: "admin_content_edit_body:{content_id}"
    """
    try:
        _, content_id_str = query.data.split(":", 1)
        content_id = int(content_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه نامعتبر است.", show_alert=True)
        return

    await query.message.edit_text(
        f"✏️ **ویرایش متن**\n\n"
        f"لطفاً متن جدید را وارد کنید:\n"
        f"(برای انصراف روی دکمه لغو کلیک کنید)",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data=f"admin_content_edit:{content_id}"
                    )
                ]
            ]
        ),
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def change_status(query: CallbackQuery) -> None:
    """
    Change content status.
    Callback data format: "admin_content_edit_status:{content_id}"
    """
    try:
        _, content_id_str = query.data.split(":", 1)
        content_id = int(content_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ منتشر شده",
                    callback_data=f"admin_content_set_status:{content_id}:published"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 پیش‌نویس",
                    callback_data=f"admin_content_set_status:{content_id}:draft"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data=f"admin_content_edit:{content_id}"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"📊 **تغییر وضعیت محتوا**\n\n"
        f"وضعیت جدید را انتخاب کنید:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def set_status(query: CallbackQuery) -> None:
    """
    Set content status.
    Callback data format: "admin_content_set_status:{content_id}:{status}"
    """
    try:
        _, content_id_str, status = query.data.split(":", 2)
        content_id = int(content_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        service = ContentCRUDService()
        updated = await service.update_status(content_id, status)

        status_icon = "✅" if status == "published" else "📝"
        status_text = "منتشر شده" if status == "published" else "پیش‌نویس"

        await query.message.edit_text(
            f"{status_icon} وضعیت محتوا با موفقیت به «{status_text}» تغییر یافت.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت به ویرایش",
                            callback_data=f"admin_content_edit:{content_id}"
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
        logger.info(f"Content {content_id} status changed to {status} by admin {query.from_user.id}")
        await query.answer("وضعیت تغییر یافت!")
    except NotFoundError as e:
        logger.warning(f"Content {content_id} not found: {e}")
        await query.answer("محتوا یافت نشد!", show_alert=True)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        await query.answer(f"❌ {str(e)}", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error setting content status: {e}")
        await query.answer("❌ خطا در تغییر وضعیت!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error setting content status: {e}", exc_info=True)
        await query.answer("❌ خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def publish_content(query: CallbackQuery) -> None:
    """
    Quick publish content.
    Callback data format: "admin_content_publish:{content_id}"
    """
    try:
        _, content_id_str = query.data.split(":", 1)
        content_id = int(content_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه نامعتبر است.", show_alert=True)
        return

    try:
        service = ContentCRUDService()
        await service.update_status(content_id, "published")

        await query.message.edit_text(
            "✅ محتوا با موفقیت منتشر شد.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
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
        logger.info(f"Content {content_id} published by admin {query.from_user.id}")
        await query.answer("محتوا منتشر شد!")
    except NotFoundError as e:
        logger.warning(f"Content {content_id} not found: {e}")
        await query.answer("محتوا یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error publishing content: {e}")
        await query.answer("❌ خطا در انتشار محتوا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error publishing content: {e}", exc_info=True)
        await query.answer("❌ خطای غیرمنتظره!", show_alert=True)