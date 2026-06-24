# my_bot_project/src/my_bot/dynamic_forms/engine/form_renderer.py
"""
رندر فرم‌های پویا (Form Renderer).

این ماژول شامل کلاس `FormRenderer` است که مسئولیت رندر کردن فرم‌ها
در خروجی‌های مختلف (تلگرام، HTML، JSON) را بر عهده دارد.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from my_bot.core.logger.logger_setup import get_logger
from my_bot.dynamic_forms.models.form_definition import FormDefinition, FormRenderMode
from my_bot.dynamic_forms.models.form_field import DynamicFormField, FieldType

logger = get_logger(__name__)


class FormRenderer:
    """
    رندر فرم‌های پویا در خروجی‌های مختلف.

    این کلاس با استفاده از اطلاعات فرم، خروجی‌های مناسب برای نمایش
    در تلگرام، وب و سایر پلتفرم‌ها تولید می‌کند.

    Attributes:
        max_field_label_length: حداکثر طول برچسب فیلد برای نمایش.
        show_step_progress: نمایش پیشرفت مراحل (پیش‌فرض True).
        use_emoji: استفاده از ایموجی در خروجی (پیش‌فرض True).
    """

    def __init__(
        self,
        max_field_label_length: int = 50,
        show_step_progress: bool = True,
        use_emoji: bool = True,
    ) -> None:
        """
        مقداردهی اولیه FormRenderer.

        Args:
            max_field_label_length: حداکثر طول برچسب فیلد برای نمایش.
            show_step_progress: نمایش پیشرفت مراحل.
            use_emoji: استفاده از ایموجی در خروجی.
        """
        self.max_field_label_length = max_field_label_length
        self.show_step_progress = show_step_progress
        self.use_emoji = use_emoji

        logger.info(
            f"FormRenderer initialized: max_label_length={max_field_label_length}, "
            f"show_progress={show_step_progress}, use_emoji={use_emoji}"
        )

    # ==========================================
    # رندر برای تلگرام
    # ==========================================

    def render_for_telegram(
        self,
        form: FormDefinition,
        current_step: int = 1,
        answers: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        رندر فرم برای نمایش در تلگرام.

        Args:
            form: تعریف فرم.
            current_step: شماره مرحله فعلی (پیش‌فرض ۱).
            answers: پاسخ‌های قبلی (برای نمایش مقادیر پر شده).
            include_metadata: شامل متادیتا (عنوان، توضیحات، و ...).

        Returns:
            Dict[str, Any]: شامل:
                - text: متن برای ارسال
                - keyboard: کیبورد شیشه‌ای
                - parse_mode: حالت پارسینگ (Markdown یا HTML)
        """
        try:
            # دریافت فیلدهای مرحله فعلی
            fields = form.get_fields_by_step(current_step)

            # ساخت متن
            text = self._build_telegram_text(
                form=form,
                fields=fields,
                current_step=current_step,
                answers=answers,
                include_metadata=include_metadata,
            )

            # ساخت کیبورد
            keyboard = self._build_telegram_keyboard(
                form=form,
                fields=fields,
                current_step=current_step,
                answers=answers,
            )

            return {
                "text": text,
                "keyboard": keyboard,
                "parse_mode": "Markdown",
            }

        except Exception as e:
            logger.error(f"Error rendering form for Telegram: {e}")
            return {
                "text": "⚠️ خطا در نمایش فرم. لطفاً دوباره تلاش کنید.",
                "keyboard": None,
                "parse_mode": "Markdown",
            }

    def render_step_for_telegram(
        self,
        form: FormDefinition,
        step: int,
        answers: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        رندر یک مرحله خاص از فرم برای تلگرام.

        Args:
            form: تعریف فرم.
            step: شماره مرحله (از ۱ شروع می‌شود).
            answers: پاسخ‌های قبلی.

        Returns:
            Dict[str, Any]: متن و کیبورد مرحله.
        """
        return self.render_for_telegram(form, step, answers)

    def _build_telegram_text(
        self,
        form: FormDefinition,
        fields: List[DynamicFormField],
        current_step: int,
        answers: Optional[Dict[str, Any]],
        include_metadata: bool,
    ) -> str:
        """
        ساخت متن برای نمایش در تلگرام.

        Args:
            form: تعریف فرم.
            fields: لیست فیلدهای مرحله.
            current_step: شماره مرحله فعلی.
            answers: پاسخ‌های قبلی.
            include_metadata: شامل متادیتا.

        Returns:
            str: متن فرمت‌شده.
        """
        lines = []

        # عنوان و توضیحات
        if include_metadata:
            if self.use_emoji:
                lines.append(f"📝 **{form.title}**")
            else:
                lines.append(f"**{form.title}**")
            lines.append("")

            if form.description:
                lines.append(f"{form.description}")
                lines.append("")

        # نمایش پیشرفت مراحل
        if self.show_step_progress and form.render_mode == FormRenderMode.STEPPED:
            progress = self._get_progress_bar(current_step, form.steps)
            lines.append(f"{progress}\n")

        # نمایش فیلدها
        if not fields:
            lines.append("⚠️ هیچ فیلدی برای این مرحله وجود ندارد.")
            return "\n".join(lines)

        for idx, field in enumerate(fields, 1):
            # نمایش فیلد
            field_text = self._render_field_for_telegram(
                field=field,
                current_value=answers.get(field.name) if answers else None,
                number=idx,
            )
            lines.append(field_text)
            lines.append("")

        # نمایش دکمه ارسال (در صورت آخرین مرحله)
        if current_step == form.steps:
            lines.append("---")
            lines.append(f"✅ {form.submit_button_text}")

        return "\n".join(lines)

    def _render_field_for_telegram(
        self,
        field: DynamicFormField,
        current_value: Optional[Any],
        number: int,
    ) -> str:
        """
        رندر یک فیلد برای نمایش در تلگرام.

        Args:
            field: فیلد فرم.
            current_value: مقدار فعلی (در صورت وجود).
            number: شماره فیلد.

        Returns:
            str: متن رندر شده فیلد.
        """
        required_indicator = " ⚠️" if field.is_required else ""
        label = field.label[:self.max_field_label_length]
        if len(field.label) > self.max_field_label_length:
            label += "..."

        lines = [f"**{number}. {label}{required_indicator}**"]

        if field.help_text:
            lines.append(f"💡 {field.help_text}")

        # نمایش مقدار فعلی
        if current_value is not None:
            display_value = self._format_value_for_display(current_value)
            lines.append(f"📌 مقدار فعلی: `{display_value}`")

        # نمایش گزینه‌ها (برای فیلدهای انتخابی)
        if field.field_type in FieldType.SELECTION_TYPES:
            options_text = self._render_options(field)
            if options_text:
                lines.append(options_text)

        # نمایش راهنمای ورودی
        input_guide = self._get_input_guide(field.field_type)
        if input_guide:
            lines.append(f"📌 {input_guide}")

        return "\n".join(lines)

    def _render_options(self, field: DynamicFormField) -> str:
        """
        رندر گزینه‌های یک فیلد انتخابی.

        Args:
            field: فیلد انتخابی.

        Returns:
            str: متن گزینه‌ها.
        """
        if not field.options:
            return ""

        lines = ["گزینه‌ها:"]
        for opt in field.options:
            label = opt.get("label", opt.get("value", "گزینه"))
            lines.append(f"• {label}")
        return "\n".join(lines)

    def _build_telegram_keyboard(
        self,
        form: FormDefinition,
        fields: List[DynamicFormField],
        current_step: int,
        answers: Optional[Dict[str, Any]],
    ) -> Optional[InlineKeyboardMarkup]:
        """
        ساخت کیبورد شیشه‌ای برای نمایش در تلگرام.

        Args:
            form: تعریف فرم.
            fields: لیست فیلدهای مرحله.
            current_step: شماره مرحله فعلی.
            answers: پاسخ‌های قبلی.

        Returns:
            Optional[InlineKeyboardMarkup]: کیبورد ساخته‌شده یا None.
        """
        buttons = []

        # دکمه‌های گزینه‌ها (برای فیلدهای انتخابی)
        for field in fields:
            if field.field_type in (FieldType.SELECT, FieldType.RADIO):
                field_buttons = self._get_field_option_buttons(field)
                buttons.extend(field_buttons)

            # برای فیلدهای چند انتخابی، دکمه‌های جداگانه
            elif field.field_type in (FieldType.MULTI_SELECT, FieldType.CHECKBOX):
                field_buttons = self._get_field_multi_option_buttons(field)
                buttons.extend(field_buttons)

        # دکمه‌های ناوبری
        nav_buttons = self._get_navigation_buttons(form, current_step)
        if nav_buttons:
            buttons.append(nav_buttons)

        # دکمه لغو
        buttons.append([
            InlineKeyboardButton(
                text="❌ انصراف",
                callback_data="form:cancel"
            )
        ])

        if not buttons:
            return None

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def _get_field_option_buttons(
        self,
        field: DynamicFormField,
    ) -> List[List[InlineKeyboardButton]]:
        """
        دریافت دکمه‌های گزینه‌ها برای یک فیلد انتخابی.

        Args:
            field: فیلد انتخابی.

        Returns:
            List[List[InlineKeyboardButton]]: دکمه‌های گزینه‌ها.
        """
        buttons = []
        for opt in field.options:
            label = opt.get("label", opt.get("value", "گزینه"))
            value = opt.get("value")
            buttons.append([
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"form:answer:{field.name}:{value}"
                )
            ])
        return buttons

    def _get_field_multi_option_buttons(
        self,
        field: DynamicFormField,
    ) -> List[List[InlineKeyboardButton]]:
        """
        دریافت دکمه‌های گزینه‌ها برای یک فیلد چند انتخابی.

        Args:
            field: فیلد چند انتخابی.

        Returns:
            List[List[InlineKeyboardButton]]: دکمه‌های گزینه‌ها.
        """
        buttons = []
        for opt in field.options:
            label = opt.get("label", opt.get("value", "گزینه"))
            value = opt.get("value")
            buttons.append([
                InlineKeyboardButton(
                    text=f"☑️ {label}",
                    callback_data=f"form:multi_answer:{field.name}:{value}"
                )
            ])
        return buttons

    def _get_navigation_buttons(
        self,
        form: FormDefinition,
        current_step: int,
    ) -> List[InlineKeyboardButton]:
        """
        دریافت دکمه‌های ناوبری برای فرم.

        Args:
            form: تعریف فرم.
            current_step: شماره مرحله فعلی.

        Returns:
            List[InlineKeyboardButton]: دکمه‌های ناوبری.
        """
        buttons = []

        if current_step > 1:
            buttons.append(
                InlineKeyboardButton(
                    text="⬅️ قبلی",
                    callback_data="form:previous"
                )
            )

        if current_step < form.steps:
            buttons.append(
                InlineKeyboardButton(
                    text="➡️ بعدی",
                    callback_data="form:next"
                )
            )
        else:
            buttons.append(
                InlineKeyboardButton(
                    text=f"✅ {form.submit_button_text}",
                    callback_data="form:submit"
                )
            )

        return buttons

    def _get_progress_bar(self, current_step: int, total_steps: int) -> str:
        """
        ساخت نوار پیشرفت برای نمایش.

        Args:
            current_step: شماره مرحله فعلی.
            total_steps: تعداد کل مراحل.

        Returns:
            str: نوار پیشرفت به‌صورت متن.
        """
        filled = "●" * current_step
        empty = "○" * (total_steps - current_step)
        percentage = int((current_step / total_steps) * 100)
        return f"پیشرفت: {filled}{empty} ({percentage}%)"

    def _get_input_guide(self, field_type: FieldType) -> Optional[str]:
        """
        دریافت راهنمای ورودی برای نوع فیلد.

        Args:
            field_type: نوع فیلد.

        Returns:
            Optional[str]: راهنمای ورودی.
        """
        guides = {
            FieldType.TEXT: "لطفاً متن مورد نظر را وارد کنید.",
            FieldType.TEXTAREA: "لطفاً متن کامل را وارد کنید.",
            FieldType.NUMBER: "لطفاً یک عدد وارد کنید.",
            FieldType.EMAIL: "لطفاً آدرس ایمیل را وارد کنید.",
            FieldType.PHONE: "لطفاً شماره تلفن را وارد کنید.",
            FieldType.DATE: "لطفاً تاریخ را به فرمت YYYY-MM-DD وارد کنید.",
            FieldType.TIME: "لطفاً زمان را به فرمت HH:MM وارد کنید.",
            FieldType.DATETIME: "لطفاً تاریخ و زمان را به فرمت ISO وارد کنید.",
            FieldType.URL: "لطفاً آدرس اینترنتی را وارد کنید.",
            FieldType.COLOR: "لطفاً کد رنگ را به فرمت #RRGGBB وارد کنید.",
            FieldType.RATING: "لطفاً امتیاز را از ۱ تا ۵ وارد کنید.",
        }
        return guides.get(field_type)

    def _format_value_for_display(self, value: Any) -> str:
        """
        فرمت‌سازی مقدار برای نمایش.

        Args:
            value: مقدار برای فرمت‌سازی.

        Returns:
            str: مقدار فرمت‌شده.
        """
        if value is None:
            return "❌ بدون پاسخ"
        if isinstance(value, bool):
            return "✅" if value else "❌"
        if isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value)
        if isinstance(value, dict):
            return str(value)
        return str(value)

    # ==========================================
    # رندر به فرمت‌های دیگر
    # ==========================================

    def render_as_json(self, form: FormDefinition) -> Dict[str, Any]:
        """
        رندر فرم به‌صورت JSON.

        Args:
            form: تعریف فرم.

        Returns:
            Dict[str, Any]: فرم به‌صورت دیکشنری.
        """
        return form.to_dict()

    def render_as_html(
        self,
        form: FormDefinition,
        include_styles: bool = True,
    ) -> str:
        """
        رندر فرم به‌صورت HTML.

        Args:
            form: تعریف فرم.
            include_styles: شامل استایل‌های CSS.

        Returns:
            str: HTML فرم.
        """
        html_parts = []

        if include_styles:
            html_parts.append(self._get_html_styles())

        html_parts.append(f'<div class="form-container">')
        html_parts.append(f'  <h2>{form.title}</h2>')

        if form.description:
            html_parts.append(f'  <p class="form-description">{form.description}</p>')

        html_parts.append('  <form method="post" action="/submit">')

        for field in form.fields:
            html_parts.append(self._render_field_as_html(field))

        html_parts.append('    <button type="submit" class="submit-btn">✅ ارسال</button>')
        html_parts.append('  </form>')
        html_parts.append('</div>')

        return "\n".join(html_parts)

    def _render_field_as_html(self, field: DynamicFormField) -> str:
        """
        رندر یک فیلد به‌صورت HTML.

        Args:
            field: فیلد فرم.

        Returns:
            str: HTML فیلد.
        """
        required_attr = ' required' if field.is_required else ''
        required_star = ' <span class="required">*</span>' if field.is_required else ''
        label = field.label[:self.max_field_label_length]
        if len(field.label) > self.max_field_label_length:
            label += "..."

        html = f'    <div class="field-group">'
        html += f'      <label for="{field.name}">{label}{required_star}</label>'

        if field.help_text:
            html += f'      <span class="help-text">{field.help_text}</span>'

        # رندر بر اساس نوع فیلد
        if field.field_type == FieldType.TEXT:
            html += f'      <input type="text" id="{field.name}" name="{field.name}"{required_attr}'
            if field.placeholder:
                html += f' placeholder="{field.placeholder}"'
            html += '>'

        elif field.field_type == FieldType.TEXTAREA:
            html += f'      <textarea id="{field.name}" name="{field.name}"{required_attr}'
            if field.placeholder:
                html += f' placeholder="{field.placeholder}"'
            html += '></textarea>'

        elif field.field_type == FieldType.NUMBER:
            html += f'      <input type="number" id="{field.name}" name="{field.name}"{required_attr}'
            if field.placeholder:
                html += f' placeholder="{field.placeholder}"'
            if "min" in field.validation_rules:
                html += f' min="{field.validation_rules["min"]}"'
            if "max" in field.validation_rules:
                html += f' max="{field.validation_rules["max"]}"'
            html += '>'

        elif field.field_type == FieldType.EMAIL:
            html += f'      <input type="email" id="{field.name}" name="{field.name}"{required_attr}'
            if field.placeholder:
                html += f' placeholder="{field.placeholder}"'
            html += '>'

        elif field.field_type == FieldType.PHONE:
            html += f'      <input type="tel" id="{field.name}" name="{field.name}"{required_attr}'
            if field.placeholder:
                html += f' placeholder="{field.placeholder}"'
            html += '>'

        elif field.field_type == FieldType.URL:
            html += f'      <input type="url" id="{field.name}" name="{field.name}"{required_attr}'
            if field.placeholder:
                html += f' placeholder="{field.placeholder}"'
            html += '>'

        elif field.field_type == FieldType.DATE:
            html += f'      <input type="date" id="{field.name}" name="{field.name}"{required_attr}>'

        elif field.field_type == FieldType.TIME:
            html += f'      <input type="time" id="{field.name}" name="{field.name}"{required_attr}>'

        elif field.field_type == FieldType.DATETIME:
            html += f'      <input type="datetime-local" id="{field.name}" name="{field.name}"{required_attr}>'

        elif field.field_type in (FieldType.SELECT, FieldType.RADIO):
            html += f'      <select id="{field.name}" name="{field.name}"{required_attr}>'
            html += '        <option value="">انتخاب کنید...</option>'
            for opt in field.options:
                label = opt.get("label", opt.get("value", ""))
                value = opt.get("value", "")
                html += f'        <option value="{value}">{label}</option>'
            html += '      </select>'

        elif field.field_type in (FieldType.MULTI_SELECT, FieldType.CHECKBOX):
            for opt in field.options:
                label = opt.get("label", opt.get("value", ""))
                value = opt.get("value", "")
                html += f'      <div class="checkbox-option">'
                html += f'        <input type="checkbox" id="{field.name}_{value}" name="{field.name}[]" value="{value}">'
                html += f'        <label for="{field.name}_{value}">{label}</label>'
                html += f'      </div>'

        elif field.field_type == FieldType.BOOLEAN:
            html += f'      <div class="boolean-option">'
            html += f'        <input type="checkbox" id="{field.name}" name="{field.name}" value="true"{required_attr}>'
            html += f'        <label for="{field.name}">بله</label>'
            html += f'      </div>'

        elif field.field_type == FieldType.RATING:
            html += f'      <div class="rating-group">'
            for i in range(1, 6):
                checked = ' checked' if field.default_value == i else ''
                html += f'        <input type="radio" id="{field.name}_{i}" name="{field.name}" value="{i}"{checked}{required_attr}>'
                html += f'        <label for="{field.name}_{i}">{i}⭐</label>'
            html += f'      </div>'

        elif field.field_type == FieldType.COLOR:
            html += f'      <input type="color" id="{field.name}" name="{field.name}"{required_attr}>'

        elif field.field_type == FieldType.RANGE:
            html += f'      <input type="range" id="{field.name}" name="{field.name}"{required_attr}'
            if "min" in field.validation_rules:
                html += f' min="{field.validation_rules["min"]}"'
            if "max" in field.validation_rules:
                html += f' max="{field.validation_rules["max"]}"'
            html += '>'

        elif field.field_type == FieldType.HIDDEN:
            html += f'      <input type="hidden" id="{field.name}" name="{field.name}">'

        else:
            html += f'      <input type="text" id="{field.name}" name="{field.name}"{required_attr}>'

        html += '    </div>'

        return html

    def _get_html_styles(self) -> str:
        """
        دریافت استایل‌های CSS برای فرم HTML.

        Returns:
            str: کد CSS.
        """
        return """
        <style>
            .form-container {
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                font-family: Arial, sans-serif;
            }
            .form-container h2 {
                color: #333;
                border-bottom: 2px solid #4CAF50;
                padding-bottom: 10px;
            }
            .form-description {
                color: #666;
                margin-bottom: 20px;
            }
            .field-group {
                margin-bottom: 20px;
            }
            .field-group label {
                display: block;
                font-weight: bold;
                margin-bottom: 5px;
                color: #333;
            }
            .field-group .required {
                color: red;
            }
            .field-group .help-text {
                display: block;
                font-size: 12px;
                color: #999;
                margin-bottom: 5px;
            }
            .field-group input[type="text"],
            .field-group input[type="email"],
            .field-group input[type="tel"],
            .field-group input[type="url"],
            .field-group input[type="number"],
            .field-group textarea,
            .field-group select {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
                font-size: 14px;
            }
            .field-group textarea {
                height: 100px;
                resize: vertical;
            }
            .checkbox-option, .boolean-option {
                margin: 5px 0;
            }
            .checkbox-option label, .boolean-option label {
                display: inline;
                font-weight: normal;
                margin-left: 5px;
            }
            .rating-group {
                display: flex;
                gap: 10px;
                align-items: center;
            }
            .rating-group input[type="radio"] {
                display: none;
            }
            .rating-group label {
                cursor: pointer;
                padding: 5px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: #f9f9f9;
                margin: 0;
            }
            .rating-group input[type="radio"]:checked + label {
                background: #4CAF50;
                color: white;
                border-color: #4CAF50;
            }
            .submit-btn {
                background: #4CAF50;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
            }
            .submit-btn:hover {
                background: #45a049;
            }
        </style>
        """