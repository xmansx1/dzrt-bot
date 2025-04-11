#!/bin/bash

# تحديث النظام وتثبيت الأدوات الأساسية
apt-get update && apt-get install -y wget curl unzip gnupg2

# تثبيت المتطلبات
pip install -r requirements.txt

# تثبيت المتصفحات اللازمة لـ Playwright
playwright install --with-deps

# بدء تشغيل البوت
python product_monitor_bot.py
