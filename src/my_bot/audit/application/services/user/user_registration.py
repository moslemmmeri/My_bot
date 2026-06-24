# my_bot_project/src/my_bot/application/services/user/user_registration.py
"""
سرویس ثبت‌نام کاربر (User Registration Service).

این سرویس مسئولیت ثبت‌نام کاربران جدید در سیستم را بر عهده دارد.
با دریافت اطلاعات از تلگرام (telegram_id, username, first_name, last_name)،
کاربر را در دیتابیس ذخیره می‌کند و در صورت نیاز، رویدادهای مربوطه را منتشر می‌کند.
"""

from typing import Optional

from my_bot.application.dtos.user_dto import UserCreateDTO, UserResponseDTO
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.user import User
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher

logger = get_logger(__name__)


class UserRegistrationService:
    """
    سرویس ثبت‌نام کاربر.

    این کلاس مسئولیت ثبت‌نام کاربران جدید در سیستم را بر عهده دارد.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        message_publisher: Optional[MessagePublisher] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس ثبت‌نام.

        Args:
            user_repository: ریپازیتوری کاربر برای ذخیره‌سازی و بازیابی.
            message_publisher: انتشاردهنده پیام برای رویدادها (اختیاری).
        """
        self._user_repository = user_repository
        self._message_publisher = message_publisher

    async def register_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> UserResponseDTO:
        """
        ثبت‌نام یک کاربر جدید در سیستم.

        Args:
            telegram_id: شناسه تلگرام کاربر.
            username: نام کاربری تلگرام (اختیاری).
            first_name: نام کوچک کاربر (اختیاری).
            last_name: نام خانوادگی کاربر (اختیاری).

        Returns:
            UserResponseDTO: اطلاعات کاربر ثبت‌نام‌شده.

        Raises:
            ValidationError: اگر اطلاعات ورودی نامعتبر باشد.
            DatabaseError: اگر خطایی در ذخیره‌سازی رخ دهد.
        """
        # اعتبارسنجی ورودی
        if telegram_id <= 0:
            raise ValidationError(
                message="شناسه تلگرام باید یک عدد مثبت باشد.",
                context={"telegram_id": telegram_id},
            )

        # بررسی وجود کاربر
        existing_user = await self._user_repository.get_by_telegram_id(telegram_id)
        if existing_user:
            logger.info(f"User with telegram_id {telegram_id} already exists.")
            return UserResponseDTO.from_entity(existing_user)

        # ایجاد موجودیت کاربر
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

        # ذخیره‌سازی در دیتابیس
        try:
            saved_user = await self._user_repository.save(user)
            logger.info(f"User registered successfully: telegram_id={telegram_id}, id={saved_user.id}")

            # انتشار رویداد ثبت‌نام (در صورت وجود انتشاردهنده)
            if self._message_publisher:
                await self._message_publisher.publish_event(
                    event_type="user.registered",
                    event_data={
                        "user_id": saved_user.id,
                        "telegram_id": saved_user.telegram_id,
                        "username": saved_user.username,
                    },
                    source="UserRegistrationService",
                )

            return UserResponseDTO.from_entity(saved_user)

        except Exception as e:
            logger.error(f"Failed to register user {telegram_id}: {e}")
            raise DatabaseError(
                message=f"خطا در ثبت‌نام کاربر: {str(e)}",
                context={"telegram_id": telegram_id},
            )

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> UserResponseDTO:
        """
        دریافت کاربر موجود یا ایجاد کاربر جدید (Get or Create).

        این متد برای مواردی استفاده می‌شود که کاربر ممکن است از قبل وجود داشته باشد
        یا نباشد. اگر کاربر وجود داشته باشد، اطلاعات او به‌روزرسانی می‌شود.

        Args:
            telegram_id: شناسه تلگرام کاربر.
            username: نام کاربری تلگرام (اختیاری).
            first_name: نام کوچک کاربر (اختیاری).
            last_name: نام خانوادگی کاربر (اختیاری).

        Returns:
            UserResponseDTO: اطلاعات کاربر (موجود یا جدید).
        """
        # بررسی وجود کاربر
        existing_user = await self._user_repository.get_by_telegram_id(telegram_id)

        if existing_user:
            # به‌روزرسانی اطلاعات (در صورت تغییر)
            updated = False
            if username and existing_user.username != username:
                existing_user.username = username
                updated = True
            if first_name and existing_user.first_name != first_name:
                existing_user.first_name = first_name
                updated = True
            if last_name and existing_user.last_name != last_name:
                existing_user.last_name = last_name
                updated = True

            if updated:
                saved_user = await self._user_repository.save(existing_user)
                logger.info(f"User {telegram_id} information updated.")
                return UserResponseDTO.from_entity(saved_user)

            # به‌روزرسانی زمان آخرین فعالیت
            await self._user_repository.update_last_activity(existing_user.id or 0)
            return UserResponseDTO.from_entity(existing_user)

        # کاربر وجود ندارد، ثبت‌نام جدید
        return await self.register_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

    async def register_admin(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> UserResponseDTO:
        """
        ثبت‌نام یک ادمین جدید در سیستم.

        این متد مشابه register_user است، اما نقش کاربر را به ADMIN تنظیم می‌کند.

        Args:
            telegram_id: شناسه تلگرام کاربر.
            username: نام کاربری تلگرام (اختیاری).
            first_name: نام کوچک کاربر (اختیاری).
            last_name: نام خانوادگی کاربر (اختیاری).

        Returns:
            UserResponseDTO: اطلاعات ادمین ثبت‌نام‌شده.
        """
        from my_bot.core.constants.user_roles import UserRole

        # اعتبارسنجی ورودی
        if telegram_id <= 0:
            raise ValidationError(
                message="شناسه تلگرام باید یک عدد مثبت باشد.",
                context={"telegram_id": telegram_id},
            )

        # بررسی وجود کاربر
        existing_user = await self._user_repository.get_by_telegram_id(telegram_id)
        if existing_user:
            # اگر کاربر وجود دارد، نقش او را به ADMIN تغییر می‌دهیم
            if existing_user.role != UserRole.ADMIN:
                existing_user.role = UserRole.ADMIN
                saved_user = await self._user_repository.save(existing_user)
                logger.info(f"User {telegram_id} promoted to ADMIN.")
                return UserResponseDTO.from_entity(saved_user)
            return UserResponseDTO.from_entity(existing_user)

        # ایجاد موجودیت کاربر با نقش ADMIN
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN,
        )

        # ذخیره‌سازی در دیتابیس
        try:
            saved_user = await self._user_repository.save(user)
            logger.info(f"Admin registered successfully: telegram_id={telegram_id}, id={saved_user.id}")
            return UserResponseDTO.from_entity(saved_user)

        except Exception as e:
            logger.error(f"Failed to register admin {telegram_id}: {e}")
            raise DatabaseError(
                message=f"خطا در ثبت‌نام ادمین: {str(e)}",
                context={"telegram_id": telegram_id},
            )

    async def check_user_exists(self, telegram_id: int) -> bool:
        """
        بررسی وجود کاربر با شناسه تلگرام.

        Args:
            telegram_id: شناسه تلگرام کاربر.

        Returns:
            True اگر کاربر وجود داشته باشد، در غیر این صورت False.
        """
        return await self._user_repository.exists_by_telegram_id(telegram_id)