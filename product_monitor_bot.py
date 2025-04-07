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

headers = {
    "User-Agent": "Mozilla/5.0"
}

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
            "text": "🚀 تم تشغيل البوت بنجاح!",
            "parse_mode": "HTML"
        }
        res = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
        print("✅ رسالة الاختبار:", res.status_code)
    except Exception as e:
        print("❌ فشل إرسال رسالة الاختبار:", e)

def check_product_info(url):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text().lower()

        status = "غير متوفر" if "نفذ من المخزون" in page_text else "متوفر"

        img = soup.find("meta", property="og:image")
        image_url = img["content"] if img else "https://via.placeholder.com/600x600.png?text=DZRT+Product"

        return status, image_url
    except Exception as e:
        print("⚠️ خطأ في check_product_info:", e)
        return "None", "https://via.placeholder.com/600x600.png?text=Error"

def send_alert(name, status, img, url):
    now = datetime.now().strftime("%H:%M:%S")
    emoji = "✅" if status == "متوفر" else "❌"

    msg = f"""<b>المنتج: {name}</b> {emoji}

<b>الحالة الجديدة:</b> {status}
<b>وقت التحديث:</b> {now}"""

    keyboard = {
        "inline_keyboard": [[
            {
                "text": "شراء الآن" if status == "متوفر" else "عرض المنتج",
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
        r = requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload)
        print(f"📤 إرسال {name}: {r.status_code}")
    except Exception as e:
        print(f"❌ خطأ في إرسال {name}:", e)

def send_summary():
    for p in products:
        name, url = p["name"], p["url"]
        status, image_url = check_product_info(url)
        now = datetime.now().strftime("%H:%M:%S")
        emoji = "✅" if status == "متوفر" else "❌"

        caption = f"""<b>المنتج: {name}</b> {emoji}

<b>الحالة الجديدة:</b> {status}
<b>وقت التحديث:</b> {now}"""

        keyboard = {
            "inline_keyboard": [[
                {
                    "text": "شراء الآن" if status == "متوفر" else "عرض المنتج",
                    "url": url
                }
            ]]
        }

        payload = {
            "chat_id": CHAT_ID,
            "photo": image_url,
            "caption": caption,
            "parse_mode": "HTML",
            "reply_markup": keyboard
        }

        try:
            requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload)
        except Exception as e:
            print(f"❌ فشل إرسال ملخص المنتج {name}:", e)

def schedule_summary():
    while True:
        now = datetime.now()
        target = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        time.sleep((target - now).total_seconds())
        send_summary()

# ✅ Start bot
test_telegram_message()
threading.Thread(target=schedule_summary, daemon=True).start()
send_summary()

while True:
    for p in products:
        name, url = p["name"], p["url"]
        status, image = check_product_info(url)
        if status:
            send_alert(name, status, image, url)
    time.sleep(60)
