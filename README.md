# IAS-Viewer-Server 🖥️

**نسخه‌ی سروری IAS Viewer — سرور مرکزی پخش استریم دوربین‌ها برای اتاق مانیتورینگ**
*Server edition of IAS Viewer — central camera stream relay server for monitoring rooms.*

## چی هست؟ | What is it?

IAS-Viewer-Server خودش به دوربین‌ها (RTSP/ONVIF) وصل می‌شود و تصویر را به‌صورت
متمرکز برای کلاینت‌ها پخش می‌کند. کاربرد اصلی: **اتاق مانیتورینگ** —
هر مانیتور فقط یک مرورگر تمام‌صفحه باز می‌کند، بدون نصب هیچ برنامه‌ای.

It connects directly to the cameras (RTSP/ONVIF) and relays the streams
centrally to clients. Primary use case: the **monitoring room** — each
monitor just opens a fullscreen browser, no client software to install.

## تفاوت با نسخه‌های دسکتاپ/موبایل | Differences from desktop/mobile

| | سروری (این ریپو) | دسکتاپ/موبایل |
|---|---|---|
| محل اتصال به دوربین | سرور مرکزی | خودِ کلاینت |
| رابط کاربری | داشبورد وب در مرورگر | برنامه‌ی گرافیکی (PyQt/Kivy) |
| نصب روی مانیتورها | لازم نیست (فقط مرورگر) | لازم است |
| اجرا | headless با Docker | تعاملی |

## معماری کلی | Architecture

```
دوربین‌ها (RTSP)
    │
    ▼
MediaMTX (کانتینر جدا) ── ingest از RTSP دوربین‌ها
    │                       پخش HLS روی پورت 8888 + WebRTC روی پورت 8889
    ▼
بک‌اند FastAPI/uvicorn (پورت 8000)
    │  • API مدیریت دوربین‌ها (لیست در cameras.json)
    │  • سروِ داشبورد وب
    │  • GET /api/license — اعلام لایسنس و سورس (الزام AGPL-3.0 برای سرور)
    ▼
داشبورد وب استاتیک ── گرید دوربین‌ها با hls.js (از CDN)
                      پروفایل مانیتور: ?monitor=mon1
```

- `tools/gen_mediamtx.py` کانفیگ MediaMTX را از روی `cameras.json` می‌سازد.
- اجرا: `docker compose up -d`

## شروع سریع | Quick start

راهنمای کامل نصب و اجرا (فارسی): **[GUIDE-FA.md](./GUIDE-FA.md)**

```bash
git clone https://github.com/thaarfknight-star/IAS-Viewer-Server.git
cd IAS-Viewer-Server
cp backend/cameras.json.example backend/cameras.json   # RTSP دوربین‌ها را بگذار
cp .env.example .env                                   # مقادیر خودت را بگذار
python3 tools/gen_mediamtx.py
docker compose up -d
# داشبورد: http://SERVER_IP:8000
```

## امنیت | Security

- هیچ یوزر/پسورد پیش‌فرضی در ریپو نیست؛ توکن API فقط از متغیر محیطی (`IVS_API_TOKEN`) خوانده می‌شود.
- فایل‌های `.env` و `cameras.json` در `.gitignore` هستند — هرگز کامیت نمی‌شوند.

## لایسنس | License

Copyright (C) 2026 Taha Arefi (طه عارفی)

این برنامه نرم‌افزار آزاد است تحت **GNU Affero General Public License v3.0**
(متن کامل: [LICENSE](./LICENSE) — https://www.gnu.org/licenses/agpl-3.0.html).
سورس‌کد همین‌جاست؛ سرورِ در حال اجرا هم از طریق `/api/license` لایسنس و
سورس را اعلام می‌کند (بند ۱۳ AGPL).

*This program is free software under the GNU Affero General Public License v3.0 —
see [LICENSE](./LICENSE).*

## ریپوهای مرتبط | Related repos

- 🖥️ دسکتاپ (ویندوز): [IAS-CMS](https://github.com/thaarfknight-star/IAS-CMS)
- 🤖 اندروید: [IAS-Viewer-Android](https://github.com/thaarfknight-star/IAS-Viewer-Android)
- 🍎 مک: [IAS-Viewer-MAC](https://github.com/thaarfknight-star/IAS-Viewer-MAC)
