import os
import time
import asyncio
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

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
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# قائمة المنتجات
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

async def fetch_product_status(page, product):
    try:
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })

        await page.goto(product["url"], timeout=90000)
        await page.wait_for_load_state("networkidle")

        inventory_element = await page.query_selector("span.product__inventory")
        inventory_text = await inventory_element.inner_text() if inventory_element else ""

        img_url = await page.get_attribute("meta[property='og:image']", "content")

        if "نفد من المخزون" in inventory_text or "غير متوفر" in inventory_text:
            return "غير متوفر", img_url
        elif inventory_text:
            return "متوفر", img_url
        return "غير معروف", img_url
    except Exception as e:
        logging.error(f"⚠️ خطأ في قراءة بيانات المنتج {product['name']}: {e}")
        return "None", None

def send_telegram_alert(product_name, status, image_url, url):
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"<b>🎉 منتج جديد متوفر الآن!</b>\n\n"
        f"🧃 <b>المنتج:</b> <code>{product_name}</code>\n"
        f"📦 <b>الحالة:</b> ✅ <b>{status}</b>\n"
        f"🕒 <b>الوقت:</b> <code>{now}</code>"
    )

    payload = {
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": msg,
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
        response = requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload)
        logging.info(f"📦 تم إرسال تنبيه للمنتج: {product_name} ({response.status_code})")
    except Exception as e:
        logging.error(f"❌ فشل إرسال التنبيه: {e}")

async def monitor():
    logging.info("🚀 بدأ البوت في مراقبة المنتجات...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        while True:
            for product in products:
                status, image_url = await fetch_product_status(page, product)

                name = product["name"]
                if not status or not image_url:
                    continue

                if name not in previous_status:
                    previous_status[name] = status

                if status == "متوفر" and previous_status[name] != "متوفر":
                    send_telegram_alert(name, status, image_url, product["url"])

                previous_status[name] = status

            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(monitor())
