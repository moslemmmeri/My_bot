# my_bot_project/src/my_bot/infrastructure/external/sms/kavenegar.py
"""
سرویس ارسال پیامک کاوه‌نگار (Kavenegar SMS).

این کلاس مسئولیت ارسال پیامک‌ها از طریق سرویس کاوه‌نگار را بر عهده دارد.
با استفاده از API کاوه‌نگار، پیامک‌های تکی و گروهی را ارسال می‌کند.
"""

import asyncio
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode

import aiohttp
from aiohttp import ClientTimeout

from my_bot.core.exceptions.external_errors import SMSServiceError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class KavenegarSMS:
    """
    سرویس ارسال پیامک کاوه‌نگار.

    این کلاس با استفاده از API کاوه‌نگار، پیامک‌ها را ارسال می‌کند.

    Attributes:
        api_key: کلید API کاوه‌نگار.
        sender: شماره فرستنده (خطوط خدمات‌پیام‌کوتاه).
        timeout: زمان timeout بر حسب ثانیه.
        base_url: آدرس پایه API کاوه‌نگار.
        _session: نشست HTTP (برای reuse اتصالات).
    """

    def __init__(
        self,
        api_key: str,
        sender: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        """
        مقداردهی اولیه سرویس کاوه‌نگار.

        Args:
            api_key: کلید API کاوه‌نگار.
            sender: شماره فرستنده (اختیاری).
            timeout: زمان timeout بر حسب ثانیه (پیش‌فرض ۳۰).
        """
        self.api_key = api_key
        self.sender = sender
        self.timeout = ClientTimeout(total=timeout)
        self.base_url = "https://api.kavenegar.com/v1"
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info(
            f"KavenegarSMS initialized: sender={sender}, "
            f"api_key={api_key[:4]}***"
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        دریافت یا ایجاد نشست HTTP.

        Returns:
            aiohttp.ClientSession: نشست HTTP.
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        ارسال درخواست به API کاوه‌نگار.

        Args:
            method: متد HTTP (GET, POST).
            endpoint: نقطه پایان API.
            params: پارامترهای URL (اختیاری).
            data: داده‌های POST (اختیاری).

        Returns:
            Dict[str, Any]: پاسخ API.

        Raises:
            SMSServiceError: در صورت بروز خطا در API.
        """
        session = await self._get_session()

        # ساخت URL کامل
        url = f"{self.base_url}/{self.api_key}/{endpoint}.json"

        # اضافه کردن پارامترها
        if params:
            url = f"{url}?{urlencode(params)}"

        try:
            async with session.request(
                method=method,
                url=url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                result = await response.json()

                # بررسی پاسخ API
                if response.status != 200:
                    error_message = result.get("return", {}).get("message", "خطای ناشناخته")
                    error_code = result.get("return", {}).get("status")
                    logger.error(
                        f"Kavenegar API error: status={response.status}, "
                        f"code={error_code}, message={error_message}"
                    )
                    raise SMSServiceError(
                        message=f"خطا در API کاوه‌نگار: {error_message}",
                        context={
                            "status_code": response.status,
                            "error_code": error_code,
                            "endpoint": endpoint,
                        },
                    )

                return result

        except aiohttp.ClientError as e:
            logger.error(f"Network error connecting to Kavenegar: {e}")
            raise SMSServiceError(
                message="خطا در ارتباط با سرویس کاوه‌نگار.",
                context={"error": str(e)},
            )
        except Exception as e:
            logger.error(f"Unexpected error in Kavenegar request: {e}")
            raise SMSServiceError(
                message=f"خطای غیرمنتظره در درخواست به کاوه‌نگار: {str(e)}",
                context={"error": str(e)},
            )

    async def send_sms(
        self,
        receptor: str,
        message: str,
        sender: Optional[str] = None,
        date: Optional[str] = None,
        type: str = "0",
    ) -> Dict[str, Any]:
        """
        ارسال یک پیامک به یک گیرنده.

        Args:
            receptor: شماره گیرنده (با فرمت 09xxxxxxxxx).
            message: متن پیامک.
            sender: شماره فرستنده (اختیاری).
            date: تاریخ ارسال (اختیاری، فرمت timestamp).
            type: نوع پیام (0: عادی، 1: تبلیغاتی) (پیش‌فرض 0).

        Returns:
            Dict[str, Any]: پاسخ API شامل اطلاعات ارسال.

        Raises:
            SMSServiceError: در صورت بروز خطا در ارسال.
        """
        params = {
            "receptor": receptor,
            "message": message,
            "sender": sender or self.sender,
            "type": type,
        }
        if date:
            params["date"] = date

        # حذف پارامترهای None
        params = {k: v for k, v in params.items() if v is not None}

        if not params.get("sender"):
            raise SMSServiceError(
                message="شماره فرستنده مشخص نشده است.",
                context={"receptor": receptor},
            )

        logger.info(f"Sending SMS: receptor={receptor}, message_len={len(message)}")

        try:
            result = await self._request("POST", "sms/send", data=params)
            logger.info(f"SMS sent successfully to {receptor}")
            return result

        except SMSServiceError:
            raise
        except Exception as e:
            logger.error(f"Error sending SMS to {receptor}: {e}")
            raise SMSServiceError(
                message=f"خطا در ارسال پیامک به {receptor}: {str(e)}",
                context={"receptor": receptor, "error": str(e)},
            )

    async def send_bulk(
        self,
        receptors: List[str],
        message: str,
        sender: Optional[str] = None,
        date: Optional[str] = None,
        type: str = "0",
    ) -> Dict[str, Any]:
        """
        ارسال یک پیامک به چندین گیرنده.

        Args:
            receptors: لیست شماره‌های گیرنده.
            message: متن پیامک.
            sender: شماره فرستنده (اختیاری).
            date: تاریخ ارسال (اختیاری).
            type: نوع پیام (پیش‌فرض 0).

        Returns:
            Dict[str, Any]: پاسخ API شامل اطلاعات ارسال.

        Raises:
            SMSServiceError: در صورت بروز خطا در ارسال.
        """
        if not receptors:
            raise SMSServiceError(
                message="حداقل یک گیرنده باید مشخص شود.",
                context={},
            )

        # تبدیل لیست به رشته با کاما
        receptor_str = ",".join(receptors)

        params = {
            "receptor": receptor_str,
            "message": message,
            "sender": sender or self.sender,
            "type": type,
        }
        if date:
            params["date"] = date

        # حذف پارامترهای None
        params = {k: v for k, v in params.items() if v is not None}

        if not params.get("sender"):
            raise SMSServiceError(
                message="شماره فرستنده مشخص نشده است.",
                context={"receptors_count": len(receptors)},
            )

        logger.info(f"Sending bulk SMS: {len(receptors)} receptors")

        try:
            result = await self._request("POST", "sms/sendarray", data=params)
            logger.info(f"Bulk SMS sent to {len(receptors)} receptors")
            return result

        except SMSServiceError:
            raise
        except Exception as e:
            logger.error(f"Error sending bulk SMS: {e}")
            raise SMSServiceError(
                message=f"خطا در ارسال پیامک گروهی: {str(e)}",
                context={"receptors_count": len(receptors), "error": str(e)},
            )

    async def send_otp(
        self,
        receptor: str,
        template: str,
        token: str,
        token2: Optional[str] = None,
        token3: Optional[str] = None,
        token4: Optional[str] = None,
        token5: Optional[str] = None,
        token6: Optional[str] = None,
        token7: Optional[str] = None,
        token8: Optional[str] = None,
        token9: Optional[str] = None,
        token10: Optional[str] = None,
        sender: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        ارسال پیامک با قالب (برای OTP و کدهای تأیید).

        Args:
            receptor: شماره گیرنده.
            template: نام قالب در کاوه‌نگار.
            token: توکن اول.
            token2: توکن دوم (اختیاری).
            token3: توکن سوم (اختیاری).
            token4: توکن چهارم (اختیاری).
            token5: توکن پنجم (اختیاری).
            token6: توکن ششم (اختیاری).
            token7: توکن هفتم (اختیاری).
            token8: توکن هشتم (اختیاری).
            token9: توکن نهم (اختیاری).
            token10: توکن دهم (اختیاری).
            sender: شماره فرستنده (اختیاری).

        Returns:
            Dict[str, Any]: پاسخ API شامل اطلاعات ارسال.

        Raises:
            SMSServiceError: در صورت بروز خطا در ارسال.
        """
        params = {
            "receptor": receptor,
            "template": template,
            "token": token,
            "sender": sender or self.sender,
        }

        # اضافه کردن توکن‌های اضافی
        tokens = {
            "token2": token2,
            "token3": token3,
            "token4": token4,
            "token5": token5,
            "token6": token6,
            "token7": token7,
            "token8": token8,
            "token9": token9,
            "token10": token10,
        }
        for key, value in tokens.items():
            if value is not None:
                params[key] = value

        # حذف پارامترهای None
        params = {k: v for k, v in params.items() if v is not None}

        if not params.get("sender"):
            raise SMSServiceError(
                message="شماره فرستنده مشخص نشده است.",
                context={"receptor": receptor},
            )

        logger.info(f"Sending OTP SMS: receptor={receptor}, template={template}")

        try:
            result = await self._request("POST", "verify/lookup", data=params)
            logger.info(f"OTP SMS sent to {receptor}")
            return result

        except SMSServiceError:
            raise
        except Exception as e:
            logger.error(f"Error sending OTP SMS to {receptor}: {e}")
            raise SMSServiceError(
                message=f"خطا در ارسال پیامک OTP به {receptor}: {str(e)}",
                context={"receptor": receptor, "error": str(e)},
            )

    async def get_status(self, message_id: str) -> Dict[str, Any]:
        """
        دریافت وضعیت یک پیامک.

        Args:
            message_id: شناسه پیامک (از پاسخ ارسال).

        Returns:
            Dict[str, Any]: وضعیت پیامک.

        Raises:
            SMSServiceError: در صورت بروز خطا در API.
        """
        try:
            result = await self._request("GET", f"sms/status/{message_id}")
            logger.debug(f"Get SMS status: message_id={message_id}")
            return result

        except SMSServiceError:
            raise
        except Exception as e:
            logger.error(f"Error getting SMS status: {e}")
            raise SMSServiceError(
                message=f"خطا در دریافت وضعیت پیامک: {str(e)}",
                context={"message_id": message_id, "error": str(e)},
            )

    async def get_remaining_credit(self) -> int:
        """
        دریافت اعتبار باقی‌مانده حساب کاوه‌نگار.

        Returns:
            int: اعتبار باقی‌مانده (به ریال).

        Raises:
            SMSServiceError: در صورت بروز خطا در API.
        """
        try:
            result = await self._request("GET", "account/info")
            credit = result.get("entries", [{}])[0].get("credit", 0)
            logger.debug(f"Remaining credit: {credit} Rials")
            return credit

        except SMSServiceError:
            raise
        except Exception as e:
            logger.error(f"Error getting remaining credit: {e}")
            raise SMSServiceError(
                message=f"خطا در دریافت اعتبار باقی‌مانده: {str(e)}",
                context={"error": str(e)},
            )

    async def close(self) -> None:
        """
        بستن نشست HTTP.
        """
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.info("KavenegarSMS session closed.")

    async def health_check(self) -> bool:
        """
        بررسی سلامت سرویس کاوه‌نگار.

        Returns:
            bool: True اگر سرویس سالم باشد.
        """
        try:
            # بررسی با دریافت اعتبار
            await self.get_remaining_credit()
            return True
        except Exception as e:
            logger.warning(f"Kavenegar health check failed: {e}")
            return False