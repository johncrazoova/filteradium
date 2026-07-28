# فیلترادیوم | Filteradium
## پلتفرم فیلترنویسی هوشمند بورس ایران

### 🎯 هدف
ساده‌سازی فیلترنویسی و تحلیل سهام بورس اوراق بهادار تهران برای معامله‌گران.

### 📊 امکانات

**فرانت‌اند:**
- رابط کاربری زیبا و ریسپانسیو
- فیلترنویسی Drag & Drop
- ۶ فیلتر آماده
- نمایش لحظه‌ای قیمت

**بک‌اند (Python):**
- API واقعی TSETMC
- موتور تحلیل تکنیکال
- سیستم امتیازدهی پیشرفته
- تشخیص الگوها
- تحلیل جریان پول
- مدیریت ریسک
- پایگاه داده SQLite

### 🛠️ نصب و اجرا

```bash
# 1. نصب dependency ها
cd backend
pip install -r requirements.txt

# 2. اجرای سرور
cd ..
python run.py
```

**یا با Docker:**
```bash
docker-compose up
```

### 📡 API Endpoints

| Endpoint | Method | توضیح |
|----------|--------|-------|
| `/api/market` | GET | دیتای بازار |
| `/api/stock/{ins_code}/score` | GET | امتیاز سهم |
| `/api/filter` | POST | اعمال فیلتر |
| `/api/search` | GET | جستجوی سهم |
| `/api/scores/batch` | GET | امتیاز چند سهم |
| `/api/filters/presets` | GET | فیلترهای آماده |
| `/docs` | GET | مستندات Swagger |

### 📁 ساختار پروژه

```
filteradium/
├── backend/
│   ├── api/
│   │   └── tsetmc_client.py    # کلاینت TSETMC
│   ├── core/
│   │   └── scoring.py          # موتور تحلیل و امتیازدهی
│   ├── models/
│   │   └── database.py         # مدل‌های پایگاه داده
│   ├── main.py                 # سرور FastAPI
│   └── requirements.txt
├── styles/
│   └── main.css                # استایل‌های فرانت‌اند
├── lib/
│   ├── filters.js              # منطق فیلترنویسی
│   └── app.js                  # منطق اپلیکیشن
├── index.html                  # صفحه اصلی
├── run.py                      # اسکریپت اجرا
└── README.md
```

### 🔧 تکنولوژی‌ها

- **Backend:** Python, FastAPI, SQLAlchemy
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **API:** TSETMC CDN

### 📋 نقشه راه

- [x] MVP فرانت‌اند
- [x] بک‌اند Python
- [x] موتور تحلیل تکنیکال
- [x] سیستم امتیازدهی
- [ ] اتصال به API واقعی
- [ ] سیستم ورود/ثبت‌نام
- [ ] هشدار تلگرام
- [ ] درگاه پرداخت
- [ ] اپلیکیشن موبایل

### 👤 تیم

- توسعه‌دهنده: Saeid
- AI Assistant: Hermes

### ⚠️ هشدار
بورس دارای ریسک است. قبل از سرمایه‌گذاری تحقیق کنید.
