import os
import time
import requests
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# روابط .json لمنتجات DZRT
products = [
    {
        "name": "Seaside Frost",
        "url": "https://www.dzrt.com/ar-sa/products/seaside-frost",
        "json_url": "https://www.dzrt.com/ar-sa/products/seaside-frost.json"
    },
    {
        "name": "icy-rush",
        "url": "https://www.dzrt.com/ar-sa/products/icy-rush",
        "json_url": "https://www.dzrt.com/ar-sa/products/icy-rush.json"
    },
    {
        "name": "Riyadh Season Edition",
        "url": "https://www.dzrt.com/ar-sa/products/riyadh-season-edition",
        "json_url": "https://www.dzrt.com/ar-sa/products/riyadh-season-edition.json"
    }
]

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

def check_product_info(product):
    try:
        response = requests.get(product["json_url"])
        data = response.json()
        variant = data["product"]["variants"][0]
        available = variant["available"]
        image_url = data["product"]["images"][0]["src"] if data["product"]["images"] else "https://via.placeholder.com/600x600.png?text=DZRT+Product"
        status = "متوفر" if available else "غير متوفر"
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
        name = p["name"]
        status, _ = check_product_info(p)
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

# ====== بداية التشغيل ======
test_telegram_message()
send_summary()
threading.Thread(target=schedule_summary, daemon=True).start()

while True:
    for p in products:
        name, url = p["name"], p["url"]
        status, image = check_product_info(p)
        if status:
            send_alert(name, status, image, url)
    time.sleep(60)
