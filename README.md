# AghaKocholo / ZLT X28 — Railway-ready

این پروژه ظاهر اصلی سایت آپلودشده را نگه می‌دارد و یک بک‌اند Flask + REST API + PostgreSQL به آن اضافه می‌کند.

## امکانات
- بسته‌های روزانه/هفتگی/ماهانه
- ثبت سفارش در دیتابیس
- ورود و حساب کاربری
- نمایش حجم کل/مصرف/باقی‌مانده/روزهای اعتبار
- چت کاربر و پشتیبانی
- پنل Admin
- تغییر حجم و وضعیت کاربر
- پیام اختصاصی و Broadcast
- مدیریت وضعیت سفارش
- Gunicorn و سازگار با Railway
- PostgreSQL روی Railway برای ماندگاری اطلاعات

## نکته مهم پرداخت
«ثبت سفارش» آماده است، اما پرداخت واقعی بانکی به درگاه نیاز دارد. برای درگاه ایرانی باید Merchant/کلید و API همان درگاه را وارد کنیم؛ بعد از آن می‌شود سفارش را به پرداخت و Callback متصل کرد.

## اجرای محلی
Windows:
```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set SECRET_KEY=یک-کلید-طولانی
set ADMIN_USERNAME=admin
set ADMIN_PASSWORD=یک-رمز-قوی
python app.py
```
سپس:
http://127.0.0.1:5000

## استقرار Railway
1. کل پوشه را در GitHub قرار بده یا با Railway CLI مستقیماً deploy کن.
2. در Railway یک سرویس PostgreSQL بساز.
3. Railway متغیر DATABASE_URL را برای پروژه در دسترس قرار می‌دهد.
4. در Variables این‌ها را بساز:
   SECRET_KEY=یک مقدار تصادفی طولانی
   ADMIN_USERNAME=نام مدیر
   ADMIN_PASSWORD=رمز قوی مدیر
5. Start Command:
   gunicorn app:app
6. از Networking گزینه Generate Domain را بزن.

## ساخت کاربر
فعلاً کاربرها از داخل دیتابیس ساخته می‌شوند. برای شروع می‌توانی یک route ثبت‌نام یا صفحه مدیریت کاربران اضافه کنی. اکانت مدیر در اولین اجرای برنامه با ADMIN_USERNAME/ADMIN_PASSWORD ساخته می‌شود.

## امنیت
- رمزها Hash می‌شوند.
- رمز مدیر را داخل کد ننویس.
- SECRET_KEY را در Railway Variables قرار بده.
- برای محیط واقعی بهتر است CSRF، rate limit، لاگ حسابرسی و درگاه پرداخت رسمی اضافه شوند.
