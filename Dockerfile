FROM python:3.9-slim

# تثبيت الاعتمادات المطلوبة لـ Playwright
RUN apt-get update && \
    apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# تثبيت Playwright واعتماداته
RUN pip install playwright==1.42.0 && \
    playwright install && \
    playwright install-deps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "product_monitor_bot.py"]