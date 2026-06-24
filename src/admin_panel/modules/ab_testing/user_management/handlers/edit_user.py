# my_bot_project/src/admin_panel/modules/user_management/handlers/edit_user.py
"""
هندلر ویرایش کاربر (Edit User Handler).

این هندلر مسئولیت ویرایش اطلاعات کاربران در پنل مدیریت را بر عهده دارد.
شامل نمایش فرم ویرایش، پردازش تغییرات و ذخیره‌سازی اطلاعات است.
"""

from typing import Optional, Dict, Any

from aiogram import types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold, hitalic, hcode

from admin_panel.core.permissions.permission_checker import PermissionChecker
from admin_panel.modules.user_management.services.user_edit_service import UserEditService
from admin_panel.modules.user_management.keyboards.user_edit_keyboard import (
    get_user_edit_keyboard,
    get_edit_field_keyboard,
    get_edit_confirm_keyboard,
)
from admin_panel.modules.user_management.validators.user_validator import UserValidator
from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.exceptions.not_found_errors import UserNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.application.services.user.user_profile import UserProfileService

logger = get_logger(__name__)


class EditUserHandler:
    """
    هندلر ویرایش کاربر.

    این کلاس با استفاده از UserEditService و UserRepository،
    عملیات ویرایش اطلاعات کاربران را در پنل مدیریت انجام می‌دهد.
    """

    # فیلدهای قابل ویرایش
    EDITABLE_FIELDS = {
        "first_name": "نام",
        "last_name": "نام خانوادگی",
        "username": "نام کاربری",
        "phone_number": "شماره تلفن",
        "email": "ایمیل",
        "role": "نقش",
        "level": "سطح",
        "points": "امتیاز",
        "is_active": "وضعیت فعال بودن",
        "is_banned": "وضعیت مسدود بودن",
    }

    def __init__(
        self,
        user_repository: UserRepository,
        user_profile_service: UserProfileService,
        permission_checker: PermissionChecker,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            user_repository: ریپازیتوری کاربر.
            user_profile_service: سرویس پروفایل کاربر.
            permission_checker: بررسی‌کننده دسترسی‌ها.
        """
        self._user_repository = user_repository
        self._user_profile_service = user_profile_service
        self._permission_checker = permission_checker
        self._edit_service = UserEditService(user_repository)
        self._validator = UserValidator()

        # وضعیت ویرایش کاربران (user_id -> {field, value, temp_data})
        self._edit_states: Dict[int, Dict[str, Any]] = {}

        logger.info("EditUserHandler initialized.")

    async def show_edit_form(self, callback: CallbackQuery) -> None:
        """
        نمایش فرم ویرایش کاربر.

        Args:
            callback: کالبک با داده‌ی `admin_user_edit:{user_id}`.
        """
        try:
            # استخراج شناسه کاربر
            user_id = int(callback.data.split(":")[1]) if ":" in callback.data else 0
            if user_id <= 0:
                await callback.answer("⚠️ شناسه کاربر نامعتبر است.", show_alert=True)
                return

            # بررسی دسترسی
            current_user = await self._get_user_from_callback(callback)
            if not current_user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(current_user, "users.edit")

            # دریافت کاربر هدف
            target_user = await self._user_repository.get_by_id(user_id)
            if not target_user:
                raise UserNotFoundError(user_id=user_id)

            # ذخیره وضعیت ویرایش
            self._edit_states[user_id] = {
                "target_user": target_user,
                "original_data": target_user.to_dict(),
                "changes": {},
                "field": None,
            }

            # نمایش فرم ویرایش
            text = self._build_edit_form_text(target_user)
            keyboard = get_user_edit_keyboard(user_id)

            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer(f"ویرایش کاربر {target_user.full_name}")

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)

        except UserNotFoundError as e:
            logger.warning(f"User not found: {e}")
            await callback.answer("⚠️ کاربر مورد نظر یافت نشد.", show_alert=True)

        except Exception as e:
            logger.error(f"Error showing edit form for user {user_id}: {e}")
            await callback.answer("⚠️ خطا در نمایش فرم ویرایش.", show_alert=True)

    async def edit_field(self, callback: CallbackQuery) -> None:
        """
        ویرایش یک فیلد خاص از کاربر.

        Args:
            callback: کالبک با داده‌ی `admin_user_edit_field:{user_id}:{field}`.
        """
        try:
            parts = callback.data.split(":")
            if len(parts) < 3:
                await callback.answer("⚠️ داده‌های کالبک نامعتبر است.", show_alert=True)
                return

            user_id = int(parts[1])
            field_name = parts[2]

            if field_name not in self.EDITABLE_FIELDS:
                await callback.answer(f"⚠️ فیلد '{field_name}' قابل ویرایش نیست.", show_alert=True)
                return

            # بررسی دسترسی
            current_user = await self._get_user_from_callback(callback)
            if not current_user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(current_user, "users.edit")

            # دریافت کاربر هدف
            target_user = await self._user_repository.get_by_id(user_id)
            if not target_user:
                raise UserNotFoundError(user_id=user_id)

            # ذخیره فیلد در حال ویرایش
            state = self._edit_states.get(user_id, {})
            state["field"] = field_name
            self._edit_states[user_id] = state

            # دریافت مقدار فعلی
            current_value = getattr(target_user, field_name, None)
            if isinstance(current_value, bool):
                current_value = "بله" if current_value else "خیر"
            elif current_value is None:
                current_value = "مشخص نشده"

            field_label = self.EDITABLE_FIELDS.get(field_name, field_name)

            # نمایش راهنمای ورودی
            input_guide = self._get_input_guide(field_name)

            await callback.message.edit_text(
                text=f"✏️ **ویرایش {field_label}**\n\n"
                     f"مقدار فعلی: `{current_value}`\n\n"
                     f"{input_guide}\n\n"
                     f"لطفاً مقدار جدید را وارد کنید.\n"
                     f"برای لغو، روی دکمه «انصراف» کلیک کنید.",
                reply_markup=get_edit_field_keyboard(user_id),
                parse_mode="Markdown",
            )
            await callback.answer()

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)

        except UserNotFoundError as e:
            logger.warning(f"User not found: {e}")
            await callback.answer("⚠️ کاربر مورد نظر یافت نشد.", show_alert=True)

        except Exception as e:
            logger.error(f"Error editing field {field_name} for user {user_id}: {e}")
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

            # پیدا کردن کاربری که در حال ویرایش است
            # جستجو در edit_states برای پیدا کردن کاربری که توسط این ادمین ویرایش می‌شود
            target_user_id = None
            for uid, state in self._edit_states.items():
                if state.get("editor_id") == user_id:
                    target_user_id = uid
                    break

            if not target_user_id:
                await message.answer(
                    "⚠️ شما در حال ویرایش هیچ کاربری نیستید.\n"
                    "لطفاً ابتدا یک کاربر را برای ویرایش انتخاب کنید.",
                )
                return

            state = self._edit_states.get(target_user_id, {})
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
            self._edit_states[target_user_id] = state

            # دریافت کاربر هدف
            target_user = await self._user_repository.get_by_id(target_user_id)
            if not target_user:
                await message.answer("⚠️ کاربر مورد نظر یافت نشد.")
                return

            # نمایش تأیید تغییرات
            field_label = self.EDITABLE_FIELDS.get(field_name, field_name)
            old_value = getattr(target_user, field_name, None)
            if isinstance(old_value, bool):
                old_value = "بله" if old_value else "خیر"
            elif old_value is None:
                old_value = "مشخص نشده"

            await message.answer(
                f"✅ **تغییرات اعمال شد**\n\n"
                f"فیلد: {field_label}\n"
                f"مقدار قبلی: `{old_value}`\n"
                f"مقدار جدید: `{new_value}`\n\n"
                f"برای تأیید نهایی، روی دکمه «تأیید تغییرات» کلیک کنید.\n"
                f"برای لغو، روی دکمه «انصراف» کلیک کنید.",
                reply_markup=get_edit_confirm_keyboard(target_user_id),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error handling edit input: {e}")
            await message.answer(
                "⚠️ خطا در پردازش ورودی. لطفاً دوباره تلاش کنید.",
            )

    async def confirm_edit(self, callback: CallbackQuery) -> None:
        """
        تأیید و ذخیره تغییرات کاربر.

        Args:
            callback: کالبک با داده‌ی `admin_user_confirm:{user_id}`.
        """
        try:
            user_id = int(callback.data.split(":")[1]) if ":" in callback.data else 0
            if user_id <= 0:
                await callback.answer("⚠️ شناسه کاربر نامعتبر است.", show_alert=True)
                return

            # بررسی دسترسی
            current_user = await self._get_user_from_callback(callback)
            if not current_user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(current_user, "users.edit")

            state = self._edit_states.get(user_id, {})
            changes = state.get("changes", {})

            if not changes:
                await callback.answer("⚠️ هیچ تغییری برای ذخیره وجود ندارد.", show_alert=True)
                return

            # اعمال تغییرات
            target_user = await self._user_repository.get_by_id(user_id)
            if not target_user:
                raise UserNotFoundError(user_id=user_id)

            # اعمال تغییرات روی موجودیت
            for field, value in changes.items():
                # تبدیل مقادیر بولی
                if field in ("is_active", "is_banned"):
                    value = value.lower() in ("true", "بله", "1", "yes", "active", "فعال")
                elif field == "points":
                    try:
                        value = int(value)
                    except ValueError:
                        await callback.answer("⚠️ امتیاز باید عدد باشد.", show_alert=True)
                        return

                setattr(target_user, field, value)

            # ذخیره در دیتابیس
            updated_user = await self._user_repository.save(target_user)

            # پاک کردن وضعیت ویرایش
            if user_id in self._edit_states:
                del self._edit_states[user_id]

            # نمایش پیام موفقیت
            await callback.message.edit_text(
                text="✅ **تغییرات با موفقیت ذخیره شد.**\n\n"
                     f"اطلاعات کاربر {updated_user.full_name} به‌روزرسانی شد.",
                reply_markup=self._get_back_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer("✅ تغییرات ذخیره شد.")

            logger.info(f"User {user_id} updated by admin {current_user.id}")

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)

        except UserNotFoundError as e:
            logger.warning(f"User not found: {e}")
            await callback.answer("⚠️ کاربر مورد نظر یافت نشد.", show_alert=True)

        except Exception as e:
            logger.error(f"Error confirming edit for user {user_id}: {e}")
            await callback.answer("⚠️ خطا در ذخیره تغییرات.", show_alert=True)

    async def cancel_edit(self, callback: CallbackQuery) -> None:
        """
        لغو ویرایش کاربر.

        Args:
            callback: کالبک با داده‌ی `admin_user_cancel:{user_id}`.
        """
        try:
            user_id = int(callback.data.split(":")[1]) if ":" in callback.data else 0
            if user_id <= 0:
                await callback.answer("⚠️ شناسه کاربر نامعتبر است.", show_alert=True)
                return

            # پاک کردن وضعیت ویرایش
            if user_id in self._edit_states:
                del self._edit_states[user_id]

            await callback.message.edit_text(
                text="❌ **ویرایش لغو شد.**\n\n"
                     "تغییرات اعمال نشد.",
                reply_markup=self._get_back_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer("ویرایش لغو شد.")

        except Exception as e:
            logger.error(f"Error cancelling edit for user {user_id}: {e}")
            await callback.answer("⚠️ خطا در لغو ویرایش.", show_alert=True)

    def _build_edit_form_text(self, user) -> str:
        """
        ساخت متن فرم ویرایش کاربر.

        Args:
            user: موجودیت کاربر.

        Returns:
            str: متن فرم.
        """
        lines = [
            f"✏️ **ویرایش کاربر**",
            "",
            f"👤 کاربر: {user.full_name} (@{user.username or 'ندارد'})",
            f"🆔 شناسه: `{user.id}`",
            "",
            "📌 **فیلدهای قابل ویرایش:**",
        ]

        for field, label in self.EDITABLE_FIELDS.items():
            value = getattr(user, field, None)
            if isinstance(value, bool):
                display = "✅" if value else "❌"
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
            "first_name": "نام کوچک کاربر را وارد کنید.",
            "last_name": "نام خانوادگی کاربر را وارد کنید.",
            "username": "نام کاربری تلگرام را بدون @ وارد کنید.",
            "phone_number": "شماره تلفن را با فرمت 09xxxxxxxxx وارد کنید.",
            "email": "آدرس ایمیل را وارد کنید.",
            "role": "نقش را وارد کنید (admin, manager, operator, user).",
            "level": "سطح را وارد کنید (bronze, silver, gold, platinum, diamond).",
            "points": "امتیاز را به‌صورت عدد وارد کنید.",
            "is_active": "فعال یا غیرفعال (بله/خیر).",
            "is_banned": "مسدود یا غیرمسدود (بله/خیر).",
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
        if field_name == "username":
            if not value or not value.isalnum() or len(value) < 3:
                return "نام کاربری باید حداقل ۳ کاراکتر و فقط شامل حروف و اعداد باشد."
            if len(value) > 32:
                return "نام کاربری نباید بیشتر از ۳۲ کاراکتر باشد."

        elif field_name == "phone_number":
            if value:
                try:
                    from my_bot.shared.utils.text_validators import validate_phone
                    validate_phone(value)
                except Exception as e:
                    return str(e)

        elif field_name == "email":
            if value:
                try:
                    from my_bot.shared.utils.text_validators import validate_email
                    validate_email(value)
                except Exception as e:
                    return str(e)

        elif field_name == "points":
            try:
                points = int(value)
                if points < 0:
                    return "امتیاز نمی‌تواند منفی باشد."
            except ValueError:
                return "امتیاز باید یک عدد صحیح باشد."

        elif field_name in ("role", "level"):
            valid_roles = ["admin", "manager", "operator", "user"]
            valid_levels = ["bronze", "silver", "gold", "platinum", "diamond"]
            valid_values = valid_roles if field_name == "role" else valid_levels
            if value.lower() not in valid_values:
                return f"مقدار '{value}' نامعتبر است. مقادیر مجاز: {', '.join(valid_values)}"

        elif field_name in ("is_active", "is_banned"):
            if value.lower() not in ("بله", "خیر", "true", "false", "1", "0", "yes", "no", "فعال", "غیرفعال"):
                return "مقدار باید بله/خیر یا فعال/غیرفعال باشد."

        return None

    def _get_back_keyboard(self) -> types.InlineKeyboardMarkup:
        """
        دریافت کیبورد بازگشت.

        Returns:
            types.InlineKeyboardMarkup: کیبورد بازگشت.
        """
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("🔙 بازگشت به لیست کاربران", callback_data="admin_users")],
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