#!/bin/bash

# تثبيت المتطلبات وتشغيل البوت
pip install -r requirements.txt
python -m playwright install --with-deps
python product_monitor_bot.py
