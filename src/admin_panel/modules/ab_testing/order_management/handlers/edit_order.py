# my_bot_project/src/admin_panel/modules/order_management/handlers/edit_order.py
"""
هندلر ویرایش سفارش (Edit Order Handler).

این هندلر مسئولیت ویرایش اطلاعات سفارشات در پنل مدیریت را بر عهده دارد.
شامل نمایش فرم ویرایش، پردازش تغییرات و ذخیره‌سازی اطلاعات است.
"""

from typing import Optional, Dict, Any

from aiogram import types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold, hitalic, hcode

from admin_panel.core.permissions.permission_checker import PermissionChecker
from admin_panel.modules.order_management.keyboards.order_actions import (
    get_order_actions_keyboard,
    get_edit_field_keyboard,
    get_edit_confirm_keyboard,
)
from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.exceptions.not_found_errors import OrderNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.application.services.order.order_status_update import OrderStatusUpdateService

logger = get_logger(__name__)


class EditOrderHandler:
    """
    هندلر ویرایش سفارش.

    این کلاس با استفاده از OrderRepository و OrderStatusUpdateService،
    عملیات ویرایش اطلاعات سفارشات را در پنل مدیریت انجام می‌دهد.
    """

    # فیلدهای قابل ویرایش
    EDITABLE_FIELDS = {
        "status": "وضعیت",
        "shipping_address": "آدرس تحویل",
        "tracking_code": "کد رهگیری",
        "notes": "یادداشت",
    }

    def __init__(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        order_status_update_service: OrderStatusUpdateService,
        permission_checker: PermissionChecker,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            order_repository: ریپازیتوری سفارش.
            user_repository: ریپازیتوری کاربر.
            order_status_update_service: سرویس به‌روزرسانی وضعیت سفارش.
            permission_checker: بررسی‌کننده دسترسی‌ها.
        """
        self._order_repository = order_repository
        self._user_repository = user_repository
        self._order_status_update_service = order_status_update_service
        self._permission_checker = permission_checker

        # وضعیت ویرایش سفارشات (order_id -> {field, value, changes})
        self._edit_states: Dict[int, Dict[str, Any]] = {}

        logger.info("EditOrderHandler initialized.")

    async def show_edit_form(self, callback: CallbackQuery) -> None:
        """
        نمایش فرم ویرایش سفارش.

        Args:
            callback: کالبک با داده‌ی `admin_order_edit:{order_id}`.
        """
        try:
            # استخراج شناسه سفارش
            order_id = int(callback.data.split(":")[1]) if ":" in callback.data else 0
            if order_id <= 0:
                await callback.answer("⚠️ شناسه سفارش نامعتبر است.", show_alert=True)
                return

            # بررسی دسترسی
            current_user = await self._get_user_from_callback(callback)
            if not current_user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(current_user, "orders.edit")

            # دریافت سفارش هدف
            target_order = await self._order_repository.get_by_id(order_id)
            if not target_order:
                raise OrderNotFoundError(order_id=str(order_id))

            # ذخیره وضعیت ویرایش
            self._edit_states[order_id] = {
                "target_order": target_order,
                "original_data": target_order.to_dict() if hasattr(target_order, "to_dict") else {},
                "changes": {},
                "field": None,
            }

            # نمایش فرم ویرایش
            text = self._build_edit_form_text(target_order)
            keyboard = get_order_actions_keyboard(order_id, target_order.status)

            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer(f"ویرایش سفارش #{target_order.order_number}")

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)

        except OrderNotFoundError as e:
            logger.warning(f"Order not found: {e}")
            await callback.answer("⚠️ سفارش مورد نظر یافت نشد.", show_alert=True)

        except Exception as e:
            logger.error(f"Error showing edit form for order {order_id}: {e}")
            await callback.answer("⚠️ خطا در نمایش فرم ویرایش.", show_alert=True)

    async def edit_field(self, callback: CallbackQuery) -> None:
        """
        ویرایش یک فیلد خاص از سفارش.

        Args:
            callback: کالبک با داده‌ی `admin_order_edit_field:{order_id}:{field}`.
        """
        try:
            parts = callback.data.split(":")
            if len(parts) < 3:
                await callback.answer("⚠️ داده‌های کالبک نامعتبر است.", show_alert=True)
                return

            order_id = int(parts[1])
            field_name = parts[2]

            if field_name not in self.EDITABLE_FIELDS:
                await callback.answer(f"⚠️ فیلد '{field_name}' قابل ویرایش نیست.", show_alert=True)
                return

            # بررسی دسترسی
            current_user = await self._get_user_from_callback(callback)
            if not current_user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(current_user, "orders.edit")

            # دریافت سفارش هدف
            target_order = await self._order_repository.get_by_id(order_id)
            if not target_order:
                raise OrderNotFoundError(order_id=str(order_id))

            # ذخیره فیلد در حال ویرایش
            state = self._edit_states.get(order_id, {})
            state["field"] = field_name
            self._edit_states[order_id] = state

            # دریافت مقدار فعلی
            current_value = getattr(target_order, field_name, None)
            if isinstance(current_value, OrderStatus):
                current_value = current_value.get_display_name()
            elif current_value is None:
                current_value = "مشخص نشده"
            elif field_name == "shipping_address" and not current_value:
                current_value = "آدرسی ثبت نشده"
            elif field_name == "tracking_code" and not current_value:
                current_value = "کد رهگیری ثبت نشده"

            field_label = self.EDITABLE_FIELDS.get(field_name, field_name)

            # نمایش راهنمای ورودی
            input_guide = self._get_input_guide(field_name)

            await callback.message.edit_text(
                text=f"✏️ **ویرایش {field_label}**\n\n"
                     f"مقدار فعلی: `{current_value}`\n\n"
                     f"{input_guide}\n\n"
                     f"لطفاً مقدار جدید را وارد کنید.\n"
                     f"برای لغو، روی دکمه «انصراف» کلیک کنید.",
                reply_markup=get_edit_field_keyboard(order_id),
                parse_mode="Markdown",
            )
            await callback.answer()

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)

        except OrderNotFoundError as e:
            logger.warning(f"Order not found: {e}")
            await callback.answer("⚠️ سفارش مورد نظر یافت نشد.", show_alert=True)

        except Exception as e:
            logger.error(f"Error editing field {field_name} for order {order_id}: {e}")
            await callback.answer("⚠️ خطا در ویرایش فیلد.", show_alert=True)

    async def handle_edit_input(self, message: Message) -> None:
        """
        پردازش ورودی کاربر برای ویرایش فیلد.

        Args:
            message: پیام دریافتی از تلگرام.
        """
        try:
            user_id = message.from_user.id

            # بررسی دسترسی
            current_user = await self._user_repository.get_by_telegram_id(user_id)
            if not current_user:
                await message.answer("⚠️ اطلاعات کاربر یافت نشد.")
                return

            # پیدا کردن سفارشی که در حال ویرایش است
            target_order_id = None
            for oid, state in self._edit_states.items():
                if state.get("editor_id") == user_id:
                    target_order_id = oid
                    break

            if not target_order_id:
                await message.answer(
                    "⚠️ شما در حال ویرایش هیچ سفارشی نیستید.\n"
                    "لطفاً ابتدا یک سفارش را برای ویرایش انتخاب کنید.",
                )
                return

            state = self._edit_states.get(target_order_id, {})
            field_name = state.get("field")

            if not field_name:
                await message.answer(
                    "⚠️ هیچ فیلدی برای ویرایش انتخاب نشده است.",
                )
                return

            # دریافت مقدار جدید
            new_value = message.text.strip()

            if not new_value:
                await message.answer(
                    "⚠️ مقدار نمی‌تواند خالی باشد. لطفاً دوباره وارد کنید.",
                )
                return

            # اعتبارسنجی مقدار جدید
            validation_error = self._validate_field_value(field_name, new_value)
            if validation_error:
                await message.answer(
                    f"⚠️ {validation_error}\n\nلطفاً دوباره وارد کنید.",
                )
                return

            # ذخیره تغییرات موقت
            if "changes" not in state:
                state["changes"] = {}
            state["changes"][field_name] = new_value
            self._edit_states[target_order_id] = state

            # دریافت سفارش هدف
            target_order = await self._order_repository.get_by_id(target_order_id)
            if not target_order:
                await message.answer("⚠️ سفارش مورد نظر یافت نشد.")
                return

            # نمایش تأیید تغییرات
            field_label = self.EDITABLE_FIELDS.get(field_name, field_name)
            old_value = getattr(target_order, field_name, None)
            if isinstance(old_value, OrderStatus):
                old_value = old_value.get_display_name()
            elif old_value is None:
                old_value = "مشخص نشده"

            await message.answer(
                f"✅ **تغییرات اعمال شد**\n\n"
                f"فیلد: {field_label}\n"
                f"مقدار قبلی: `{old_value}`\n"
                f"مقدار جدید: `{new_value}`\n\n"
                f"برای تأیید نهایی، روی دکمه «تأیید تغییرات» کلیک کنید.\n"
                f"برای لغو، روی دکمه «انصراف» کلیک کنید.",
                reply_markup=get_edit_confirm_keyboard(target_order_id),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error handling edit input: {e}")
            await message.answer(
                "⚠️ خطا در پردازش ورودی. لطفاً دوباره تلاش کنید.",
            )

    async def confirm_edit(self, callback: CallbackQuery) -> None:
        """
        تأیید و ذخیره تغییرات سفارش.

        Args:
            callback: کالبک با داده‌ی `admin_order_confirm:{order_id}`.
        """
        try:
            order_id = int(callback.data.split(":")[1]) if ":" in callback.data else 0
            if order_id <= 0:
                await callback.answer("⚠️ شناسه سفارش نامعتبر است.", show_alert=True)
                return

            # بررسی دسترسی
            current_user = await self._get_user_from_callback(callback)
            if not current_user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(current_user, "orders.edit")

            state = self._edit_states.get(order_id, {})
            changes = state.get("changes", {})

            if not changes:
                await callback.answer("⚠️ هیچ تغییری برای ذخیره وجود ندارد.", show_alert=True)
                return

            # دریافت سفارش هدف
            target_order = await self._order_repository.get_by_id(order_id)
            if not target_order:
                raise OrderNotFoundError(order_id=str(order_id))

            # اعمال تغییرات
            for field, value in changes.items():
                if field == "status":
                    # تغییر وضعیت با استفاده از سرویس
                    new_status = OrderStatus.from_string(value)
                    if not new_status:
                        await callback.answer(f"⚠️ وضعیت '{value}' نامعتبر است.", show_alert=True)
                        return

                    await self._order_status_update_service.update_status(
                        order_id=order_id,
                        new_status=new_status,
                        actor_id=current_user.id,
                        reason=f"ویرایش توسط ادمین {current_user.id}",
                    )
                elif field == "shipping_address":
                    target_order.shipping_address = value
                    await self._order_repository.save(target_order)
                elif field == "tracking_code":
                    target_order.tracking_code = value
                    await self._order_repository.save(target_order)
                elif field == "notes":
                    target_order.notes = value
                    await self._order_repository.save(target_order)

            # پاک کردن وضعیت ویرایش
            if order_id in self._edit_states:
                del self._edit_states[order_id]

            # نمایش پیام موفقیت
            await callback.message.edit_text(
                text="✅ **تغییرات با موفقیت ذخیره شد.**\n\n"
                     f"سفارش #{target_order.order_number} به‌روزرسانی شد.",
                reply_markup=self._get_back_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer("✅ تغییرات ذخیره شد.")

            logger.info(f"Order {order_id} updated by admin {current_user.id}")

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)

        except OrderNotFoundError as e:
            logger.warning(f"Order not found: {e}")
            await callback.answer("⚠️ سفارش مورد نظر یافت نشد.", show_alert=True)

        except Exception as e:
            logger.error(f"Error confirming edit for order {order_id}: {e}")
            await callback.answer("⚠️ خطا در ذخیره تغییرات.", show_alert=True)

    async def cancel_edit(self, callback: CallbackQuery) -> None:
        """
        لغو ویرایش سفارش.

        Args:
            callback: کالبک با داده‌ی `admin_order_cancel:{order_id}`.
        """
        try:
            order_id = int(callback.data.split(":")[1]) if ":" in callback.data else 0
            if order_id <= 0:
                await callback.answer("⚠️ شناسه سفارش نامعتبر است.", show_alert=True)
                return

            # پاک کردن وضعیت ویرایش
            if order_id in self._edit_states:
                del self._edit_states[order_id]

            await callback.message.edit_text(
                text="❌ **ویرایش لغو شد.**\n\n"
                     "تغییرات اعمال نشد.",
                reply_markup=self._get_back_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer("ویرایش لغو شد.")

        except Exception as e:
            logger.error(f"Error cancelling edit for order {order_id}: {e}")
            await callback.answer("⚠️ خطا در لغو ویرایش.", show_alert=True)

    def _build_edit_form_text(self, order) -> str:
        """
        ساخت متن فرم ویرایش سفارش.

        Args:
            order: موجودیت سفارش.

        Returns:
            str: متن فرم.
        """
        status_display = order.status.get_display_name() if order.status else "نامشخص"

        lines = [
            f"✏️ **ویرایش سفارش**",
            "",
            f"📋 شماره سفارش: `{order.order_number}`",
            f"📌 وضعیت فعلی: {status_display}",
            "",
            "📌 **فیلدهای قابل ویرایش:**",
        ]

        for field, label in self.EDITABLE_FIELDS.items():
            value = getattr(order, field, None)
            if isinstance(value, OrderStatus):
                display = value.get_display_name()
            elif value is None:
                display = "❌ مشخص نشده"
            else:
                display = str(value)

            lines.append(f"• {label}: `{display}`")

        lines.append("")
        lines.append("💡 روی دکمه هر فیلد کلیک کنید تا آن را ویرایش کنید.")
        lines.append("پس از ویرایش، روی «تأیید تغییرات» کلیک کنید.")

        return "\n".join(lines)

    def _get_input_guide(self, field_name: str) -> str:
        """
        دریافت راهنمای ورودی برای یک فیلد.

        Args:
            field_name: نام فیلد.

        Returns:
            str: راهنمای ورودی.
        """
        guides = {
            "status": "وضعیت جدید را وارد کنید.\n"
                       "مقادیر مجاز: pending, paid, processing, shipped, delivered, canceled, refunded, on_hold, failed",
            "shipping_address": "آدرس جدید تحویل را وارد کنید.",
            "tracking_code": "کد رهگیری جدید را وارد کنید.",
            "notes": "یادداشت جدید را وارد کنید.",
        }
        return guides.get(field_name, "لطفاً مقدار جدید را وارد کنید.")

    def _validate_field_value(self, field_name: str, value: str) -> Optional[str]:
        """
        اعتبارسنجی مقدار یک فیلد.

        Args:
            field_name: نام فیلد.
            value: مقدار جدید.

        Returns:
            Optional[str]: پیام خطا یا None در صورت معتبر بودن.
        """
        if field_name == "status":
            valid_statuses = [s.value for s in OrderStatus]
            if value.lower() not in valid_statuses:
                return f"وضعیت '{value}' نامعتبر است. مقادیر مجاز: {', '.join(valid_statuses)}"

        elif field_name == "shipping_address":
            if len(value) > 500:
                return "آدرس تحویل نباید بیشتر از ۵۰۰ کاراکتر باشد."

        elif field_name == "tracking_code":
            if len(value) > 100:
                return "کد رهگیری نباید بیشتر از ۱۰۰ کاراکتر باشد."

        elif field_name == "notes":
            if len(value) > 1000:
                return "یادداشت نباید بیشتر از ۱۰۰۰ کاراکتر باشد."

        return None

    def _get_back_keyboard(self) -> types.InlineKeyboardMarkup:
        """
        دریافت کیبورد بازگشت.

        Returns:
            types.InlineKeyboardMarkup: کیبورد بازگشت.
        """
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("🔙 بازگشت به لیست سفارشات", callback_data="admin_orders")],
        ])

    async def _get_user_from_callback(self, callback: CallbackQuery):
        """
        دریافت کاربر از کالبک.

        Args:
            callback: کالبک دریافتی.

        Returns:
            User یا None.
        """
        telegram_id = callback.from_user.id
        return await self._user_repository.get_by_telegram_id(telegram_id)