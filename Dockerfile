FROM python:3.11-slim

WORKDIR /app

COPY . .

# تثبيت الحزم الأساسية فقط
RUN apt-get update && apt-get install -y \
    curl wget unzip gnupg ca-certificates \
    libnss3 libxss1 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxcomposite1 libxdamage1 libxrandr2 libasound2 \
    libx11-xcb1 libxkbcommon0 libgtk-3-0 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# تثبيت pip والمتطلبات
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# تثبيت المتصفحات بعد تثبيت playwright
RUN python -m playwright install --with-deps

CMD ["python", "product_monitor_bot.py"]
