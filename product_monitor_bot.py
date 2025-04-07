import os
import time
import requests
import threading
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv

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

# حفظ آخر حالة لكل منتج لتفادي تكرار الإرسال
last_statuses = {}

def test_telegram_message():
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": "تم تشغيل البوت بنجاح! 🚀",
        }
        res = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
        print("✅ رسالة الاختبار:", res.status_code)
    except Exception as e:
        print("❌ فشل إرسال رسالة الاختبار:", e)
def check_product_info(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text.lower()

        if "نفد من المخزون" in html or "غير متوفر" in html:
            status = "غير متوفر"
        else:
            status = "متوفر"

        soup = BeautifulSoup(html, 'html.parser')
        img = soup.find("meta", property="og:image")
        image_url = img["content"] if img else "https://via.placeholder.com/600x600.png?text=DZRT+Product"

        return status, image_url
    except Exception as e:
        print("⚠️ خطأ في check_product_info:", e)
        return "None", None


def send_alert(name, status, img, url):
    now = datetime.now().strftime("%H:%M:%S")
    emoji = "✅" if status == "متوفر" else "❌"
    msg = f"""{emoji} <b>المنتج: {name}</b>

<b>الحالة الجديدة:</b> <code>{status}</code>
<b>وقت التحديث:</b> {now}"""

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
        print(f"📦 إرسال تنبيه {name}: {res.status_code}")
    except Exception as e:
        print("❌ خطأ في إرسال التنبيه:", e)

def send_summary():
    print("📦 إرسال ملخص المنتجات...")
    today = datetime.now().strftime('%Y-%m-%d')
    summary = f"📊 <b>ملخص المنتجات - {today}</b>\n"
    for p in products:
        name, url = p["name"], p["url"]
        status, _ = check_product_info(url)
        symbol = "✅" if status == "متوفر" else "❌"
        summary += f"{symbol} <b>{name}:</b> <code>{status}</code>\n"

    payload = {
        "chat_id": CHAT_ID,
        "text": summary,
        "parse_mode": "HTML"
    }

    try:
        res = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
        print("📤 تم إرسال الملخص:", res.status_code)
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

# =================== التشغيل =======================
test_telegram_message()
send_summary()
threading.Thread(target=schedule_summary, daemon=True).start()

while True:
    for p in products:
        name, url = p["name"], p["url"]
        status, image = check_product_info(url)
        if status and last_statuses.get(name) != status:
            send_alert(name, status, image, url)
            last_statuses[name] = status
    time.sleep(60)
