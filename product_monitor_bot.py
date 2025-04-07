import os
import time
import requests
import threading
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import undetected_chromedriver as uc
import chromedriver_autoinstaller
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

import undetected_chromedriver as uc

def create_driver():
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920x1080")

    driver = uc.Chrome(options=options)
    return driver


def test_telegram_message():
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": "تم تشغيل البوت بنجاح!",
            "parse_mode": "HTML"
        }
        res = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
        print("✅ رسالة الاختبار:", res.status_code)
    except Exception as e:
        print("❌ فشل إرسال رسالة:", e)

def check_product_info(url):
    driver = create_driver()
    try:
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        page_text = soup.get_text().lower()
        status = "غير متوفر" if "نفذ من المخزون" in page_text else "متوفر"
        img = soup.find("meta", property="og:image")
        image_url = img["content"] if img else "https://via.placeholder.com/600x600.png?text=DZRT+Product"
        return status, image_url
    except Exception as e:
        print("⚠️ خطأ في check_product_info:", e)
        return None, None
    finally:
        driver.quit()

def send_alert(name, status, img, url):
    now = datetime.now().strftime("%H:%M:%S")
    msg = f"<b>المنتج: {name}</b>\n\n<b>الحالة:</b> <code>{status}</code>\n<b>الوقت:</b> {now}"

    keyboard = {
        "inline_keyboard": [[
            {
                "text": "شراء" if status == "متوفر" else "غير متوفر",
                "url": url if status == "متوفر" else "https://www.dzrt.com/ar-sa"
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
        r = requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload)
        print(f"📤 إرسال {name}: {r.status_code}")
    except Exception as e:
        print("❌ خطأ في إرسال التليجرام:", e)

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

def send_summary():
    summary = f"📊 <b>ملخص المنتجات - {datetime.now().strftime('%Y-%m-%d')}</b>\n\n"
    for p in products:
        name, url = p["name"], p["url"]
        status, _ = check_product_info(url)
        symbol = "✅" if status == "متوفر" else "❌"
        summary += f"{symbol} <b>{name}</b>: <code>{status}</code>\n"

    payload = {
        "chat_id": CHAT_ID,
        "text": summary,
        "parse_mode": "HTML"
    }
    try:
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
    except Exception as e:
        print("❌ فشل إرسال الملخص:", e)

def schedule_summary():
    while True:
        now = datetime.now()
        target = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        time.sleep((target - now).total_seconds())
        send_summary()

test_telegram_message()
threading.Thread(target=schedule_summary, daemon=True).start()
send_summary()

while True:
    for p in products:
        name, url = p["name"], p["url"]
        status, image = check_product_info(url)
        if status:
            send_alert(name, status, image, url)
    time.sleep(30)
