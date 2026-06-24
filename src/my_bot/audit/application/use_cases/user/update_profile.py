# my_bot_project/src/my_bot/application/use_cases/user/update_profile.py
"""
موارد استفاده به‌روزرسانی پروفایل کاربر (Update Profile Use Case).

این Use Case مسئولیت به‌روزرسانی اطلاعات پروفایل کاربر را بر عهده دارد.
با دریافت اطلاعات جدید کاربر، آن را اعتبارسنجی و در سیستم به‌روزرسانی می‌کند.
"""

from typing import Optional, Dict, Any

from my_bot.application.dtos.user_dto import UserUpdateDTO, UserResponseDTO
from my_bot.application.services.user.user_profile import UserProfileService
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.core.exceptions.not_found_errors import UserNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class UpdateProfileUseCase:
    """
    Use Case به‌روزرسانی پروفایل کاربر.

    این کلاس مسئولیت به‌روزرسانی اطلاعات پروفایل کاربر را بر عهده دارد.
    """

    def __init__(
        self,
        profile_service: UserProfileService,
    ) -> None:
        """
        مقداردهی اولیه Use Case به‌روزرسانی پروفایل.

        Args:
            profile_service: سرویس پروفایل کاربر.
        """
        self._profile_service = profile_service

    async def execute(
        self,
        user_id: int,
        update_data: Dict[str, Any],
    ) -> UserResponseDTO:
        """
        اجرای Use Case به‌روزرسانی پروفایل کاربر.

        Args:
            user_id: شناسه کاربر.
            update_data: داده‌های جدید برای به‌روزرسانی.

        Returns:
            UserResponseDTO: اطلاعات کاربر به‌روزرسانی‌شده.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
            ValidationError: اگر داده‌ها نامعتبر باشند.
            DatabaseError: اگر خطایی در ذخیره‌سازی رخ دهد.
        """
        logger.info(f"Executing UpdateProfileUseCase: user_id={user_id}")

        # اعتبارسنجی اولیه
        if user_id <= 0:
            raise ValidationError(
                message="شناسه کاربر باید یک عدد مثبت باشد.",
                context={"user_id": user_id},
            )

        try:
            # ایجاد DTO از داده‌های ورودی
            # فیلدهای قابل به‌روزرسانی: username, first_name, last_name, phone_number, email, metadata
            allowed_fields = {
                "username", "first_name", "last_name",
                "phone_number", "email", "metadata"
            }

            # فیلتر کردن داده‌ها
            filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}

            if not filtered_data:
                raise ValidationError(
                    message="حداقل یک فیلد برای به‌روزرسانی باید ارائه شود.",
                    context={"user_id": user_id},
                )

            # ساخت DTO
            update_dto = UserUpdateDTO(**filtered_data)

            # استفاده از سرویس پروفایل برای به‌روزرسانی
            updated_user = await self._profile_service.update_profile(
                user_id=user_id,
                data=update_dto,
            )

            logger.info(f"UpdateProfileUseCase completed: user_id={user_id}")

            return updated_user

        except UserNotFoundError as e:
            logger.warning(f"User not found in UpdateProfileUseCase: {e}")
            raise

        except ValidationError as e:
            logger.warning(f"Validation error in UpdateProfileUseCase: {e}")
            raise

        except DatabaseError as e:
            logger.error(f"Database error in UpdateProfileUseCase: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in UpdateProfileUseCase: {e}")
            raise DatabaseError(
                message=f"خطای غیرمنتظره در به‌روزرسانی پروفایل: {str(e)}",
                context={"user_id": user_id},
            )

    async def execute_update_phone(
        self,
        user_id: int,
        phone_number: str,
    ) -> UserResponseDTO:
        """
        به‌روزرسانی شماره تلفن کاربر.

        Args:
            user_id: شناسه کاربر.
            phone_number: شماره تلفن جدید.

        Returns:
            UserResponseDTO: اطلاعات کاربر به‌روزرسانی‌شده.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
            ValidationError: اگر شماره تلفن نامعتبر باشد.
        """
        logger.info(f"Executing UpdateProfileUseCase update_phone: user_id={user_id}")

        try:
            updated_user = await self._profile_service.update_phone(
                user_id=user_id,
                phone_number=phone_number,
            )

            logger.info(f"UpdateProfileUseCase update_phone completed: user_id={user_id}")
            return updated_user

        except Exception as e:
            logger.error(f"Error in UpdateProfileUseCase update_phone: {e}")
            raise

    async def execute_update_email(
        self,
        user_id: int,
        email: str,
    ) -> UserResponseDTO:
        """
        به‌روزرسانی ایمیل کاربر.

        Args:
            user_id: شناسه کاربر.
            email: ایمیل جدید.

        Returns:
            UserResponseDTO: اطلاعات کاربر به‌روزرسانی‌شده.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
            ValidationError: اگر ایمیل نامعتبر باشد.
        """
        logger.info(f"Executing UpdateProfileUseCase update_email: user_id={user_id}")

        try:
            updated_user = await self._profile_service.update_email(
                user_id=user_id,
                email=email,
            )

            logger.info(f"UpdateProfileUseCase update_email completed: user_id={user_id}")
            return updated_user

        except Exception as e:
            logger.error(f"Error in UpdateProfileUseCase update_email: {e}")
            raise

    async def execute_update_metadata(
        self,
        user_id: int,
        metadata: Dict[str, Any],
    ) -> UserResponseDTO:
        """
        به‌روزرسانی متادیتای کاربر.

        Args:
            user_id: شناسه کاربر.
            metadata: متادیتای جدید (اضافه می‌شود).

        Returns:
            UserResponseDTO: اطلاعات کاربر به‌روزرسانی‌شده.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        logger.info(f"Executing UpdateProfileUseCase update_metadata: user_id={user_id}")

        try:
            # دریافت کاربر و به‌روزرسانی metadata
            update_data = {
                "metadata": metadata,
            }
            update_dto = UserUpdateDTO(**update_data)

            updated_user = await self._profile_service.update_profile(
                user_id=user_id,
                data=update_dto,
            )

            logger.info(f"UpdateProfileUseCase update_metadata completed: user_id={user_id}")
            return updated_user

        except Exception as e:
            logger.error(f"Error in UpdateProfileUseCase update_metadata: {e}")
            raise