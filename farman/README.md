# 🚀 فرمان (Farman) - Enterprise AI Operating System

**سامانه‌عامل هوش مصنوعی برای مدیریت شرکت**

فرمان یک پلتفرم SaaS سازمانی است که فایل‌های اکسل را به یک سیستم هوشمند مدیریت کسب‌وکار تبدیل می‌کند.

## ✨ ویژگی‌های کلیدی

- 📤 **آپلود هوشمند فایل**: تشخیص خودکار دامنه (فروش، انبار، حسابداری، منابع انسانی و...)
- 🧹 **پاکسازی خودکار داده**: حذف ادغام‌ها، تکراری‌ها، استانداردسازی تاریخ و اعداد
- 📊 **تولید داشبورد حرفه‌ای**: ایجاد خودکار نمودار، Pivot Table، KPI
- 🗄️ **انبار داده PostgreSQL**: ذخیره داده‌های نرمال‌شده برای تحلیل سریع
- 🔗 **لایه معنایی**: نگاشت ستون‌های مختلف به مفاهیم یکپارچه کسب‌وکار
- 🧠 **گراف دانش**: ایجاد ارتباط بین مشتریان، محصولات، فاکتورها، انبارها
- 🤖 **AI Agent**: پاسخ به سؤالات طبیعی با تحلیل چندبخشی
- 📈 **امتیاز سلامت شرکت**: محاسبه روزانه امتیاز ۰-۱۰۰ با توصیه‌های عملی
- 🔮 **پیش‌بینی و تحلیل**: پیش‌بینی موجودی، نقدینگی، ریزش مشتریان
- 📱 **ربات تلگرام**: گزارش روزانه، هشدارها، اقدامات خودکار

## 🏗️ معماری سیستم

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (React/Vue)               │
│              Tailwind CSS + Persian UI              │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                 Django REST API                     │
│           JWT Auth + Rate Limiting                  │
└─────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Celery     │  │   PostgreSQL │  │    Redis     │
│   Workers    │  │   + pgvector │  │   Cache      │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  AI Engine   │  │  Data Models │
│  LangChain   │  │  Sales, Inv  │
│  OpenAI      │  │  HR, Acc     │
└──────────────┘  └──────────────┘
```

## 🛠️ نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Node.js 18+ (برای فرانت‌اند)

### مراحل نصب

```bash
# کلون کردن پروژه
git clone https://github.com/yourusername/farman.git
cd farman

# ساخت محیط مجازی
python -m venv venv
source venv/bin/activate  # Linux/Mac
# یا
venv\Scripts\activate  # Windows

# نصب وابستگی‌ها
pip install -r requirements.txt

# کپی فایل تنظیمات
cp .env.example .env
# ویرایش فایل .env و تنظیم مقادیر

# اجرای مهاجرت‌ها
python manage.py migrate

# ساخت سوپریوزر
python manage.py createsuperuser

# جمع‌آوری فایل‌های استاتیک
python manage.py collectstatic

# اجرای سرور توسعه
python manage.py runserver
```

### اجرای Celery

```bash
# ترمینال اول - Celery Worker
celery -A farman worker --loglevel=info

# ترمینال دوم - Celery Beat (برای تسک‌های دوره‌ای)
celery -A farman beat --loglevel=info
```

## 📁 ساختار پروژه

```
farman/
├── farman/                 # تنظیمات اصلی پروژه
│   ├── settings.py         # تنظیمات Django
│   ├── urls.py             # URL Routing
│   ├── celery_app.py       # تنظیمات Celery
│   └── wsgi.py
├── core/                   # ماژول احراز هویت و کاربران
│   ├── models.py           # User, TimeStampedModel
│   ├── views.py
│   └── middleware.py
├── companies/              # مدیریت شرکت‌ها و شعب
│   ├── models.py           # Company, Branch, Department
│   └── views.py
├── uploads/                # آپلود و پردازش فایل
│   ├── models.py           # UploadedFile, ColumnMapping
│   ├── services.py         # منطق پردازش فایل
│   └── tasks.py            # تسک‌های Celery
├── ai_engine/              # موتور هوش مصنوعی
│   ├── domain_detector.py  # تشخیص دامنه فایل
│   ├── cleaning_engine.py  # پاکسازی داده
│   ├── knowledge_graph.py  # گراف دانش
│   └── agent.py            # AI Agent
├── analytics/              # تحلیل و گزارش‌گیری
│   ├── health_score.py     # امتیاز سلامت شرکت
│   └── predictors.py       # پیش‌بینی‌ها
├── api/                    # API endpoints
│   ├── views.py
│   └── serializers.py
├── templates/              # قالب‌های HTML
├── static/                 # فایل‌های استاتیک
└── media/                  # فایل‌های آپلود شده
```

## 🔐 امنیت

- احراز هویت JWT با امکان چرخش توکن
- رمزنگاری پسوردها با bcrypt
- محافظت در برابر CSRF, XSS, SQL Injection
- محدودیت نرخ درخواست (Rate Limiting)
- تفکیک دسترسی بر اساس نقش (RBAC)
- لاگ کامل فعالیت‌ها

## 💳 طرح‌های اشتراک

| طرح | قیمت | دوره آزمایشی | ویژگی‌ها |
|-----|------|--------------|----------|
| آزمایشی | رایگان | ۱۴ روز | ۵ کاربر، ۱۰ گیگابایت فضا |
| ماهانه | ۹۹ دلار/ماه | - | نامحدود |
| سالانه | ۹۹۰ دلار/سال | - | ۲ ماه رایگان |
| سازمانی | تماس بگیرید | - | سفارشی‌سازی کامل |

## 🤖 ربات تلگرام

ربات تلگرام برای:
- 📬 دریافت گزارش روزانه ساعت ۸ صبح
- ⚠️ هشدار چک‌های سررسید شده
- 📊 پرسش و پاسخ طبیعی از داده‌ها
- ✅ تأیید اقدامات پیشنهادی AI

## 📊 API Documentation

پس از اجرای سرور، مستندات API را در آدرس زیر مشاهده کنید:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## 🧪 تست

```bash
# اجرای تست‌ها
pytest

# با پوشش کد
pytest --cov=farman
```

## 📝 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.

## 🤝 مشارکت

خوشحال می‌شویم در توسعه فرمان مشارکت کنید!

---

**ساخته شده با ❤️ برای کسب‌وکارهای ایرانی**
