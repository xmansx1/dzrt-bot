import os
import time
import requests
import threading
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

products = [
    {
        "name": "Seaside Frost",
        "url": "https://www.dzrt.com/ar-sa/products/seaside-frost"
    },
    {
        "name": "icy-rush",
        "url": "https://www.dzrt.com/ar-sa/products/icy-rush"
    },
    {
        "name": "Riyadh Season Edition",
        "url": "https://www.dzrt.com/ar-sa/products/riyadh-season-edition"
    }
]

def test_telegram_message():
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": "تم تشغيل البوت بنجاح! \ud83d\ude80",
        }
        res = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
        print("\u2705 رسالة الاختبار:", res.status_code)
    except Exception as e:
        print("\u274c فشل إرسال رسالة الاختبار:", e)

def check_product_info(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)

            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')

            inventory_tag = soup.find("span", class_="product__inventory")
            inventory_text = inventory_tag.get_text(strip=True) if inventory_tag else ""

            status = "غير متوفر" if "نفد من المخزون" in inventory_text or "غير متوفر" in inventory_text else "متوفر"

            img = soup.find("meta", property="og:image")
            image_url = img["content"] if img else "https://via.placeholder.com/600x600.png?text=DZRT+Product"

            browser.close()
            return status, image_url

    except Exception as e:
        print("\u26a0\ufe0f خطأ في check_product_info:", e)
        return "None", None

def send_alert(name, status, img, url):
    now = datetime.now().strftime("%H:%M:%S")
    emoji = "\u2705" if status == "متوفر" else "\u274c"
    msg = f"""{emoji} <b>المنتج: {name}</b>\n\n<b>الحالة الجديدة:</b> <code>{status}</code>\n<b>وقت التحديث:</b> {now}"""

    keyboard = {
        "inline_keyboard": [[
            {
                "text": "شراء" if status == "متوفر" else "زيارة الموقع",
                "url": url
            }
        ]]
    }

    payload = {
        "chat_id": CHAT_ID,
        "photo": img,
        "caption": msg,
        "parse_mode": "HTML",
        "reply_markup": keyboard
    }

    try:
        res = requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload)
        print(f"\ud83d\udce6 إرسال تنبيه {name}: {res.status_code}")
    except Exception as e:
        print("\u274c خطأ في إرسال التنبيه:", e)

def send_summary():
    print("\ud83d\udce6 إرسال ملخص المنتجات...")
    today = datetime.now().strftime('%Y-%m-%d')
    summary = f"\ud83d\udcca <b>ملخص المنتجات - {today}</b>\n"
    for p in products:
        name, url = p["name"], p["url"]
        status, _ = check_product_info(url)
        symbol = "\u2705" if status == "متوفر" else "\u274c"
        summary += f"{symbol} <b>{name}:</b> <code>{status}</code>\n"

    payload = {
        "chat_id": CHAT_ID,
        "text": summary,
        "parse_mode": "HTML"
    }

    try:
        res = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
        print("\ud83d\udce4 تم إرسال الملخص:", res.status_code)
    except Exception as e:
        print("\u274c فشل إرسال الملخص:", e)

def schedule_summary():
    while True:
        now = datetime.now()
        target = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        time.sleep((target - now).total_seconds())
        send_summary()

# =================== بدء التشغيل ======================
test_telegram_message()
send_summary()
threading.Thread(target=schedule_summary, daemon=True).start()

while True:
    for p in products:
        name, url = p["name"], p["url"]
        status, image = check_product_info(url)
        if status:
            send_alert(name, status, image, url)
    time.sleep(60)
