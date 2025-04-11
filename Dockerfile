# الصورة الرسمية لبايثون
FROM python:3.11-slim

# تثبيت المتطلبات الأساسية لتشغيل Playwright والمتصفحات
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg2 \
    libglib2.0-0 libnss3 libatk-bridge2.0-0 libdrm2 \
    libxcomposite1 libxdamage1 libxrandr2 libasound2 \
    libatk1.0-0 libcups2 libdbus-1-3 libxss1 libx11-xcb1 \
    libxext6 libxfixes3 libxkbcommon0 libpango-1.0-0 \
    libcairo2 libgbm1 libexpat1 libnspr4 libsmime3 libx11-6 \
    libxcursor1 libxtst6 libgtk-3-0 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# نسخ ملفات المشروع إلى الحاوية
WORKDIR /app
COPY . .

# تثبيت الحزم
RUN pip install --no-cache-dir -r requirements.txt

# تثبيت المتصفحات الخاصة بـ Playwright
RUN python -m playwright install --with-deps

# أمر التشغيل
CMD ["python", "product_monitor_bot.py"]
