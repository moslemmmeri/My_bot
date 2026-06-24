# my_bot_project/src/my_bot/application/services/user/user_profile.py
"""
سرویس پروفایل کاربر (User Profile Service).

این سرویس مسئولیت مدیریت پروفایل کاربران را بر عهده دارد و شامل
عملیات‌های دریافت، به‌روزرسانی و نمایش اطلاعات کاربر است.
"""

from typing import Optional, List

from my_bot.application.dtos.user_dto import UserProfileDTO, UserUpdateDTO, UserResponseDTO
from my_bot.application.dtos.order_dto import OrderResponseDTO
from my_bot.core.exceptions.not_found_errors import UserNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.user import User
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.payment_repository import PaymentRepository
from my_bot.domain.value_objects.email import Email
from my_bot.domain.value_objects.phone import Phone

logger = get_logger(__name__)


class UserProfileService:
    """
    سرویس مدیریت پروفایل کاربر.

    این کلاس مسئولیت دریافت، به‌روزرسانی و نمایش اطلاعات پروفایل کاربران را بر عهده دارد.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        order_repository: Optional[OrderRepository] = None,
        payment_repository: Optional[PaymentRepository] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس پروفایل.

        Args:
            user_repository: ریپازیتوری کاربر.
            order_repository: ریپازیتوری سفارش (اختیاری).
            payment_repository: ریپازیتوری پرداخت (اختیاری).
        """
        self._user_repository = user_repository
        self._order_repository = order_repository
        self._payment_repository = payment_repository

    async def get_profile(self, user_id: int) -> UserProfileDTO:
        """
        دریافت پروفایل کامل یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            UserProfileDTO: اطلاعات کامل پروفایل کاربر.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # دریافت آمار کاربر
        stats = await self._get_user_stats(user_id)

        return UserProfileDTO.from_entity(user, stats)

    async def get_profile_by_telegram_id(self, telegram_id: int) -> UserProfileDTO:
        """
        دریافت پروفایل کامل یک کاربر با شناسه تلگرام.

        Args:
            telegram_id: شناسه تلگرام کاربر.

        Returns:
            UserProfileDTO: اطلاعات کامل پروفایل کاربر.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_telegram_id(telegram_id)
        if not user:
            raise UserNotFoundError(telegram_id=telegram_id)

        stats = await self._get_user_stats(user.id or 0)
        return UserProfileDTO.from_entity(user, stats)

    async def update_profile(self, user_id: int, data: UserUpdateDTO) -> UserResponseDTO:
        """
        به‌روزرسانی اطلاعات پروفایل کاربر.

        Args:
            user_id: شناسه کاربر.
            data: داده‌های جدید برای به‌روزرسانی.

        Returns:
            UserResponseDTO: اطلاعات به‌روزرسانی‌شده کاربر.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
            ValidationError: اگر داده‌ها نامعتبر باشند.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # اعتبارسنجی و به‌روزرسانی فیلدها
        updated = False

        if data.first_name is not None:
            user.first_name = data.first_name
            updated = True

        if data.last_name is not None:
            user.last_name = data.last_name
            updated = True

        if data.username is not None:
            user.username = data.username
            updated = True

        if data.phone_number is not None:
            # اعتبارسنجی شماره تلفن
            if data.phone_number:
                try:
                    Phone(data.phone_number)
                except ValidationError as e:
                    raise ValidationError(
                        message=f"شماره تلفن نامعتبر: {e.message}",
                        context={"user_id": user_id, "phone": data.phone_number},
                    )
            user.phone_number = data.phone_number
            updated = True

        if data.email is not None:
            # اعتبارسنجی ایمیل
            if data.email:
                try:
                    Email(data.email)
                except ValidationError as e:
                    raise ValidationError(
                        message=f"ایمیل نامعتبر: {e.message}",
                        context={"user_id": user_id, "email": data.email},
                    )
            user.email = data.email
            updated = True

        if not updated:
            logger.debug(f"No changes to update for user {user_id}")
            return UserResponseDTO.from_entity(user)

        # ذخیره تغییرات
        saved_user = await self._user_repository.save(user)
        logger.info(f"Profile updated for user {user_id}")
        return UserResponseDTO.from_entity(saved_user)

    async def update_phone(self, user_id: int, phone_number: str) -> UserResponseDTO:
        """
        به‌روزرسانی شماره تلفن کاربر.

        Args:
            user_id: شناسه کاربر.
            phone_number: شماره تلفن جدید.

        Returns:
            UserResponseDTO: اطلاعات به‌روزرسانی‌شده کاربر.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
            ValidationError: اگر شماره تلفن نامعتبر باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # اعتبارسنجی شماره تلفن
        if phone_number:
            try:
                Phone(phone_number)
            except ValidationError as e:
                raise ValidationError(
                    message=f"شماره تلفن نامعتبر: {e.message}",
                    context={"user_id": user_id, "phone": phone_number},
                )

        user.phone_number = phone_number
        saved_user = await self._user_repository.save(user)
        logger.info(f"Phone updated for user {user_id}")
        return UserResponseDTO.from_entity(saved_user)

    async def update_email(self, user_id: int, email: str) -> UserResponseDTO:
        """
        به‌روزرسانی ایمیل کاربر.

        Args:
            user_id: شناسه کاربر.
            email: ایمیل جدید.

        Returns:
            UserResponseDTO: اطلاعات به‌روزرسانی‌شده کاربر.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
            ValidationError: اگر ایمیل نامعتبر باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # اعتبارسنجی ایمیل
        if email:
            try:
                Email(email)
            except ValidationError as e:
                raise ValidationError(
                    message=f"ایمیل نامعتبر: {e.message}",
                    context={"user_id": user_id, "email": email},
                )

        user.email = email
        saved_user = await self._user_repository.save(user)
        logger.info(f"Email updated for user {user_id}")
        return UserResponseDTO.from_entity(saved_user)

    async def get_user_orders(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> List[OrderResponseDTO]:
        """
        دریافت تاریخچه سفارشات کاربر.

        Args:
            user_id: شناسه کاربر.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[OrderResponseDTO]: لیست سفارشات کاربر.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        if not self._order_repository:
            raise ValueError("Order repository not available")

        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        orders = await self._order_repository.get_by_user_id(user_id, skip=skip, limit=limit)
        return [OrderResponseDTO.from_entity(order) for order in orders]

    async def get_user_stats(self, user_id: int) -> dict:
        """
        دریافت آمار کاربر (تعداد سفارشات، مجموع پرداخت‌ها، و ...).

        Args:
            user_id: شناسه کاربر.

        Returns:
            dict: آمار کاربر.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        return await self._get_user_stats(user_id)

    async def _get_user_stats(self, user_id: int) -> dict:
        """
        دریافت آمار کاربر (داخلی).

        Args:
            user_id: شناسه کاربر.

        Returns:
            dict: آمار کاربر.
        """
        stats = {
            "total_orders": 0,
            "total_spent": 0,
            "average_order_value": 0,
            "last_order_date": None,
            "points": 0,
            "level": "bronze",
        }

        if self._order_repository:
            # تعداد سفارشات
            stats["total_orders"] = await self._order_repository.get_order_count_by_user(user_id)

            # آخرین سفارش
            last_order = await self._order_repository.get_last_order_by_user(user_id)
            if last_order:
                stats["last_order_date"] = last_order.created_at.isoformat() if last_order.created_at else None

        if self._payment_repository:
            # مجموع پرداخت‌ها
            total_spent = await self._payment_repository.get_total_amount_by_user(user_id)
            stats["total_spent"] = total_spent.amount if total_spent else 0

        # امتیاز و سطح از کاربر
        user = await self._user_repository.get_by_id(user_id)
        if user:
            stats["points"] = user.points
            stats["level"] = user.level.value if user.level else "bronze"

        return stats