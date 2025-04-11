# استخدم صورة رسمية من Python
FROM python:3.11-slim

# إعداد مجلد العمل
WORKDIR /app

# نسخ الملفات إلى الحاوية
COPY . .

# تثبيت أدوات النظام اللازمة لـ Playwright
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg2 \
    libglib2.0-0 libnss3 libatk-bridge2.0-0 libdrm2 \
    libxcomposite1 libxdamage1 libxrandr2 libasound2 \
    libatk1.0-0 libcups2 libdbus-1-3 libxss1 libx11-xcb1 \
    libxext6 libxfixes3 libxkbcommon0 libpango-1.0-0 \
    libcairo2 libgbm1 libexpat1 libnspr4 libsmime3 libx11-6 \
    libxcursor1 libxtst6 libgtk-3-0 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# تثبيت pip وتحديثه
RUN pip install --upgrade pip

# تثبيت الحزم المطلوبة
RUN pip install -r requirements.txt

# تثبيت المتصفحات الخاصة بـ Playwright
RUN python -m playwright install --with-deps

# تحديد أمر التشغيل
CMD ["python", "product_monitor_bot.py"]
