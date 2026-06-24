# my_bot_project/src/my_bot/application/use_cases/payment/initiate_payment.py
"""
موارد استفاده شروع پرداخت (Initiate Payment Use Case).

این Use Case مسئولیت شروع فرآیند پرداخت را بر عهده دارد.
با دریافت اطلاعات پرداخت، تراکنش را ثبت کرده و لینک پرداخت را از درگاه دریافت می‌کند.
"""

from typing import Optional, Dict, Any

from my_bot.application.dtos.payment_dto import (
    PaymentCreateDTO,
    PaymentResponseDTO,
    PaymentGatewayResponseDTO,
)
from my_bot.application.services.payment.payment_gateway import PaymentGatewayService
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.core.exceptions.not_found_errors import UserNotFoundError, OrderNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.payment_errors import PaymentGatewayError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.payment import Payment
from my_bot.domain.interfaces.repositories.payment_repository import PaymentRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.value_objects.money import Money

logger = get_logger(__name__)


class InitiatePaymentUseCase:
    """
    Use Case شروع پرداخت.

    این کلاس مسئولیت شروع فرآیند پرداخت را بر عهده دارد.
    """

    def __init__(
        self,
        payment_repository: PaymentRepository,
        user_repository: UserRepository,
        order_repository: Optional[OrderRepository] = None,
        gateway_service: Optional[PaymentGatewayService] = None,
    ) -> None:
        """
        مقداردهی اولیه Use Case شروع پرداخت.

        Args:
            payment_repository: ریپازیتوری پرداخت.
            user_repository: ریپازیتوری کاربر.
            order_repository: ریپازیتوری سفارش (اختیاری).
            gateway_service: سرویس درگاه پرداخت (اختیاری).
        """
        self._payment_repository = payment_repository
        self._user_repository = user_repository
        self._order_repository = order_repository
        self._gateway_service = gateway_service

    async def execute(
        self,
        user_id: int,
        amount: float,
        currency: str = "IRR",
        order_id: Optional[str] = None,
        description: Optional[str] = None,
        callback_url: Optional[str] = None,
        gateway: str = "mock",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        اجرای Use Case شروع پرداخت.

        Args:
            user_id: شناسه کاربر پرداخت‌کننده.
            amount: مبلغ پرداختی.
            currency: واحد پول (پیش‌فرض: IRR).
            order_id: شناسه سفارش مرتبط (اختیاری).
            description: توضیحات پرداخت (اختیاری).
            callback_url: آدرس بازگشت پس از پرداخت (اختیاری).
            gateway: نام درگاه پرداخت (پیش‌فرض: mock).
            metadata: داده‌های اضافی (اختیاری).

        Returns:
            Dict[str, Any]: نتیجه پرداخت شامل:
                - payment: اطلاعات پرداخت ثبت‌شده
                - payment_url: لینک پرداخت
                - transaction_id: شناسه تراکنش در درگاه

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
            OrderNotFoundError: اگر سفارش وجود نداشته باشد (در صورت مشخص شدن order_id).
            ValidationError: اگر داده‌ها نامعتبر باشند.
            PaymentGatewayError: اگر خطایی در درگاه پرداخت رخ دهد.
            DatabaseError: اگر خطایی در ذخیره‌سازی رخ دهد.
        """
        logger.info(
            f"Executing InitiatePaymentUseCase: user_id={user_id}, "
            f"amount={amount}, currency={currency}, order_id={order_id}"
        )

        # اعتبارسنجی اولیه
        if user_id <= 0:
            raise ValidationError(
                message="شناسه کاربر باید یک عدد مثبت باشد.",
                context={"user_id": user_id},
            )

        if amount <= 0:
            raise ValidationError(
                message="مبلغ پرداخت باید مثبت باشد.",
                context={"amount": amount},
            )

        try:
            # بررسی وجود کاربر
            user = await self._user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(user_id=user_id)

            # بررسی وجود سفارش (در صورت مشخص شدن)
            if order_id and self._order_repository:
                order = await self._order_repository.get_by_id(int(order_id))
                if not order:
                    raise OrderNotFoundError(order_id=order_id)

                # بررسی مالکیت سفارش
                if order.user_id != user_id:
                    raise ValidationError(
                        message="شما مالک این سفارش نیستید.",
                        context={"order_id": order_id, "user_id": user_id},
                    )

                # بررسی وضعیت سفارش (فقط سفارشات در انتظار پرداخت قابل پرداخت هستند)
                if order.status.value != "pending":
                    raise ValidationError(
                        message="فقط سفارشات در انتظار پرداخت قابل پرداخت هستند.",
                        context={"order_id": order_id, "status": order.status.value},
                    )

            # تبدیل مبلغ به Money
            money_amount = Money(amount, currency)

            # ایجاد DTO پرداخت
            payment_dto = PaymentCreateDTO(
                user_id=user_id,
                order_id=order_id,
                amount=float(money_amount.amount),
                currency=currency,
                gateway=gateway,
                description=description,
                callback_url=callback_url,
                metadata=metadata or {},
            )

            # ایجاد موجودیت پرداخت
            payment = Payment(
                user_id=payment_dto.user_id,
                amount=money_amount,
                order_id=payment_dto.order_id,
                currency=payment_dto.currency,
                gateway=payment_dto.gateway,
                description=payment_dto.description,
                metadata=payment_dto.metadata,
            )

            # ذخیره پرداخت در دیتابیس
            saved_payment = await self._payment_repository.save(payment)

            logger.info(f"Payment record created: payment_id={saved_payment.id}")

            # اگر سرویس درگاه پرداخت وجود دارد، پرداخت را به درگاه ارسال می‌کنیم
            payment_url = None
            transaction_id = None
            gateway_response = None

            if self._gateway_service:
                try:
                    # استفاده از callback_url از DTO یا مقدار پیش‌فرض
                    callback = callback_url or "https://example.com/payment/callback"

                    # شروع پرداخت در درگاه
                    gateway_response = await self._gateway_service.initiate_payment(
                        payment=saved_payment,
                        callback_url=callback,
                        gateway_name=gateway,
                    )

                    if gateway_response.success:
                        payment_url = gateway_response.payment_url
                        transaction_id = gateway_response.transaction_id

                        # به‌روزرسانی پرداخت با اطلاعات درگاه
                        saved_payment.transaction_id = transaction_id
                        if gateway_response.reference_id:
                            saved_payment.reference_id = gateway_response.reference_id
                        saved_payment.metadata["gateway_response"] = gateway_response.gateway_data

                        # ذخیره مجدد
                        saved_payment = await self._payment_repository.save(saved_payment)

                        logger.info(
                            f"Payment sent to gateway: payment_id={saved_payment.id}, "
                            f"transaction_id={transaction_id}"
                        )
                    else:
                        # اگر درگاه با خطا مواجه شد، پرداخت را ناموفق علامت بزن
                        saved_payment.mark_as_failed(
                            gateway_response.message or "Payment initiation failed"
                        )
                        saved_payment = await self._payment_repository.save(saved_payment)

                        raise PaymentGatewayError(
                            message=gateway_response.message or "شروع پرداخت در درگاه ناموفق بود.",
                            context={"payment_id": saved_payment.id},
                        )

                except PaymentGatewayError as e:
                    # پرداخت را ناموفق علامت بزن
                    saved_payment.mark_as_failed(str(e))
                    await self._payment_repository.save(saved_payment)
                    raise

                except Exception as e:
                    logger.error(f"Gateway error in InitiatePaymentUseCase: {e}")
                    saved_payment.mark_as_failed(f"Gateway error: {str(e)}")
                    await self._payment_repository.save(saved_payment)
                    raise PaymentGatewayError(
                        message=f"خطا در ارتباط با درگاه پرداخت: {str(e)}",
                        context={"payment_id": saved_payment.id},
                    )

            else:
                # اگر سرویس درگاه وجود نداشت، فقط پرداخت را ثبت می‌کنیم
                logger.warning("Payment gateway service not available. Payment recorded without gateway.")
                # در این حالت، لینک پرداخت شبیه‌سازی می‌شود
                payment_url = f"https://mock-payment.com/pay/{saved_payment.id}"
                transaction_id = f"mock_{saved_payment.id}"

            # نتیجه نهایی
            result = {
                "payment": PaymentResponseDTO.from_entity(saved_payment).model_dump(),
                "payment_url": payment_url,
                "transaction_id": transaction_id,
                "gateway_response": gateway_response.gateway_data if gateway_response else None,
            }

            logger.info(
                f"InitiatePaymentUseCase completed: payment_id={saved_payment.id}, "
                f"transaction_id={transaction_id}"
            )

            return result

        except UserNotFoundError as e:
            logger.warning(f"User not found in InitiatePaymentUseCase: {e}")
            raise

        except OrderNotFoundError as e:
            logger.warning(f"Order not found in InitiatePaymentUseCase: {e}")
            raise

        except ValidationError as e:
            logger.warning(f"Validation error in InitiatePaymentUseCase: {e}")
            raise

        except PaymentGatewayError as e:
            logger.error(f"Gateway error in InitiatePaymentUseCase: {e}")
            raise

        except DatabaseError as e:
            logger.error(f"Database error in InitiatePaymentUseCase: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in InitiatePaymentUseCase: {e}")
            raise DatabaseError(
                message=f"خطای غیرمنتظره در شروع پرداخت: {str(e)}",
                context={"user_id": user_id, "amount": amount},
            )

    async def execute_for_order(
        self,
        order_id: int,
        user_id: int,
        gateway: str = "mock",
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        شروع پرداخت برای یک سفارش خاص.

        این متد مبلغ را از سفارش دریافت می‌کند و نیازی به مشخص کردن مبلغ نیست.

        Args:
            order_id: شناسه سفارش.
            user_id: شناسه کاربر.
            gateway: نام درگاه پرداخت.
            callback_url: آدرس بازگشت (اختیاری).

        Returns:
            Dict[str, Any]: نتیجه پرداخت.
        """
        logger.info(f"Executing InitiatePaymentUseCase for order: order_id={order_id}")

        # بررسی وجود سفارش
        if not self._order_repository:
            raise ValidationError(
                message="سرویس سفارش در دسترس نیست.",
                context={"order_id": order_id},
            )

        order = await self._order_repository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(order_id=order_id)

        # بررسی مالکیت
        if order.user_id != user_id:
            raise ValidationError(
                message="شما مالک این سفارش نیستید.",
                context={"order_id": order_id, "user_id": user_id},
            )

        # دریافت مبلغ از سفارش
        amount = float(order.total_amount.amount)
        currency = order.total_amount.currency

        # دریافت توضیحات
        description = f"پرداخت سفارش #{order.order_number}"

        return await self.execute(
            user_id=user_id,
            amount=amount,
            currency=currency,
            order_id=str(order_id),
            description=description,
            callback_url=callback_url,
            gateway=gateway,
            metadata={"order_number": order.order_number},
        )