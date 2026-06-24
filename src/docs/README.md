============================================================
              پروژه ربات تلگرام با معماری Clean Architecture
============================================================

نام پروژه: my_bot_project
نسخه: 1.0.0
زبان: Python 3.9+
معماری: Clean Architecture + DDD
ارتباط: aiohttp (Long Polling)
دیتابیس: PostgreSQL (اصلی) / SQLite (توسعه)
کش: Redis (اختیاری با Fallback محلی)

------------------------------------------------------------
                    معرفی پروژه
------------------------------------------------------------

این پروژه یک ربات تلگرام با معماری Clean Architecture و رویکرد
Domain-Driven Design (DDD) است. ربات شامل دو بخش اصلی است:

1. my_bot: هسته اصلی ربات برای کاربران عادی
2. admin_panel: پنل مدیریت برای ادمین‌ها

تمامی عملیات مدیریتی فقط از طریق دکمه‌های شیشه‌ای (Inline Keyboard)
انجام می‌شود و کاربران نیازی به تایپ هیچ دستوری ندارند.

------------------------------------------------------------
                    ویژگی‌های اصلی
------------------------------------------------------------

۱. ساختار Clean Architecture با دو پکیج مستقل
۲. سلسلهمراتب استثناهای سفارشی
۳. لاگ‌گیری حرفه‌ای با RotatingFileHandler
۴. اعتبارسنجی ورودی با Pydantic
۵. اتصال به دیتابیس با Connection Pool
۶. سیستم کش با Redis (با Fallback خودکار به Local)
۷. محدودیت نرخ درخواست (Rate Limiting - Sliding Window)
۸. دکوریتور Retry با Backoff
۹. سیستم فرم‌ساز پویا (Dynamic Form Engine)
۱۰. سیستم Import از فایل اکسل (Bulk Import)
۱۱. تکمیل Type Hints در کل پروژه
۱۲. مدیریت خودکار منابع
۱۳. مدیریت پیکربندی متمرکز (Config با dataclass)
۱۴. مدیریت حرفه‌ای دکمه‌ها (پیام، فرم، پرداخت، لینک، دستور)
۱۵. پنل لاگ در مدیریت
۱۶. پنل آمار و تحلیل در پنل مدیریت
۱۷. مستندات در پنل مدیریت
۱۸. سیستم ارسال پیام گروهی (Broadcast) با فیلترهای پیشرفته
۱۹. تحلیل رفتار، A/B تست، گزارش خودکار، یادآوری، بازخورد،
    امتیاز و سطوح، وبهوک، چندزبانی، کش هوشمند، بررسی سلامت،
    تیکت پشتیبانی، تخفیف و کوپن
۲۰. پروفایل کاربر (نمایش اطلاعات، سفارشات، امتیاز، سطح)
۲۱. راهنمای کاربر (راهنمای کامل، سوالات متداول، تماس با ما)
۲۲. پیام‌های رندوم و حرفه‌ای
۲۳. محیط کاربرپسند (دکمه‌های ثابت بازگشت/انصراف/منوی اصلی + ایموجی)
۲۴. آمادگی برای وب ربات (لایه Presentation جدا + مسیر web_api)
۲۵. بخش خطاها (Error Logs) در پنل مدیریت
۲۶. سیستم Feature Flag (مدیریت فعال/غیرفعال‌سازی ماژول‌ها)

------------------------------------------------------------
                    ساختار پروژه
------------------------------------------------------------

my_bot_project/
├── pyproject.toml
├── .env
├── .gitignore
├── README.md
├── docker-compose.yml
├── src/
│   ├── my_bot/
│   │   ├── core/           (config, constants, exceptions, logger, feature_flags)
│   │   ├── domain/         (entities, value_objects, interfaces)
│   │   ├── application/    (services, dtos, use_cases)
│   │   ├── infrastructure/ (database, repositories, cache, external, health_check)
│   │   ├── presentation/   (handlers, keyboards, middlewares, web_api)
│   │   ├── shared/         (utils, decorators, i18n)
│   │   ├── dynamic_forms/  (موتور فرم‌ساز پویا)
│   │   ├── bulk_import/    (واردات از اکسل)
│   │   ├── export/         (خروجی‌گیری)
│   │   ├── notifications/  (یادآوری، پیام‌های خودکار)
│   │   ├── audit/          (ثبت لاگ عملیات)
│   │   └── bootstrap/      (container, app)
│   ├── admin_panel/
│   │   ├── core/           (permissions)
│   │   ├── modules/        (مدیریت کاربران، سفارشات، آمار، محتوا، ...)
│   │   ├── ui/             (keyboards)
│   │   └── bootstrap/      (admin_loader, module_register, admin_router)
│   ├── scripts/            (db_migrate, create_admin, backup_db, seed_data)
│   ├── tests/              (unit, integration, e2e)
│   └── docs/               (مستندات)

------------------------------------------------------------
                    نصب و راه‌اندازی
------------------------------------------------------------

۱. پیش‌نیازها:
   - Python 3.9 یا بالاتر
   - pip (مدیریت بسته‌های Python)
   - PostgreSQL یا SQLite
   - Redis (اختیاری)

۲. کلون کردن پروژه:
   git clone https://github.com/yourusername/my_bot_project.git
   cd my_bot_project

۳. ایجاد محیط مجازی:
   python -m venv venv
   source venv/bin/activate   # در لینوکس/Mac
   venv\Scripts\activate      # در ویندوز

۴. نصب وابستگی‌ها:
   pip install -r requirements.txt

۵. تنظیم متغیرهای محیطی:
   فایل .env را بر اساس نمونه .env.example ایجاد کنید:
   
   BOT_TOKEN=your_bot_token
   ADMIN_IDS=123456789,987654321
   DATABASE_URL=postgresql://user:password@localhost/dbname
   # یا برای SQLite: sqlite:///./dev.db
   REDIS_URL=redis://localhost:6379/0
   LOG_FILE=logs/my_bot.log
   RATE_LIMIT=30
   RATE_WINDOW=60

۶. اجرای مهاجرت‌های دیتابیس:
   python -m src.scripts.db_migrate upgrade

۷. ایجاد کاربر ادمین:
   python -m src.scripts.create_admin --telegram-id 123456789 --role super_admin

۸. اجرای ربات:
   python -m src.my_bot.bootstrap.app

------------------------------------------------------------
                    ساختار فایل‌های کلیدی
------------------------------------------------------------

src/my_bot/core/config.py
   پیکربندی متمرکز با استفاده از dataclass

src/my_bot/core/exceptions.py
   سلسلهمراتب استثناهای سفارشی

src/my_bot/core/logger.py
   لاگ‌گیری با RotatingFileHandler

src/my_bot/core/feature_flags.py
   مدیریت Feature Flag با کش

src/my_bot/bootstrap/container.py
   کانتینر DI (Dependency Injection)

src/my_bot/bootstrap/app.py
   راه‌اندازی ربات

src/my_bot/shared/utils/message_pool.py
   بانک پیام‌های رندوم

src/my_bot/presentation/keyboards/common_keyboards.py
   دکمه‌های مشترک (بازگشت، انصراف، منوی اصلی)

src/admin_panel/ui/keyboards.py
   کیبوردهای اصلی پنل مدیریت

src/admin_panel/modules/feature_management/handlers.py
   پردازش دکمه‌های مدیریت فیچرها

------------------------------------------------------------
                    نحوه تعامل ادمین
------------------------------------------------------------

تمامی عملیات مدیریتی فقط از طریق کلیک روی دکمه‌های شیشه‌ای
(Inline Keyboard) در پنل مدیریت انجام می‌شود.

دستورات اسلش (مثل /new_form) صرفاً به عنوان میانبرهای اختیاری
برای توسعه‌دهنده در نظر گرفته می‌شوند.

مسیر دسترسی به پنل مدیریت:
1. کاربر روی دکمه "⚙️ پنل مدیریت" در منوی اصلی کلیک می‌کند
2. ربات کیبورد اصلی پنل مدیریت را نمایش می‌دهد
3. ادمین با کلیک روی هر دکمه، عملیات مربوطه را انجام می‌دهد

------------------------------------------------------------
                    تست‌ها
------------------------------------------------------------

برای اجرای تست‌ها:

# اجرای همه تست‌ها
pytest tests/

# اجرای تست‌های واحد
pytest tests/unit/

# اجرای تست‌های یکپارچه
pytest tests/integration/

# اجرای تست‌های End-to-End
pytest tests/e2e/

# اجرای تست‌ها با پوشش کد
pytest --cov=src tests/

------------------------------------------------------------
                    اسکریپت‌های کمکی
------------------------------------------------------------

۱. مهاجرت دیتابیس:
   python -m src.scripts.db_migrate upgrade
   python -m src.scripts.db_migrate migrate -m "add new table"
   python -m src.scripts.db_migrate downgrade -1
   python -m src.scripts.db_migrate status

۲. ایجاد کاربر ادمین:
   python -m src.scripts.create_admin --telegram-id 123456789 --role super_admin
   python -m src.scripts.create_admin --list

۳. پشتیبان‌گیری از دیتابیس:
   python -m src.scripts.backup_db backup
   python -m src.scripts.backup_db backup --compress
   python -m src.scripts.backup_db list
   python -m src.scripts.backup_db restore ./backups/db_backup.sql

۴. پر کردن دیتابیس با داده‌های نمونه:
   python -m src.scripts.seed_data --count 20
   python -m src.scripts.seed_data --clear --users 30 --orders 100

------------------------------------------------------------
                    ماژول‌های پنل مدیریت
------------------------------------------------------------

پنل مدیریت شامل ۱۷ ماژول مجزا است:

۱. user_management    - مدیریت کاربران
۲. order_management   - مدیریت سفارشات
۳. analytics          - آمار و تحلیل
۴. content_management - مدیریت محتوا
۵. backup_restore     - پشتیبان‌گیری و بازیابی
۶. monitoring         - پایش سیستم
۷. admin_management   - مدیریت ادمین‌ها
۸. advanced_search    - جستجوی پیشرفته
۹. settings           - تنظیمات عمومی
۱۰. logs_viewer       - مشاهده لاگ‌ها
۱۱. broadcast         - ارسال گروهی
۱۲. error_logs        - مشاهده خطاها
۱۳. system_health     - سلامت سیستم
۱۴. tickets           - تیکت‌های پشتیبانی
۱۵. coupons           - تخفیف و کوپن
۱۶. feedback_management - مدیریت بازخورد
۱۷. ab_testing        - آزمون A/B
۱۸. behavior_analytics - تحلیل رفتار
۱۹. feature_management - مدیریت فیچر فلاگ‌ها

------------------------------------------------------------
                    وابستگی‌های اصلی
------------------------------------------------------------

- aiogram 3.x          - کتابخانه اصلی ربات تلگرام
- aiohttp              - برای Long Polling و وب‌هوک
- SQLAlchemy 2.x       - ORM برای دیتابیس
- Alembic              - مدیریت مهاجرت‌های دیتابیس
- asyncpg              - درایور PostgreSQL
- aiosqlite            - درایور SQLite
- redis-py             - کلاینت Redis
- Pydantic 2.x         - اعتبارسنجی داده‌ها
- python-dotenv        - مدیریت متغیرهای محیطی
- matplotlib           - تولید نمودارها
- openpyxl             - کار با فایل‌های Excel
- psutil               - پایش سیستم
- pytest               - تست‌نویسی

------------------------------------------------------------
                    مجوز و حقوق
------------------------------------------------------------

این پروژه تحت مجوز MIT منتشر شده است.

------------------------------------------------------------
                    ارتباط با توسعه‌دهنده
------------------------------------------------------------

برای گزارش مشکلات یا پیشنهادات، لطفاً یک Issue در مخزن GitHub
ایجاد کنید یا با پشتیبانی تماس بگیرید.

ایمیل: support@mybot.com
تلگرام: @MyBotSupport

------------------------------------------------------------
                    نسخه‌ها و تغییرات
------------------------------------------------------------

نسخه 1.0.0 (تاریخ انتشار: ۱۴۰۵/۰۴/۰۳)
- انتشار اولیه پروژه
- پیاده‌سازی کامل ۲۶ ویژگی اجباری
- پنل مدیریت با ۱۹ ماژول

============================================================
                    پایان فایل README
============================================================