#!/bin/bash

apt-get update && apt-get install -y wget gnupg2 curl unzip

pip install -r requirements.txt

python -m playwright install --with-deps

python product_monitor_bot.py
