# استخدام صورة Python الرسمية
FROM python:3.11-slim

# إعداد مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملفات المشروع إلى الحاوية
COPY . .

# تثبيت المتطلبات الأساسية لتشغيل Playwright في Docker
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg2 \
    fonts-liberation libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 \
    libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 libgtk-3-0 libxss1 libxtst6 libxshmfence1 \
    libglib2.0-0 libxext6 libxfixes3 libxkbcommon0 libpango-1.0-0 \
    libdrm2 libcairo2 libgbm1 libexpat1 libx11-6 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# تثبيت مكتبات Python
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

# تثبيت متصفحات Playwright
RUN playwright install --with-deps

# تشغيل البوت تلقائيًا عند تشغيل الحاوية
CMD ["python", "product_monitor_bot.py"]
