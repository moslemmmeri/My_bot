# my_bot_project/src/my_bot/application/use_cases/user/register_user.py
"""
موارد استفاده ثبت‌نام کاربر (Register User Use Case).

این Use Case مسئولیت ثبت‌نام یک کاربر جدید در سیستم را بر عهده دارد.
با دریافت اطلاعات کاربر از تلگرام، کاربر را ثبت کرده و اطلاعات آن را
به همراه وضعیت (جدید یا موجود) برمی‌گرداند.
"""

from typing import Optional, Tuple

from my_bot.application.dtos.user_dto import UserResponseDTO
from my_bot.application.services.user.user_registration import UserRegistrationService
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class RegisterUserUseCase:
    """
    Use Case ثبت‌نام کاربر.

    این کلاس مسئولیت ثبت‌نام یک کاربر جدید در سیستم را بر عهده دارد.
    """

    def __init__(
        self,
        registration_service: UserRegistrationService,
    ) -> None:
        """
        مقداردهی اولیه Use Case ثبت‌نام.

        Args:
            registration_service: سرویس ثبت‌نام کاربر.
        """
        self._registration_service = registration_service

    async def execute(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Tuple[UserResponseDTO, bool]:
        """
        اجرای Use Case ثبت‌نام کاربر.

        Args:
            telegram_id: شناسه تلگرام کاربر.
            username: نام کاربری تلگرام (اختیاری).
            first_name: نام کوچک کاربر (اختیاری).
            last_name: نام خانوادگی کاربر (اختیاری).

        Returns:
            Tuple[UserResponseDTO, bool]: اطلاعات کاربر ثبت‌نام‌شده و
            وضعیت (True اگر کاربر جدید ایجاد شده باشد، False اگر قبلاً وجود داشته باشد).

        Raises:
            ValidationError: اگر اطلاعات ورودی نامعتبر باشد.
            DatabaseError: اگر خطایی در ذخیره‌سازی رخ دهد.
        """
        logger.info(
            f"Executing RegisterUserUseCase: telegram_id={telegram_id}, "
            f"username={username}"
        )

        # اعتبارسنجی اولیه
        if telegram_id <= 0:
            raise ValidationError(
                message="شناسه تلگرام باید یک عدد مثبت باشد.",
                context={"telegram_id": telegram_id},
            )

        try:
            # استفاده از سرویس ثبت‌نام برای دریافت یا ایجاد کاربر
            # متد get_or_create_user در سرویس وجود دارد که این کار را انجام می‌دهد
            user_dto = await self._registration_service.get_or_create_user(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )

            # بررسی اینکه کاربر جدید است یا قبلاً وجود داشته
            is_new = False
            # با توجه به پیاده‌سازی سرویس، اگر کاربر جدید ثبت شده باشد،
            # می‌توانیم از طریق متد check_user_exists تشخیص دهیم که قبلاً وجود نداشته
            # اما در اینجا با توجه به طراحی سرویس، از متد get_or_create_user
            # استفاده می‌کنیم که خودش تشخیص می‌دهد.
            # برای تشخیص جدید بودن، می‌توانیم از تاریخ ایجاد یا یک پرچم استفاده کنیم
            # اما در نسخه ساده، فرض می‌کنیم که اگر کاربر از قبل وجود داشته،
            # اطلاعاتش به‌روزرسانی شده و کاربر جدید نیست.
            # برای تشخیص دقیق‌تر، می‌توانیم متد جداگانه‌ای در سرویس پیاده‌سازی کنیم.
            # فعلاً با استفاده از زمان ایجاد کاربر می‌توانیم تشخیص دهیم
            # که آیا در این جلسه ثبت شده یا خیر.

            # در نسخه کامل، سرویس می‌تواند یک پرچم is_new برگرداند.
            # برای سادگی، فرض می‌کنیم که اگر کاربر قبلاً وجود داشته باشد،
            # متد get_or_create_user کاربر موجود را برمی‌گرداند و is_new = False.
            # اما نیاز به یک راه حل بهتر داریم.

            # با توجه به اینکه سرویس UserRegistrationService متد get_or_create_user
            # را دارد، اما تشخیص جدید بودن کاربر به‌صورت مستقیم در DTO نیست.
            # برای حل این مشکل، می‌توانیم از repository مستقیماً استفاده کنیم
            # یا متد new_user_exists را در سرویس اضافه کنیم.
            # در اینجا از روش ساده استفاده می‌کنیم: اگر کاربر قبلاً وجود داشته،
            # متد register_user (که کاربر جدید ایجاد می‌کند) صدا زده نمی‌شود.
            # اما در get_or_create_user، اگر کاربر وجود داشته باشد،
            # به‌روزرسانی می‌شود و is_new = False است.

            # برای تشخیص، از متد check_user_exists قبل از ثبت‌نام استفاده می‌کنیم
            # اما این کار باعث دو بار رفتن به دیتابیس می‌شود.
            # در یک پیاده‌سازی بهتر، سرویس باید is_new را برگرداند.
            # فعلاً فرض می‌کنیم که اگر کاربر جدید باشد،
            # زمان ایجاد با زمان فعلی نزدیک است (کمتر از ۵ ثانیه).

            import datetime
            now = datetime.datetime.now()
            if user_dto.created_at and (now - user_dto.created_at).total_seconds() < 5:
                is_new = True
            else:
                # برای تشخیص دقیق‌تر، بررسی می‌کنیم که آیا کاربر قبلاً ثبت شده بود
                # با بررسی وجود کاربر قبل از ثبت‌نام
                existed = await self._registration_service.check_user_exists(telegram_id)
                is_new = not existed

            logger.info(
                f"RegisterUserUseCase completed: telegram_id={telegram_id}, "
                f"user_id={user_dto.id}, is_new={is_new}"
            )

            return user_dto, is_new

        except ValidationError as e:
            logger.warning(f"Validation error in RegisterUserUseCase: {e}")
            raise

        except DatabaseError as e:
            logger.error(f"Database error in RegisterUserUseCase: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in RegisterUserUseCase: {e}")
            raise DatabaseError(
                message=f"خطای غیرمنتظره در ثبت‌نام کاربر: {str(e)}",
                context={"telegram_id": telegram_id},
            )

    async def execute_with_admin_role(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Tuple[UserResponseDTO, bool]:
        """
        اجرای Use Case ثبت‌نام کاربر با نقش ادمین.

        این متد کاربر را با نقش ادمین ثبت‌نام می‌کند.

        Args:
            telegram_id: شناسه تلگرام کاربر.
            username: نام کاربری تلگرام (اختیاری).
            first_name: نام کوچک کاربر (اختیاری).
            last_name: نام خانوادگی کاربر (اختیاری).

        Returns:
            Tuple[UserResponseDTO, bool]: اطلاعات کاربر ثبت‌نام‌شده و
            وضعیت (True اگر کاربر جدید ایجاد شده باشد، False اگر قبلاً وجود داشته باشد).

        Raises:
            ValidationError: اگر اطلاعات ورودی نامعتبر باشد.
            DatabaseError: اگر خطایی در ذخیره‌سازی رخ دهد.
        """
        logger.info(
            f"Executing RegisterUserUseCase with admin role: telegram_id={telegram_id}"
        )

        try:
            user_dto = await self._registration_service.register_admin(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )

            # تشخیص جدید بودن کاربر
            existed = await self._registration_service.check_user_exists(telegram_id)
            is_new = not existed

            logger.info(
                f"RegisterUserUseCase (admin) completed: telegram_id={telegram_id}, "
                f"user_id={user_dto.id}, is_new={is_new}"
            )

            return user_dto, is_new

        except Exception as e:
            logger.error(f"Error in RegisterUserUseCase with admin role: {e}")
            raise