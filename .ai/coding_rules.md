# Coding Rules

## قوانین نام‌گذاری
| نوع | الگو | مثال |
|-----|------|------|
| متغیر | camelCase | `allStocks`, `selectedStocks` |
| تابع | camelCase | `fetchAllStocks()`, `renderTable()` |
| کلاس | PascalCase | `TSETMCClient` |
| constant | UPPER_SNAKE | `API_URLS`, `DATABASE_URL` |
| فایل JS | camelCase | `renderer.js`, `main.js` |
| فایل CSS | kebab-case | `styles.css` |
| فایل MD | snake_case | `coding_rules.md` |
| ID در HTML | kebab-case | `btnFetch`, `symbolList` |
| CSS class | kebab-case | `.symbol-item`, `.btn-primary` |
| دیتابیس | snake_case | `price_history`, `client_type` |

## فرمت Commit
```
<emoji> <پیام فارسی>

<توضیحات اختیاری>
```

### ایموجی‌ها
| ایموجی | نوع |
|--------|-----|
| 🎯 | ویژگی جدید |
| 🔧 | فیکس باگ |
| ✨ | بهبود UI |
| 📦 | وابستگی جدید |
| 🔨 | refactor |
| 📝 | مستندات |
| 🧪 | تست |

### مثال
```
🎯 اتصال TSETMC از مرورگر

API calls رو از Node.js به browser fetch منتقل کرد
```

## سبک کدنویسی
- **Indent:** 2 spaces
- **Semicolon:** ضروری نیست ولی یکسان باشه
- **Quotes:** single quote در JS
- **RTL:** تمام متن‌های فارسی
- **Comment:** فارسی برای توضیحات منطق

## ممنوعیت‌ها
- ❌ تغییر فایل‌های تولیدشده (`dist/`, `node_modules/`)
- ❌ استفاده از `var` (فقط `let` و `const`)
- ❌ console.log در production (فقط برای debug)
- ❌ hardcoded API URL (از `API_URLS` استفاده شود)
- ❌ تغییر ساختار دیتابیس بدون migration
- ❌ حذف جداول دیتابیس
- ❌ تغییر نام فیلدهای دیتابیس

## تست
- قبل از هر commit: `npm run build` بدون خطا
- اتصال TSETMC: دکمه تست اتصال
- خروجی: تست CSV و Excel
