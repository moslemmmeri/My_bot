# my_bot_project/src/my_bot/core/constants/form_types.py
"""
ثابت‌های مربوط به انواع فرم‌ها (Form Types).

این ماژول شامل Enum انواع فرم‌های قابل استفاده در سیستم است که
برای دسته‌بندی فرم‌ها، اعمال قوانین خاص و نمایش مناسب به کاربران استفاده می‌شود.
"""

from enum import Enum
from typing import Optional


class FormType(str, Enum):
    """
    انواع فرم‌های قابل استفاده در سیستم.

    هر نوع فرم دارای ویژگی‌ها، قوانین و رفتارهای خاص خود است.

    Attributes:
        SURVEY: فرم نظرخواهی (نظرسنجی)
        REGISTRATION: فرم ثبت‌نام (عضویت در دوره، رویداد و ...)
        ORDER: فرم سفارش (ثبت سفارش محصول یا خدمات)
        FEEDBACK: فرم بازخورد (نظرات و پیشنهادات)
        CONTACT: فرم تماس با ما (ارتباط با پشتیبانی)
        TICKET: فرم تیکت پشتیبانی (ثبت درخواست پشتیبانی)
        CUSTOM: فرم سفارشی (تعریف شده توسط ادمین)
        APPLICATION: فرم درخواست (استخدام، همکاری و ...)
        RESERVATION: فرم رزرو (رزرو زمان، نوبت و ...)
        REGISTRATION_EVENT: فرم ثبت‌نام رویداد (خاص رویدادها)
        COMPLAINT: فرم شکایت (ثبت شکایت و پیگیری)
        SUGGESTION: فرم پیشنهاد (ارائه ایده و پیشنهاد)
    """

    SURVEY = "survey"
    REGISTRATION = "registration"
    ORDER = "order"
    FEEDBACK = "feedback"
    CONTACT = "contact"
    TICKET = "ticket"
    CUSTOM = "custom"
    APPLICATION = "application"
    RESERVATION = "reservation"
    REGISTRATION_EVENT = "registration_event"
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"

    @classmethod
    def from_string(cls, value: str) -> Optional["FormType"]:
        """
        تبدیل یک رشته به نوع فرم.

        Args:
            value: رشته‌ای که نمایانگر نوع فرم است.

        Returns:
            نوع فرم متناظر با رشته داده شده، یا None در صورت عدم تطابق.
        """
        try:
            return cls(value.lower())
        except ValueError:
            return None

    def get_display_name(self) -> str:
        """
        دریافت نام نمایشی نوع فرم (به فارسی).

        Returns:
            نام نمایشی نوع فرم.
        """
        display_names = {
            FormType.SURVEY: "نظرسنجی",
            FormType.REGISTRATION: "ثبت‌نام",
            FormType.ORDER: "سفارش",
            FormType.FEEDBACK: "بازخورد",
            FormType.CONTACT: "تماس با ما",
            FormType.TICKET: "تیکت پشتیبانی",
            FormType.CUSTOM: "فرم سفارشی",
            FormType.APPLICATION: "درخواست همکاری",
            FormType.RESERVATION: "رزرو",
            FormType.REGISTRATION_EVENT: "ثبت‌نام رویداد",
            FormType.COMPLAINT: "شکایت",
            FormType.SUGGESTION: "پیشنهاد",
        }
        return display_names.get(self, self.value)

    def get_emoji(self) -> str:
        """
        دریافت ایموجی متناسب با نوع فرم.

        Returns:
            ایموجی نمایشی برای نوع فرم.
        """
        emojis = {
            FormType.SURVEY: "📊",
            FormType.REGISTRATION: "📝",
            FormType.ORDER: "🛒",
            FormType.FEEDBACK: "💬",
            FormType.CONTACT: "📞",
            FormType.TICKET: "🎫",
            FormType.CUSTOM: "⚙️",
            FormType.APPLICATION: "👔",
            FormType.RESERVATION: "📅",
            FormType.REGISTRATION_EVENT: "🎪",
            FormType.COMPLAINT: "⚠️",
            FormType.SUGGESTION: "💡",
        }
        return emojis.get(self, "📋")

    def is_multistep(self) -> bool:
        """
        بررسی اینکه آیا فرم چند مرحله‌ای است.

        فرم‌های چند مرحله‌ای: ORDER, REGISTRATION, REGISTRATION_EVENT, APPLICATION
        """
        return self in (
            FormType.ORDER,
            FormType.REGISTRATION,
            FormType.REGISTRATION_EVENT,
            FormType.APPLICATION,
        )

    def requires_payment(self) -> bool:
        """
        بررسی اینکه آیا فرم نیاز به پرداخت دارد.

        فرم‌های نیازمند پرداخت: ORDER, REGISTRATION_EVENT (برخی موارد)
        """
        return self in (FormType.ORDER, FormType.REGISTRATION_EVENT)

    def is_public(self) -> bool:
        """
        بررسی اینکه آیا فرم عمومی است (قابل دسترسی برای همه کاربران).

        فرم‌های عمومی: SURVEY, REGISTRATION, ORDER, FEEDBACK, CONTACT, RESERVATION, SUGGESTION
        """
        return self not in (FormType.TICKET, FormType.APPLICATION, FormType.COMPLAINT)

    def requires_login(self) -> bool:
        """
        بررسی اینکه آیا فرم نیاز به لاگین دارد.

        فرم‌های نیازمند لاگین: ORDER, TICKET, APPLICATION, COMPLAINT
        """
        return self in (FormType.ORDER, FormType.TICKET, FormType.APPLICATION, FormType.COMPLAINT)

    def is_admin_defined(self) -> bool:
        """
        بررسی اینکه آیا فرم توسط ادمین تعریف شده است.

        فرم‌های تعریف شده توسط ادمین: CUSTOM, SURVEY (در برخی موارد)
        """
        return self == FormType.CUSTOM

    def get_form_structure_template(self) -> dict:
        """
        دریافت قالب ساختار فرم برای هر نوع.

        Returns:
            دیکشنری شامل فیلدهای پیشنهادی برای فرم.
        """
        templates = {
            FormType.SURVEY: {
                "fields": [
                    {"name": "question_1", "type": "text", "label": "سوال اول", "required": True},
                    {"name": "question_2", "type": "text", "label": "سوال دوم", "required": False},
                    {"name": "rating", "type": "rating", "label": "امتیاز شما", "required": True},
                ]
            },
            FormType.REGISTRATION: {
                "fields": [
                    {"name": "full_name", "type": "text", "label": "نام و نام خانوادگی", "required": True},
                    {"name": "phone", "type": "phone", "label": "شماره تماس", "required": True},
                    {"name": "email", "type": "email", "label": "ایمیل", "required": False},
                    {"name": "course", "type": "select", "label": "دوره مورد نظر", "required": True},
                ]
            },
            FormType.ORDER: {
                "fields": [
                    {"name": "product", "type": "select", "label": "محصول", "required": True},
                    {"name": "quantity", "type": "number", "label": "تعداد", "required": True},
                    {"name": "address", "type": "text", "label": "آدرس تحویل", "required": True},
                    {"name": "phone", "type": "phone", "label": "شماره تماس", "required": True},
                ]
            },
            FormType.FEEDBACK: {
                "fields": [
                    {"name": "message", "type": "textarea", "label": "متن بازخورد", "required": True},
                    {"name": "rating", "type": "rating", "label": "امتیاز", "required": True},
                    {"name": "anonymous", "type": "boolean", "label": "ارسال ناشناس", "required": False},
                ]
            },
            FormType.CONTACT: {
                "fields": [
                    {"name": "full_name", "type": "text", "label": "نام و نام خانوادگی", "required": True},
                    {"name": "phone", "type": "phone", "label": "شماره تماس", "required": True},
                    {"name": "email", "type": "email", "label": "ایمیل", "required": False},
                    {"name": "message", "type": "textarea", "label": "متن پیام", "required": True},
                ]
            },
            FormType.TICKET: {
                "fields": [
                    {"name": "subject", "type": "text", "label": "موضوع", "required": True},
                    {"name": "category", "type": "select", "label": "دسته‌بندی", "required": True},
                    {"name": "description", "type": "textarea", "label": "شرح مشکل", "required": True},
                    {"name": "priority", "type": "select", "label": "اولویت", "required": False},
                ]
            },
            FormType.APPLICATION: {
                "fields": [
                    {"name": "full_name", "type": "text", "label": "نام و نام خانوادگی", "required": True},
                    {"name": "phone", "type": "phone", "label": "شماره تماس", "required": True},
                    {"name": "email", "type": "email", "label": "ایمیل", "required": True},
                    {"name": "position", "type": "select", "label": "موقعیت شغلی", "required": True},
                    {"name": "resume", "type": "file", "label": "بارگذاری رزومه", "required": True},
                ]
            },
            FormType.RESERVATION: {
                "fields": [
                    {"name": "service", "type": "select", "label": "خدمت مورد نظر", "required": True},
                    {"name": "date", "type": "date", "label": "تاریخ", "required": True},
                    {"name": "time", "type": "time", "label": "ساعت", "required": True},
                    {"name": "phone", "type": "phone", "label": "شماره تماس", "required": True},
                ]
            },
            FormType.REGISTRATION_EVENT: {
                "fields": [
                    {"name": "full_name", "type": "text", "label": "نام و نام خانوادگی", "required": True},
                    {"name": "phone", "type": "phone", "label": "شماره تماس", "required": True},
                    {"name": "email", "type": "email", "label": "ایمیل", "required": False},
                    {"name": "event_type", "type": "select", "label": "نوع رویداد", "required": True},
                    {"name": "ticket_count", "type": "number", "label": "تعداد بلیت", "required": True},
                ]
            },
            FormType.COMPLAINT: {
                "fields": [
                    {"name": "order_id", "type": "text", "label": "شناسه سفارش", "required": False},
                    {"name": "subject", "type": "text", "label": "موضوع شکایت", "required": True},
                    {"name": "description", "type": "textarea", "label": "شرح شکایت", "required": True},
                    {"name": "attachments", "type": "file", "label": "پیوست‌ها", "required": False},
                ]
            },
            FormType.SUGGESTION: {
                "fields": [
                    {"name": "title", "type": "text", "label": "عنوان پیشنهاد", "required": True},
                    {"name": "description", "type": "textarea", "label": "شرح پیشنهاد", "required": True},
                    {"name": "anonymous", "type": "boolean", "label": "ارسال ناشناس", "required": False},
                ]
            },
            FormType.CUSTOM: {
                "fields": [
                    {"name": "field_1", "type": "text", "label": "فیلد ۱", "required": True},
                    {"name": "field_2", "type": "text", "label": "فیلد ۲", "required": False},
                ]
            },
        }
        return templates.get(self, {})

    def is_allowed_for_user(self, user_role: str) -> bool:
        """
        بررسی اینکه آیا فرم برای نقش کاربری مشخص مجاز است.

        Args:
            user_role: نقش کاربری (admin, manager, operator, user, guest)

        Returns:
            True اگر فرم برای نقش کاربری مجاز باشد.
        """
        # فرم‌های عمومی برای همه مجاز هستند
        if self.is_public():
            return True

        # فرم‌های خاص فقط برای کاربران لاگین شده
        if self.requires_login():
            return user_role not in ("guest",)

        # فرم تیکت و شکایت برای همه کاربران (به جز مهمان) مجاز است
        if self in (FormType.TICKET, FormType.COMPLAINT):
            return user_role not in ("guest",)

        # فرم درخواست همکاری برای همه مجاز است
        if self == FormType.APPLICATION:
            return True

        return False


# لیست فرم‌های عمومی (قابل دسترسی برای همه)
PUBLIC_FORMS = (
    FormType.SURVEY,
    FormType.REGISTRATION,
    FormType.ORDER,
    FormType.FEEDBACK,
    FormType.CONTACT,
    FormType.RESERVATION,
    FormType.SUGGESTION,
    FormType.APPLICATION,
)

# لیست فرم‌های نیازمند پرداخت
PAYMENT_REQUIRED_FORMS = (FormType.ORDER, FormType.REGISTRATION_EVENT)

# لیست فرم‌های نیازمند لاگین
LOGIN_REQUIRED_FORMS = (
    FormType.ORDER,
    FormType.TICKET,
    FormType.APPLICATION,
    FormType.COMPLAINT,
)

# لیست فرم‌های چند مرحله‌ای
MULTISTEP_FORMS = (
    FormType.ORDER,
    FormType.REGISTRATION,
    FormType.REGISTRATION_EVENT,
    FormType.APPLICATION,
)

# لیست فرم‌های مدیریتی (فقط ادمین)
ADMIN_ONLY_FORMS = (FormType.CUSTOM,)

# لیست فرم‌های قابل ویرایش توسط کاربر (پس از ثبت)
USER_EDITABLE_FORMS = (FormType.REGISTRATION, FormType.ORDER, FormType.RESERVATION)

# لیست فرم‌های دارای فایل پیوست
FILE_UPLOAD_FORMS = (FormType.APPLICATION, FormType.COMPLAINT)

# فرم پیش‌فرض برای استفاده در مواقعی که نوع مشخص نیست
DEFAULT_FORM_TYPE = FormType.CUSTOM


__all__ = [
    "FormType",
    "PUBLIC_FORMS",
    "PAYMENT_REQUIRED_FORMS",
    "LOGIN_REQUIRED_FORMS",
    "MULTISTEP_FORMS",
    "ADMIN_ONLY_FORMS",
    "USER_EDITABLE_FORMS",
    "FILE_UPLOAD_FORMS",
    "DEFAULT_FORM_TYPE",
]