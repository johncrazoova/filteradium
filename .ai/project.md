# Filteradium

## هدف پروژه
استخراج، تحلیل و صادرات اطلاعات بورس ایران (TSETMC) با رابط کاربری گرافیکی

## قابلیت‌های اصلی
- دریافت لیست تمام نمادهای بازار از TSETMC
- دریافت تاریخچه قیمت، حقیقی/حقوقی، سهام‌داران
- ذخیره داده در دیتابیس لوکال (SQLite)
- صادرات CSV و Excel
- فیلتر بر اساس صنعت، نماد، بازه زمانی
- رابط کاربری تاریک با تم طلایی

## تکنولوژی‌ها
- **Desktop:** Electron 28 + Node.js
- **Database:** SQLite (better-sqlite3)
- **Export:** xlsx library
- **Backend (اختیاری):** Python FastAPI + SQLAlchemy
- **CI/CD:** GitHub Actions

## وابستگی‌ها
```json
{
  "better-sqlite3": "^9.4.0",
  "xlsx": "^0.18.5",
  "electron": "^28.0.0",
  "electron-builder": "^24.0.0"
}
```

## API
- TSETMC CDN: `https://cdn.tsetmc.com`
- مستقیم از مرورگر (renderer process) فراخوانی می‌شود
