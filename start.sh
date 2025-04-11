#!/bin/bash

# تحديث النظام وتثبيت الأدوات الأساسية
apt-get update && apt-get install -y wget gnupg2 curl unzip

# تثبيت الحزم من requirements.txt
pip install -r requirements.txt

# تثبيت متصفحات Playwright
python -m playwright install --with-deps

# تشغيل سكربت البوت
python product_monitor_bot.py
