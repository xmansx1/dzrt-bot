#!/bin/bash

# تحديث النظام وتثبيت الأدوات الأساسية
apt-get update && apt-get install -y wget curl unzip gnupg2

# تثبيت الحزم المطلوبة من requirements.txt
pip install --upgrade pip
pip install -r requirements.txt

# تثبيت متصفحات Playwright المطلوبة للتشغيل
python -m playwright install --with-deps

# تشغيل سكربت البوت
python product_monitor_bot.py
