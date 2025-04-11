import os
import time
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('product_monitor.log'),
        logging.StreamHandler()
    ]
)

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"

# المنتجات
products = [
    {
        "name": "Seaside Frost",
        "url": "https://www.dzrt.com/ar-sa/products/seaside-frost"
    },
    {
        "name": "Icy Rush",
        "url": "https://www.dzrt.com/ar-sa/products/icy-rush"
    },
    {
        "name": "Riyadh Season Edition",
        "url": "https://www.dzrt.com/ar-sa/products/riyadh-season-edition"
    }
]

previous_status = {}

def fetch_status(product):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(product["url"], headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        inventory = soup.find("span", class_="product__inventory")
        inventory_text = inventory.text.strip() if inventory else ""

        image_meta = soup.find("meta", property="og:image")
        image_url = image_meta["content"] if image_meta else "https://via.placeholder.com/600x600.png?text=NO+IMAGE"

        if "نفد من المخزون" in inventory_text or "غير متوفر" in inventory_text:
            return "غير متوفر", image_url
        elif inventory_text:
            return "متوفر", image_url
        return "غير معروف", image_url
    except Exception as e:
        logging.error(f"⚠️ خطأ في قراءة بيانات المنتج {product['name']}: {e}")
        return None, None

def send_telegram_alert(name, status, image_url, url):
    now = datetime.now().strftime("%H:%M:%S")
    caption = (
        f"<b>🎉 منتج جديد متوفر الآن!</b>\n\n"
        f"🧃 <b>المنتج:</b> <code>{name}</code>\n"
        f"📦 <b>الحالة:</b> ✅ <b>{status}</b>\n"
        f"🕒 <b>الوقت:</b> <code>{now}</code>"
    )

    payload = {
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[
                {
                    "text": "🛒 اضغط للشراء المباشر",
                    "url": url
                }
            ]]
        }
    }

    try:
        res = requests.post(TELEGRAM_API_URL, json=payload)
        logging.info(f"📦 تم إرسال تنبيه للمنتج: {name} (رمز الحالة: {res.status_code})")
    except Exception as e:
        logging.error(f"❌ فشل في إرسال التنبيه للمنتج {name}: {e}")

def monitor():
    logging.info("🚀 بدأ البوت في مراقبة المنتجات...")
    while True:
        for product in products:
            status, img = fetch_status(product)

            if not status or not img:
                continue

            name = product["name"]

            if name not in previous_status:
                previous_status[name] = status

            if status == "متوفر" and previous_status[name] != "متوفر":
                send_telegram_alert(name, status, img, product["url"])

            previous_status[name] = status

        time.sleep(60)

if __name__ == "__main__":
    monitor()
