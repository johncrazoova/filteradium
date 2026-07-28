# Architecture

## ساختار پوشه‌ها
```
filteradium/
├── .ai/                    # مستندات AI
├── desktop/                # اپ دسکتاپ Electron
│   ├── main.js            # Main process: دیتابیس + IPC
│   ├── preload.js         # Bridge: Main ↔ Renderer
│   ├── renderer.js        # Renderer process: UI + API
│   ├── index.html         # ساختار HTML
│   ├── styles.css         # استایل‌ها
│   └── package.json       # وابستگی‌ها
├── core/                   # (اختیاری) کلاینت Python
├── models/                 # (اختیاری) مدل‌های DB
├── services/               # (اختیاری) سرویس‌ها
├── main.py                 # (اختیاری) نقطه ورود Python
└── requirements.txt        # (اختیاری) وابستگی‌های Python
```

## الگوی معماری
**Electron Two-Process Model:**

```
┌─────────────────────────────────────────┐
│              Renderer Process            │
│  (renderer.js + index.html + styles.css) │
│                                          │
│  ✅ UI                                  │
│  ✅ API calls (browser fetch)           │
│  ✅ منطق نمایش                          │
└──────────────┬──────────────────────────┘
               │ IPC (preload.js)
┌──────────────▼──────────────────────────┐
│              Main Process                │
│              (main.js)                   │
│                                          │
│  ✅ دیتابیس SQLite                      │
│  ✅ ذخیره/بازیابی داده                  │
│  ✅ صادرات فایل                          │
│  ❌ API calls (غیرفعال)                 │
└─────────────────────────────────────────┘
```

## قوانین وابستگی
1. **renderer.js** → فقط با `window.api` ( preload ) ارتباط دارد
2. **main.js** → فقط از طریق `ipcMain.handle` سرویس می‌دهد
3. **preload.js** → فقط bridge بین renderer و main
4. **API calls** → حتماً از renderer.js با `fetch()` انجام شود
5. **دیتابیس** → فقط در main.js دسترسی دارد

## ممنوعیت‌ها
- ❌ استفاده از `node-fetch` یا `http` module برای API
- ❌ دسترسی مستقیم renderer به SQLite
- ❌ استفاده از `nodeIntegration: true`
- ❌ تغییر ساختار IPC بدون بروزرسانی preload
