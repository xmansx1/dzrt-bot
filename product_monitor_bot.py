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
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        page_text = soup.get_text().lower()
        status = "غير متوفر" if "نفذ من المخزون" in page_text else "متوفر"

        img = soup.find("meta", property="og:image")
        image_url = img["content"] if img else "https://via.placeholder.com/600x600.png?text=DZRT+Product"
        return status, image_url
    except Exception as e:
        print(f"⚠️ خطأ في check_product_info: {e}")
        return None, None

def send_alert(name, status, image, url):
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
        "photo": image,
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": keyboard
    }

    try:
        res = requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload)
        print(f"📦 إرسال {name}: {res.status_code}, الرد: {res.text}")
    except Exception as e:
        print("❌ خطأ في إرسال تنبيه التليجرام:", e)

def send_summary():
    for p in products:
        try:
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

            res = requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload)
            print(f"📊 ملخص {name}: {res.status_code}, رد التليجرام: {res.text}")
        except Exception as e:
            print(f"❌ فشل إرسال ملخص المنتج {p['name']}: {e}")

def schedule_summary():
    while True:
        now = datetime.now()
        target = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        time.sleep((target - now).total_seconds())
        send_summary()

# تشغيل البوت
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
