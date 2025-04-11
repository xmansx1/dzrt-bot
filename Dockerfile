FROM python:3.11-slim

# تثبيت الأدوات الأساسية والحزم المطلوبة لتشغيل Playwright
RUN apt-get update && apt-get install -y \
    curl wget unzip fonts-liberation libasound2 libatk1.0-0 libc6 \
    libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 \
    libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 \
    libpango-1.0-0 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 \
    libxrender1 libxss1 libxtst6 libdrm2 libgbm1 libxkbcommon0 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# إنشاء مجلد العمل
WORKDIR /app

# نسخ جميع الملفات
COPY . .

# تثبيت pip والحزم
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# تثبيت المتصفحات الخاصة بـ Playwright
RUN python -m playwright install --with-deps

# أمر التشغيل
CMD ["python", "product_monitor_bot.py"]
