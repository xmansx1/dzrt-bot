FROM python:3.9-slim

# تثبيت مكتبات النظام الضرورية لتشغيل Playwright
RUN apt-get update && apt-get install -y \
    wget gnupg2 curl unzip \
    libnss3 libatk-bridge2.0-0 libgtk-3-0 libxss1 libasound2 libxshmfence1 \
    libgbm1 libxcomposite1 libxrandr2 libglu1-mesa libxi6 libxcursor1 \
    libxtst6 libgconf-2-4 libpango-1.0-0 libcups2 libxdamage1 libxfixes3 \
    libatspi2.0-0 libx11-xcb1 libdrm2 libdbus-1-3 libexpat1 libxext6 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملفات المشروع إلى الحاوية
WORKDIR /app
COPY . .

# تثبيت الحزم المطلوبة من Python
RUN pip install --no-cache-dir -r requirements.txt

# تثبيت المتصفحات اللازمة لـ Playwright
RUN python -m playwright install --with-deps

# تشغيل البوت
CMD ["python", "product_monitor_bot.py"]
